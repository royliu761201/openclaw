import asyncio
from typing import List, Dict, Optional
from types import SimpleNamespace
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from core.model_client import ModelClient
from .search_ops import query_ops, engine_ops

class SearchClient:
    """
    Leverages Gemini's Native Google Search Grounding.
    Uses ModelClient's authenticated session.
    Refactored to use `search_ops`.
    """
    def __init__(self, model_client: Optional[ModelClient] = None):
        self.model_client = model_client or ModelClient()
        self.client = self.model_client.client
        # Use a model verified to support tools
        self.model_id = "gemini-3-flash-preview" 

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_literature_async(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Uses Gemini Grounding + LLM Extraction to find high-quality papers.
        """
        # 1. Build Query
        refined_query = query_ops.build_grounding_query(query)

        print(f"[SearchClient] Grounding Query: {refined_query}")
        
        try:
            # Enable Google Search Tool
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            
            # Execute Grounding Call
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=refined_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"],
                    temperature=0.1 
                )
            )
            
            # 2. Try Parsing JSON from Text
            text_response = response.candidates[0].content.parts[0].text
            valid_papers = query_ops.parse_llm_json(text_response)
            
            if valid_papers:
                print(f"[SearchClient] ✅ Successfully extracted {len(valid_papers)} papers from LLM text.")
                return valid_papers

            print("[SearchClient] ⚠️ Failed to parse JSON from Search. Falling back to metadata.")

            # 3. Fallback: Parse Metadata
            return self._parse_grounding_metadata(response, max_results)
            
        except Exception as e:
            print(f"[SearchClient] Error searching '{query}': {e}")
            # Fallback to DDG if needed?
            # return engine_ops.execute_duckduckgo(query, max_results)
            return []

    def _parse_grounding_metadata(self, response, max_results: int) -> List[Dict]:
        """EXTRACTS URLs from GroundingMetadata (Fallback)."""
        try:
            candidate = response.candidates[0]
            if not candidate.grounding_metadata:
                return []
                
            cmd = candidate.grounding_metadata
            if not cmd.grounding_chunks:
                return []
                
            return query_ops.filter_grounding_metadata(cmd.grounding_chunks, max_results)
            
        except Exception as e:
            print(f"[SearchClient] Parsing Error: {e}")
            return []
