"""LLM call helper — switches between Anthropic (cloud) and Ollama (local) via LLM_PROVIDER.

Agent code (analysts/researchers/trader/risk) only knows about this file's ask()/ask_json()
and has no idea which provider is being used. Switching providers doesn't touch that code.
"""

from __future__ import annotations

import json
import re

import anthropic
import requests

from app.core.config import (
    ANTHROPIC_EFFORT,
    ANTHROPIC_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)

_client: anthropic.Anthropic | None = None

# Qwen2.5 has been observed to drift into Chinese when the context gets long or the
# temperature is high (e.g. the entire response coming out in Chinese after round 2 of
# a debate). We append this to the end of every system prompt so it applies uniformly
# to both providers.
_LANGUAGE_GUARD = "\n\n반드시 한국어로만 답하라. 중국어, 영어 등 다른 언어를 섞지 마라."


class AgentRefusal(RuntimeError):
    """Raised when the model refuses to respond for safety reasons (Anthropic only)."""


def _get_anthropic_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    return _client


def _extract_anthropic_text(response) -> str:
    # Reading content[0] before checking stop_reason raises IndexError on a refusal
    if response.stop_reason == "refusal":
        detail = getattr(response.stop_details, "category", None)
        raise AgentRefusal(f"모델이 응답을 거절했습니다 (category={detail})")
    return "".join(b.text for b in response.content if b.type == "text").strip()


def _anthropic_ask(system: str, prompt: str, max_tokens: int) -> str:
    response = _get_anthropic_client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": ANTHROPIC_EFFORT},
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_anthropic_text(response)


def _anthropic_ask_json(system: str, prompt: str, schema: dict, max_tokens: int) -> dict:
    response = _get_anthropic_client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        thinking={"type": "adaptive"},
        output_config={
            "effort": ANTHROPIC_EFFORT,
            "format": {"type": "json_schema", "schema": schema},
        },
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(_extract_anthropic_text(response))


def _ollama_chat(system: str, prompt: str, max_tokens: int, format_: dict | str | None = None) -> str:
    res = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": format_,
            "stream": False,
            # Feeding in all the stock data can get truncated at the default context size
            # (2-4K), so we set this generously. Temperature is lowered from the default
            # (0.8) to reduce randomness like language drift.
            "options": {"num_ctx": 8192, "num_predict": max_tokens, "temperature": 0.3},
        },
        timeout=300,  # local 7B models can be slow, so give it plenty of room
    )
    res.raise_for_status()
    return res.json()["message"]["content"].strip()


_CJK_RE = re.compile(r"[一-鿿]")  # a normal response in this app should never contain Chinese characters


def _contains_chinese(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _ollama_ask(system: str, prompt: str, max_tokens: int, retries: int = 2) -> str:
    text = ""
    for attempt in range(retries + 1):
        text = _ollama_chat(system, prompt, max_tokens)
        if not _contains_chinese(text):
            return text
        print(f"[warn] 중국어 드리프트 감지, 재시도 {attempt + 1}/{retries}")
    return text  # if still contaminated after exhausting retries, return the last result anyway


def _ollama_ask_json(system: str, prompt: str, schema: dict, max_tokens: int, retries: int = 2) -> dict:
    raw = ""
    for attempt in range(retries + 1):
        raw = _ollama_chat(system, prompt, max_tokens, format_=schema)
        if not _contains_chinese(raw):
            return json.loads(raw)
        print(f"[warn] 중국어 드리프트 감지, 재시도 {attempt + 1}/{retries}")
    return json.loads(raw)


# Call counter for audit trail purposes. We surface how many times the LLM is called
# per debate in the response, to get a sense of where the bottleneck is / what it
# would cost if switched to a cloud API.
_call_count = 0


def reset_call_count() -> None:
    global _call_count
    _call_count = 0


def get_call_count() -> int:
    return _call_count


def ask(system: str, prompt: str, max_tokens: int = 8000) -> str:
    """Gets a free-form text response (analyst reports, debate statements)."""
    global _call_count
    _call_count += 1
    system = system + _LANGUAGE_GUARD
    if LLM_PROVIDER == "ollama":
        return _ollama_ask(system, prompt, max_tokens)
    return _anthropic_ask(system, prompt, max_tokens)


def ask_json(system: str, prompt: str, schema: dict, max_tokens: int = 8000) -> dict:
    """Gets a schema-guaranteed JSON response (trader decisions, risk verdicts)."""
    global _call_count
    _call_count += 1
    system = system + _LANGUAGE_GUARD
    if LLM_PROVIDER == "ollama":
        return _ollama_ask_json(system, prompt, schema, max_tokens)
    return _anthropic_ask_json(system, prompt, schema, max_tokens)
