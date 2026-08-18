from dotenv import load_dotenv

# pykrx는 import되는 순간 KRX_ID/KRX_PW 환경변수로 로그인을 시도하므로,
# .env는 pykrx를 (간접적으로라도) import하는 그 어떤 구문보다도 먼저 로드돼야 한다.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes.analysis import router as analysis_router  # noqa: E402
from app.api.routes.research import router as research_router  # noqa: E402
from app.api.routes.stocks import router as stocks_router  # noqa: E402
from app.core.config import CORS_ORIGINS  # noqa: E402

app = FastAPI(title="Stock Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks_router)
app.include_router(analysis_router)
app.include_router(research_router)


@app.get("/health")
def health():
    return {"status": "ok"}
