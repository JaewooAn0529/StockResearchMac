import os

from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
DART_API_KEY = os.environ.get("DART_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
# 낮출수록 빠르고 저렴하지만 토론의 깊이가 줄어든다 (low|medium|high|xhigh|max)
ANTHROPIC_EFFORT = os.environ.get("ANTHROPIC_EFFORT", "high")
# bull/bear가 서로 반박하는 라운드 수. 1라운드 = bull 1회 + bear 1회
MAX_DEBATE_ROUNDS = int(os.environ.get("MAX_DEBATE_ROUNDS", "2"))

# "anthropic"(유료, 클라우드) | "ollama"(무료, 로컬). 개인용 도구라 기본은 ollama.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")]
