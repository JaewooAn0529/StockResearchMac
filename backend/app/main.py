from dotenv import load_dotenv

# pykrx tries to log in using the KRX_ID/KRX_PW environment variables the moment it's
# imported, so .env must be loaded before any statement that imports pykrx (even indirectly).
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
