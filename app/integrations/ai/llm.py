"""Large language model client (Google Gemini over REST).

`get_llm()` returns None when GEMINI_API_KEY is missing; callers then answer with rules computed
from real data. Tests inject a fake through FastAPI's dependency_overrides.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class LlmUnavailable(RuntimeError):
    """The model could not answer (network, quota, invalid output). Callers fall back to rules."""


@dataclass
class LlmReply:
    text: str
    model: str


class Llm(Protocol):
    model: str

    async def generate(self, system: str, prompt: str, *, as_json: bool = False) -> LlmReply: ...


class GeminiClient:
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self.model = model

    async def generate(self, system: str, prompt: str, *, as_json: bool = False) -> LlmReply:
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
        }
        if as_json:
            body["generationConfig"]["responseMimeType"] = "application/json"
        try:
            async with httpx.AsyncClient(timeout=45) as http:
                r = await http.post(self.URL.format(model=self.model), params={"key": self._api_key}, json=body)
        except httpx.HTTPError as e:
            raise LlmUnavailable(f"falha de rede: {e.__class__.__name__}")
        if r.status_code != 200:
            raise LlmUnavailable(f"Gemini respondeu {r.status_code}")
        try:
            parts = r.json()["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, ValueError):
            raise LlmUnavailable("resposta do Gemini sem conteúdo")
        if not text:
            raise LlmUnavailable("resposta do Gemini vazia")
        return LlmReply(text, self.model)


def parse_json(reply: LlmReply) -> Any:
    text = reply.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("\n") + 1:] if "\n" in text else text
    try:
        return json.loads(text)
    except ValueError:
        raise LlmUnavailable("o modelo não devolveu JSON válido")


def get_llm() -> Llm | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key.startswith("sua-chave"):
        return None
    return GeminiClient(key, os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
