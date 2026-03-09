import os
import json
import asyncio
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, Any, List
import yaml

# Import from core config if available, otherwise define defaults or simple fallback
try:
    from config import MODEL_POOL, ModelTier
except ImportError:
    # Fallback/Standalone Mode Support (Partial)
    MODEL_POOL = {}
    class ModelTier:
        CRITICAL = "critical"
        STANDARD = "standard"
        ECONOMY = "economy"


DEFAULT_TASK_ROUTING = {
    "idea_generation": ModelTier.CRITICAL,
    "literature_review": ModelTier.STANDARD,
    "reflection": ModelTier.CRITICAL,
    "paper_drafting": ModelTier.CRITICAL,
    "complex_coding": ModelTier.STANDARD,
    "code_review": ModelTier.STANDARD,
    "routine_coding": ModelTier.STANDARD,
    "summarization": ModelTier.STANDARD,
    "status_check": ModelTier.ECONOMY,
    "formatting": ModelTier.ECONOMY,
    "sentiment_analysis": ModelTier.ECONOMY,
    "visual_critique": ModelTier.CRITICAL
}

class LLMClient:
    """
    Unified LLM Client acting as a lightweight utility.
    Encapsulates Logic from previous `core.model_client` and `src.llm_client`.
    """
    def __init__(self, config_path="config.yaml"):
        # Load API Key
        self.api_key = self._load_api_key()
        if not self.api_key:
            # Non-blocking warning for hybrid modes
            print("[LLMClient] Warning: GOOGLE_API_KEY not found. Helper functions might fail.")
        
        # Initialize the Client (VertexAI/AI Studio)
        # Using vertexai=True as per previous verified implementation
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key, vertexai=True)
            pass

        # Load routing config if file exists (Legacy support)
        if os.path.exists(config_path):
             with open(config_path, 'r') as f:
                self.simple_config = yaml.safe_load(f)
        else:
            self.simple_config = {}

    def _load_api_key(self) -> Optional[str]:
        # Priority 1: Check known external secret paths
        potential_paths = [
            os.path.abspath(os.path.join(os.getcwd(), "../MyAI/ai4s/secrets.json")), # User specified
            os.path.join(os.getcwd(), "secrets.json") # Local fallback
        ]
        
        for secrets_path in potential_paths:
            try:
                if os.path.exists(secrets_path):
                    with open(secrets_path, "r") as f:
                        secrets = json.load(f)
                        # Try common key variants (including lowercase)
                        for key in ["GOOGLE_API_KEY", "google_api_key", "GEMINI_API_KEY", "API_KEY"]:
                            if val := secrets.get(key):
                                return val
            except Exception:
                pass
        
        # Priority 2: Fallback to ENV
        return os.getenv("GOOGLE_API_KEY")

    def _get_model_id(self, tier: Any) -> str:
        """Resolve Model ID from Tier Enum or String Alias."""
        # Case A: Tier Enum (from Config)
        if hasattr(tier, 'name') and MODEL_POOL:
             config = MODEL_POOL.get(tier)
             if config:
                 return config.id
        
        # Case B: String Alias (Legacy/Simple)
        if isinstance(tier, str):
            # Check if it matches a predefined pool alias
            # Or return as is if it looks like a model ID
            if "gemini" in tier:
                return tier
            
        # Default Fallback
        return "gemini-1.5-flash"

    def _load_guideline(self, filename: str) -> str:
        """Load a specific guideline file from Knowledge Base or Legacy .agent_rules"""
        # Priority 1: Knowledge Base Standards
        kb_path = os.path.join(os.getcwd(), "research_vault", "knowledge_base", "standards", filename)
        if os.path.exists(kb_path):
            with open(kb_path, "r") as f:
                return f"\n\n[System Guideline: {filename}]\n{f.read()}\n"
        
        # Priority 2: Legacy .agent_rules
        legacy_path = os.path.join(os.getcwd(), "research_vault", ".agent_rules", filename)
        if os.path.exists(legacy_path):
            with open(legacy_path, "r") as f:
                return f"\n\n[System Guideline: {filename}]\n{f.read()}\n"
        
        return ""

    def _get_system_context(self, task_type: str) -> str:
        """Dynamically build system prompt based on Meta-Knowledge."""
        context = ""
        
        # Mapping task types to relevant guidelines
        if task_type in ["idea_generation", "planning", "reflection"]:
            context += self._load_guideline("idea_standards.md")
            
        if task_type in ["complex_coding", "routine_coding", "experimentation"]:
            context += self._load_guideline("task_guidelines.md")
            
        if task_type in ["paper_drafting", "summarization", "literature_review", "writing", "grant_writing"]:
            context += self._load_guideline("paper_standards.md")
            context += self._load_guideline("citation_policy.md")
            # Awareness of existing portfolio for citations
            context += self._load_guideline("project_map.md")

        if task_type in ["grant_writing"]:
             context += self._load_guideline("grant/nsfc_guidelines.md")

        return context

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def chat(self, 
                   message: Any, 
                   tier: Any = None,
                   task_type: str = "general",
                   system_instruction: Optional[str] = None,
                   structured_schema: Optional[Any] = None) -> str:
        
        # 1. Route Task to Tier if not specified
        if not tier:
             tier = DEFAULT_TASK_ROUTING.get(task_type, ModelTier.STANDARD)
        
        model_id = self._get_model_id(tier)
        
        print(f"[LLMClient] Routing '{task_type}' -> ({model_id})")
        
        # 2. Configure Config
        config = types.GenerateContentConfig()
        
        # INJECT METAKNOWLEDGE
        guideline_context = self._get_system_context(task_type)
        base_instruction = system_instruction or "You are an autonomous AI scientist."
        config.system_instruction = base_instruction + guideline_context
        
        if structured_schema:
            config.response_mime_type = "application/json"
            config.response_schema = structured_schema

        # 3. Execute using V2 Client
        try:
            response = await self.client.aio.models.generate_content(
                model=model_id,
                contents=message,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"[LLMClient] Error with {model_id}: {e}")
            # Fallback Logic
            if "NOT_FOUND" in str(e) or "404" in str(e) or "400" in str(e):
                 print(f"[LLMClient] Switching to Fallback")
                 # Hardcoded reliable fallback for now, or check config
                 fallback_id = "gemini-2.0-flash-exp"
                 response = await self.client.aio.models.generate_content(
                    model=fallback_id,
                    contents=message,
                    config=config
                 )
                 return response.text
            raise e
