# stock-research-app / backend

Backend for a personal stock research tool. Wraps pykrx/DART/Naver data with
FastAPI to provide 7 indicators, plus a local LLM (Ollama) that runs a
multi-agent debate to reach a BUY/SELL/HOLD decision. The macOS app
(`../macapp`) calls this server at localhost:8000.

## How to run

pykrx>=1.2.x requires Python 3.10+. Since this machine's default Python is
3.9, we install 3.11 separately with [uv](https://astral.sh/uv) and build the
venv from it (no sudo/brew required).

```bash
cd backend
curl -LsSf https://astral.sh/uv/install.sh | sh   # once only
uv python install 3.11                             # once only
uv venv --python 3.11 venv
source venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # fill in KRX_ID/KRX_PW, DART_API_KEY (see below)
uvicorn app.main:app --reload
```

The server runs at http://localhost:8000 by default.

### Why KRX_ID / KRX_PW are needed

The moment pykrx **is imported**, it attempts to log in to data.krx.co.kr
using the `KRX_ID`/`KRX_PW` environment variables, and sends every subsequent
request through that session if it succeeds. Individual stock prices
(`/price`) work even without logging in, but the full ticker list (`/search`)
and flow data (`/flows`) are blocked (400 response) without a login session.
The same account already registered in the stock-briefing project's GitHub
Actions Secrets can be reused here.

`.env` needs to load before any code that imports pykrx (even indirectly), so
`load_dotenv()` is called at the very top of `app/main.py`, ahead of every
other import — reordering it makes the login fail silently.

### Why DART_API_KEY is needed

`/earnings-calendar` and `/risk-flags` use the DART Open API
(opendart.fss.or.kr, free registration). The ticker → DART corporate-code
mapping is downloaded and cached the first time it's requested (about 3.6MB,
~1.2 seconds).

### Multi-agent debate (`/analysis/{ticker}/debate`) — running Ollama locally

The default is `LLM_PROVIDER=ollama` (free, local). To use it with no cloud
API cost:

```bash
# after installing the ollama app
ollama pull qwen2.5:7b-instruct
```

Switching `.env`'s `LLM_PROVIDER` to `anthropic` and filling in
`ANTHROPIC_API_KEY` switches to the Claude API (paid) — also set
`ANTHROPIC_MODEL`/`ANTHROPIC_EFFORT`.

We observed Qwen2.5 drifting into Chinese as its responses get longer (see
`app/agents/client.py`) — addressed by adding a language-enforcement
instruction to the system prompt, automatically retrying whenever Chinese
characters appear, and setting `max_tokens` tightly to the amount actually
needed.

## Endpoints

- `GET /stocks/search?q=` — search by stock name/ticker (based on the KIND
  listed-company list, no login required)
- `GET /stocks/{ticker}/price` — current price + daily OHLCV for the last 90
  days
- `GET /stocks/{ticker}/flows` — foreign/institutional net buying trend (last
  90 days, requires KRX login)
- `GET /stocks/{ticker}/valuation` — current PER/PBR + 1-year band
  (min/median/max), requires KRX login
- `GET /stocks/{ticker}/consensus` — brokerage consensus rating and target
  price (quoted from Naver Finance/FnGuide, not our own analysis — the source
  is stated in the `source` field. Returns 404 for tickers without coverage)
- `GET /stocks/{ticker}/technical` — MA20/MA60 deviation, volume ratio versus
  the 20-day average
- `GET /stocks/{ticker}/volatility` — beta (relative to the KOSPI/KOSDAQ
  index) + annualized volatility
- `GET /stocks/{ticker}/peers` — PER/PBR comparison against peers (by KIND
  industry classification). Somewhat slow (~9s) since it queries 5 stocks —
  add caching later if needed
- `GET /stocks/{ticker}/earnings-calendar` — D-day to the statutory filing
  deadline for the next regular disclosure (an estimate of the Capital
  Markets Act deadline, not the company's announced earnings date — stated in
  the `note` field)
- `GET /stocks/{ticker}/risk-flags` — lock-up/mandatory-holding/large-holding
  (5%+) disclosures from the last 180 days. Routine filing types, such as
  executive/major-shareholder ownership reports, are excluded as noise
- `GET /stocks/{ticker}/news` — related news (title + description + link,
  Naver News API)
- `GET /stocks/{ticker}/recovery-history?buy_price=` — **not a future
  prediction, a historical fact lookup.** The average/median number of days
  it took past cases with a similar drawdown from the buy price to recover to
  their prior high. Returns `applicable=false` (not applicable) if the
  current price is higher than or equal to the buy price, and
  `sufficient_sample=false` (no statistics computed) if there are fewer than
  2 similar cases. The `summary` sentence is always phrased in the past tense
  ("it took ... days"), and the frontend only displays this sentence
  verbatim — phrasing like "it will take a few days next time" is prohibited
  both here and on the frontend
- `POST /analysis/{ticker}/debate` — 4 analysts (fundamentals/news/
  technical/flow) → bull/bear debate (2 rounds by default) → trader
  BUY/SELL/HOLD → risk manager approve/revise/reject. Since 10 calls run
  sequentially, this takes about 2 minutes with local Ollama

## Verifying

```bash
curl "localhost:8000/stocks/search?q=LG에너지솔루션"
curl "localhost:8000/stocks/373220/price"
curl "localhost:8000/stocks/373220/flows"
curl "localhost:8000/stocks/005930/earnings-calendar"
curl "localhost:8000/stocks/005930/risk-flags"
curl -X POST "localhost:8000/analysis/005930/debate"
```
