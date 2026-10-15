# pip install google-generativeai

import models.config as config
from utils.mylogger import MyLogger
import os
from models.llm import LLM
import google.generativeai as genai
from tqdm.contrib.concurrent import thread_map

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
if __name__ == "models.gemini":
    sys.modules["src.models.gemini"] = sys.modules[__name__]
elif __name__ == "src.models.gemini":
    sys.modules["models.gemini"] = sys.modules[__name__]

_model_name_map = {
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-1.5-pro": "gemini-1.5-pro-latest",
    "gemini-1.5-flash": "gemini-1.5-flash-latest",
    "gemini-pro": "gemini-pro",
    "gemini-pro-vision": "gemini-pro-vision",
    "gemini-1.0-pro-vision": "gemini-1.0-pro-vision-latest"
}
_GEMINI_DEFAULT_PARAMS = {"temperature": 0.4, "top_p": 1, "top_k": 32, "max_tokens": 2048 }

import threading

class GeminiModel(LLM):
    # Process-wide token counters to aggregate across pipeline stages
    _global_token_lock = threading.Lock()
    _global_prompt_tokens = 0
    _global_candidate_tokens = 0
    _global_total_tokens = 0

    @classmethod
    def reset_token_usage(cls):
        with cls._global_token_lock:
            cls._global_prompt_tokens = 0
            cls._global_candidate_tokens = 0
            cls._global_total_tokens = 0

    @classmethod
    def get_token_usage(cls):
        with cls._global_token_lock:
            return {
                "prompt_tokens": cls._global_prompt_tokens,
                "candidate_tokens": cls._global_candidate_tokens,
                "total_tokens": cls._global_total_tokens
            }

    def __init__(self, model_name, logger: MyLogger, **kwargs):
        # https://aistudio.google.com/app/apikey
        if ("google_api_key" in kwargs) and (kwargs["google_api_key"] is not None):
            api_key = kwargs["google_api_key"]
        elif ("gemini_api_key" in kwargs) and (kwargs["gemini_api_key"] is not None):
            api_key = kwargs["gemini_api_key"]
        else:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key not found! Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file or environment variables."
            )
        genai.configure(api_key=api_key)
        self.logprobs = None
        for k in _GEMINI_DEFAULT_PARAMS:
            if k in kwargs:
                #print(f"Setting {k}:{kwargs[k]}")
                _GEMINI_DEFAULT_PARAMS[k] = kwargs[k]
        genai.GenerationConfig(max_output_tokens=_GEMINI_DEFAULT_PARAMS["max_tokens"],
                               temperature=_GEMINI_DEFAULT_PARAMS["temperature"],
                               top_p=_GEMINI_DEFAULT_PARAMS["top_p"],
                               top_k=_GEMINI_DEFAULT_PARAMS["top_k"])
        actual_model_name = _model_name_map.get(model_name.lower(), model_name)
        self.client = genai.GenerativeModel(model_name=actual_model_name)

    def predict(self, prompt, batch_size=0, no_progress_bar=False):
        if batch_size == 0:
            return self._predict(prompt)
        args = range(0, len(prompt))
        responses = thread_map(
            lambda x: self._predict(prompt[x]),
            args,
            max_workers=batch_size,
            disable=no_progress_bar)
        return responses

    def _predict(self, main_prompt):
        history = [
            {"role": "user", "parts": [{"text": f"System prompt: {main_prompt[0]['content']}"}]},
            {"role": "model", "parts": [{"text": "Understood."}]},
            {"role": "user", "parts": [{"text": f"{main_prompt[1]['content']}"}]}
        ]
        
        import time
        import re
        max_retries = 10
        base_delay = 5.0
        
        for attempt in range(max_retries):
            try:
                response = self.client.generate_content(history)
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    p_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    c_tokens = getattr(usage, "candidates_token_count", 0) or 0
                    t_tokens = getattr(usage, "total_token_count", 0) or (p_tokens + c_tokens)
                    with GeminiModel._global_token_lock:
                        GeminiModel._global_prompt_tokens += p_tokens
                        GeminiModel._global_candidate_tokens += c_tokens
                        GeminiModel._global_total_tokens += t_tokens
                return response.text
            except Exception as e:
                err_str = str(e)
                if "ResourceExhausted" in type(e).__name__ or "429" in err_str or "quota" in err_str.lower():
                    # Parse suggested retry delay if provided by Google API
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str)
                    if retry_match:
                        wait_seconds = float(retry_match.group(1)) + 2.0
                    else:
                        wait_seconds = base_delay * (1.5 ** attempt)
                    
                    print(f"\n[Gemini Rate Limit 429] Waiting {wait_seconds:.1f}s before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_seconds)
                else:
                    raise e
                    
        raise RuntimeError("Exceeded maximum retries for Gemini API request due to rate limits.")
    
if __name__ == '__main__':
    gemini=GeminiModel('gemini-1.5-pro', None)
    system_prompt=""
    user_prompt=""
    gemini.predict([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
