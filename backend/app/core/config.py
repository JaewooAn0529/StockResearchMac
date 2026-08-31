import os

from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
DART_API_KEY = os.environ.get("DART_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
# Lower is faster and cheaper but reduces the depth of the debate (low|medium|high|xhigh|max)
ANTHROPIC_EFFORT = os.environ.get("ANTHROPIC_EFFORT", "high")
# Number of rounds where bull/bear rebut each other. 1 round = 1 bull turn + 1 bear turn
MAX_DEBATE_ROUNDS = int(os.environ.get("MAX_DEBATE_ROUNDS", "2"))

# "anthropic" (paid, cloud) | "ollama" (free, local). This is a personal tool, so ollama is the default.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")]
