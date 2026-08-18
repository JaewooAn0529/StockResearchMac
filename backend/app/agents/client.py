"""LLM 호출 헬퍼 — Anthropic(클라우드) / Ollama(로컬) 중 LLM_PROVIDER로 전환.

에이전트 코드(analysts/researchers/trader/risk)는 이 파일의 ask()/ask_json()만
알고, 어느 프로바이더를 쓰는지는 모른다. 프로바이더를 바꿔도 그쪽은 안 건드린다.
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

# Qwen2.5는 문맥이 길어지거나 온도가 높으면 중국어로 드리프트하는 경우가 실측
# 확인됨(2라운드 토론 이후 응답이 통째로 중국어로 나온 사례). 모든 시스템
# 프롬프트 끝에 강제해서 두 프로바이더 모두에 일괄 적용한다.
_LANGUAGE_GUARD = "\n\n반드시 한국어로만 답하라. 중국어, 영어 등 다른 언어를 섞지 마라."


class AgentRefusal(RuntimeError):
    """모델이 안전상의 이유로 응답을 거절했을 때 (Anthropic 전용)."""


def _get_anthropic_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # ANTHROPIC_API_KEY를 환경에서 읽는다
    return _client


def _extract_anthropic_text(response) -> str:
    # stop_reason을 먼저 확인하지 않고 content[0]을 읽으면 거절 시 IndexError가 난다
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
            # 종목 데이터를 다 넣으면 기본 컨텍스트(2~4K)로는 잘릴 수 있어서 넉넉히 잡는다.
            # temperature는 기본값(0.8)보다 낮춰서 언어 드리프트 등 무작위성을 줄인다.
            "options": {"num_ctx": 8192, "num_predict": max_tokens, "temperature": 0.3},
        },
        timeout=300,  # 로컬 7B는 느릴 수 있어 넉넉히
    )
    res.raise_for_status()
    return res.json()["message"]["content"].strip()


_CJK_RE = re.compile(r"[一-鿿]")  # 이 앱에서는 정상 응답에 한자가 나올 일이 없다


def _contains_chinese(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _ollama_ask(system: str, prompt: str, max_tokens: int, retries: int = 2) -> str:
    text = ""
    for attempt in range(retries + 1):
        text = _ollama_chat(system, prompt, max_tokens)
        if not _contains_chinese(text):
            return text
        print(f"[warn] 중국어 드리프트 감지, 재시도 {attempt + 1}/{retries}")
    return text  # 재시도를 다 써도 오염됐으면 마지막 결과라도 반환


def _ollama_ask_json(system: str, prompt: str, schema: dict, max_tokens: int, retries: int = 2) -> dict:
    raw = ""
    for attempt in range(retries + 1):
        raw = _ollama_chat(system, prompt, max_tokens, format_=schema)
        if not _contains_chinese(raw):
            return json.loads(raw)
        print(f"[warn] 중국어 드리프트 감지, 재시도 {attempt + 1}/{retries}")
    return json.loads(raw)


# 감사 추적용 호출 카운터. 토론 1회에 LLM을 몇 번 부르는지 응답에 남겨서
# 어디가 느린지 / 클라우드 API로 바꿨을 때 비용이 얼마나 될지 감을 잡는다.
_call_count = 0


def reset_call_count() -> None:
    global _call_count
    _call_count = 0


def get_call_count() -> int:
    return _call_count


def ask(system: str, prompt: str, max_tokens: int = 8000) -> str:
    """자유 서술 응답을 받는다 (분석가 리포트, 토론 발언)."""
    global _call_count
    _call_count += 1
    system = system + _LANGUAGE_GUARD
    if LLM_PROVIDER == "ollama":
        return _ollama_ask(system, prompt, max_tokens)
    return _anthropic_ask(system, prompt, max_tokens)


def ask_json(system: str, prompt: str, schema: dict, max_tokens: int = 8000) -> dict:
    """스키마가 보장된 JSON 응답을 받는다 (트레이더 결정, 리스크 판정)."""
    global _call_count
    _call_count += 1
    system = system + _LANGUAGE_GUARD
    if LLM_PROVIDER == "ollama":
        return _ollama_ask_json(system, prompt, schema, max_tokens)
    return _anthropic_ask_json(system, prompt, schema, max_tokens)
