import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from .config import CONFIG, GlobalConfig

# 🚀 Manage noisy third-party libraries
NOISY_LOGGERS = [
    "httpx",
    "httpcore",
    "urllib3",
    "groq",
    "openai",
    "google",
    "google.generativeai",
    "absl",
]

for logger_name in NOISY_LOGGERS:
    logging.getLogger(logger_name).setLevel(logging.INFO)

# Default Model Pool
MODEL_POOL = {
    "gemini-3": {"provider": "google", "id": "gemini-3-flash-preview"},
    "gemini-2.5": {"provider": "google", "id": "gemini-2.5-flash-lite"},
    "gemini-1.5": {"provider": "google", "id": "gemini-1.5-flash"},
    "gemini-2.0": {"provider": "google", "id": "gemini-2.0-flash-exp"},
    "qwen-32b": {"provider": "groq", "id": "qwen/qwen3-32b"},
    "deepseek-r1": {"provider": "hf", "id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"},
}


# API Keys (Sourced from Config/Env)
# Helper to make a list if single string
def _to_list(val):
    return [val] if val else []


API_KEYS = {
    "GROQ": _to_list(CONFIG.groq_api_key),
    "GOOGLE": _to_list(CONFIG.google_api_key),
    "HF": _to_list(CONFIG.hf_token),
}

# Late imports to avoid hard dependencies if not used
try:
    from google import genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None


class UnifiedLLMClient:
    def __init__(self, model_key: str):
        if model_key not in MODEL_POOL:
            raise ValueError(f"Model key {model_key} not found in MODEL_POOL")

        self.cfg = MODEL_POOL[model_key]
        self.model_key = model_key
        self.provider = self.cfg["provider"]
        self.model_id = self.cfg["id"]

        # Initialize Key List and Index
        raw_keys = API_KEYS.get(self.provider.upper(), [])
        self.keys = [raw_keys] if isinstance(raw_keys, str) else raw_keys
        if not self.keys:
            print(f"⚠️ Warning: No API keys found for provider {self.provider}")
        self.current_key_idx = 0

        # Cache Configuration
        cache_dir = os.path.join(GlobalConfig.PROD_DIR, "api_cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_path = os.path.join(cache_dir, f"cache_{model_key}.json")

        # Load Cache
        self.cache = {}
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"[UnifiedLLMClient] Failed to load cache: {e}")

        # Client placeholders
        self._google_client = None
        self._groq_client = None
        self._hf_client = None

    def _get_current_key(self):
        if not self.keys:
            return None
        return self.keys[self.current_key_idx]

    def _rotate_key(self):
        if len(self.keys) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
            print(f"[UnifiedLLMClient] {self.provider} Rotating to Key #{self.current_key_idx}")
            # Reset clients to force re-init with new key
            self._google_client = None
            self._groq_client = None
            self._hf_client = None

    # ------------------ Lazy Initialization ------------------ #
    def _ensure_google(self):
        if not genai:
            raise ImportError("google-genai not installed")
        if self._google_client is None:
            key = self._get_current_key()
            if not key:
                raise ValueError("No Google API Key available")
            # default to vertexai=True as it matches the 'AQ...' keys used by the user
            self._google_client = genai.Client(api_key=key, vertexai=True)

    def _ensure_groq(self):
        if not Groq:
            raise ImportError("groq not installed")
        if self._groq_client is None:
            key = self._get_current_key()
            if not key:
                raise ValueError("No Groq API Key available")
            self._groq_client = Groq(api_key=key)

    def _ensure_hf(self):
        if not InferenceClient:
            raise ImportError("huggingface_hub not installed")
        if self._hf_client is None:
            key = self._get_current_key()
            if not key:
                raise ValueError("No HF Token available")
            self._hf_client = InferenceClient(model=self.model_id, token=key)

    # ------------------ Underlying Calls ------------------ #
    def _raw_call_google(self, sys_p: str, user_p: str) -> str:
        self._ensure_google()
        contents = f"{sys_p}\n\n{user_p}" if sys_p else user_p
        config = {
            "temperature": 0.1,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        resp = self._google_client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config,
        )
        return resp.text

    def _raw_call_groq(self, sys_p: str, user_p: str) -> str:
        self._ensure_groq()
        resp = self._groq_client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "system", "content": sys_p}, {"role": "user", "content": user_p}],
            temperature=0.1,
        )
        return resp.choices[0].message.content

    def _raw_call_hf(self, sys_p: str, user_p: str) -> str:
        self._ensure_hf()
        messages = [{"role": "user", "content": f"[SYSTEM]\n{sys_p}\n\n[USER]\n{user_p}"}]
        resp = self._hf_client.chat_completion(messages=messages, max_tokens=4000, temperature=0.1)
        return resp.choices[0].message.content

    # ------------------ Main Interface ------------------ #
    def request(self, system_prompt: str, user_prompt: str):
        # 1) Check Cache
        key_str = self.model_id + system_prompt + user_prompt
        h = hashlib.md5(key_str.encode("utf-8")).hexdigest()
        if h in self.cache:
            return self.cache[h].get("thought", ""), self.cache[h].get("answer", "")

        # 2) Call API with Retry
        raw = ""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if self.provider == "google":
                    raw = self._raw_call_google(system_prompt, user_prompt)
                elif self.provider == "groq":
                    raw = self._raw_call_groq(system_prompt, user_prompt)
                elif self.provider == "hf":
                    raw = self._raw_call_hf(system_prompt, user_prompt)
                break
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "limit" in err_str:
                    self._rotate_key()

                wait_time = (2**attempt) + (0.1 * attempt)
                print(
                    f"[UnifiedLLMClient] {self.model_key} Attempt {attempt+1} Failed: {e}. Waiting {wait_time}s..."
                )
                time.sleep(wait_time)

        if not raw:
            return "", "ERROR"

        # 3) Parse Thought Chain
        thought, answer = "", raw
        match = re.search(r"<(think|thought)>(.*?)</\1>", raw, re.DOTALL | re.IGNORECASE)
        if match:
            thought = match.group(2).strip()
            answer = re.sub(
                r"<(think|thought)>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE
            ).strip()

        # 4) Save Cache
        self.cache[h] = {"thought": thought, "answer": answer}
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[UnifiedLLMClient] Failed to save cache: {e}")

        return thought, answer
