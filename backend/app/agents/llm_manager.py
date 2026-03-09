import json
import os
from threading import RLock
from openai import OpenAI
from typing import Dict, List

class LLMManager:
    _config_cache: Dict[str, dict] = {}
    _client_cache: Dict[tuple, OpenAI] = {}
    _lock = RLock()

    def __init__(self, config_path: str = "llm.json", timeout_seconds: float | None = None):
        self.config_path = config_path
        self.timeout_seconds = float(timeout_seconds or os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.config = self._load_config(config_path)

    def call(self, model_key: str, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
        cfg = self.config[model_key]
        client = self._get_client(cfg)

        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content or ""

    def list_model_keys(self) -> List[str]:
        return list(self.config.keys())

    def get_display_name(self, model_key: str) -> str:
        cfg = self.config.get(model_key, {})
        return cfg.get("display_name") or model_key

    @classmethod
    def _load_config(cls, config_path: str) -> dict:
        with cls._lock:
            cached = cls._config_cache.get(config_path)
            if cached is not None:
                return cached
            with open(config_path, encoding="utf-8") as f:
                parsed = json.load(f)
            cls._config_cache[config_path] = parsed
            return parsed

    def _get_client(self, cfg: dict) -> OpenAI:
        key = (
            str(cfg.get("base_url", "")),
            str(cfg.get("api_key", "")),
            self.timeout_seconds,
        )
        with self._lock:
            cached = self._client_cache.get(key)
            if cached is not None:
                return cached
            client = OpenAI(
                base_url=cfg["base_url"],
                api_key=cfg["api_key"],
                timeout=self.timeout_seconds,
            )
            self._client_cache[key] = client
            return client
