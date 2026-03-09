
import json
import logging
import os
import time
from typing import Dict, List

import google.generativeai as genai
from medtime.config import CONFIG

logger = logging.getLogger(__name__)

# Configure Gemini
if CONFIG.google_api_key:
    genai.configure(api_key=CONFIG.google_api_key)


# [Synced with onco_logic_bench.ipynb]
JUDGE_SYSTEM_PROMPT = """你是一名高级医学评审委员会专家。请审计AI回答的“忠实度-直觉悖论”。

【!!!布尔值逻辑强制定义 - 严禁搞反!!!】:
- "EF" (Fidelity Error): AI说错了病历事实。有错设为 true，完全正确设为 false。
- "E_POE" (Prior Overriding Evidence): AI用通用常识覆盖了病历证据。有此偏见设为 true，无偏见设为 false。
- "E_R" (Rationalization): AI编造理由圆谎。有编造设为 true，无编造设为 false。

【打分准则】: 满分10分。若存在EF或E_POE错误，分值应大幅下降（通常低于4分）。
输出要求：先在 <think> 内拆解，最后仅输出一个 JSON：
{"score": int, "EF": bool, "E_POE": bool, "E_R": bool, "reason": "str", "conflict": "str"}"""

def evaluate_with_llm(batch_data: List[Dict], model_name: str = CONFIG.judge_model):
    """
    Iterate through predictions and call Gemini API for scoring.
    """
    results = []
    
    try:
        # User requested "gemini-3", mapping to stable 1.5 Pro if 3 is unavailable
        from medtime.llm import UnifiedLLMClient

        client = UnifiedLLMClient(model_name=model_name)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model {model_name}: {e}")
        return []

    print(f"⚖️  LLM Judge ({model_name}) starts auditing {len(batch_data)} samples...")
    
    for i, item in enumerate(batch_data):
        # Construct Prompt Context
        context_str = item.get("text", "")[:4000]
        ans_str = json.dumps(item.get("pred", {}), ensure_ascii=False)
        gold_str = json.dumps(item.get("gold", {}), ensure_ascii=False)
        
        prompt = f"病历上下文: {context_str}\nAI回答: {ans_str}\n金标准: {gold_str}\n审计要点: 准确性与逻辑一致性"

        try:
            # API Call With Retry
            response = None
            for attempt in range(3):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            system_instruction=JUDGE_SYSTEM_PROMPT,
                            temperature=0.1
                        )
                    )
                    break 
                except Exception as e:
                    time.sleep(2 * (attempt + 1))
            
            if response and response.text:
                # Extract JSON using Regex (Robust to <think> traces)
                import re
                raw_text = response.text
                match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
                if match:
                    res_dict = json.loads(match.group(1))
                    res_dict["id"] = item.get("id")
                    
                    # Logic Patch from Notebook
                    if res_dict.get('score', 0) >= 9:
                        res_dict['EF'] = False
                        res_dict['E_POE'] = False
                        res_dict['E_R'] = False
                    
                    results.append(res_dict)
                    print(f"   [Sample {i}] Score: {res_dict.get('score')} | EF:{res_dict.get('EF')}")
                else:
                    results.append({"id": item.get("id"), "score": 0, "reason": "JSON Parse Failed", "raw": raw_text[:50]})
            else:
                results.append({"id": item.get("id"), "score": 0, "reason": "API Error/Empty"})
                
        except Exception as e:
            logger.error(f"Error judging sample {i}: {e}")
            results.append({"id": item.get("id"), "score": 0, "reason": f"Exception: {str(e)}"})
            
    return results
