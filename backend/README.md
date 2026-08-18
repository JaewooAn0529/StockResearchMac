# stock-research-app / backend

개인용 주식 리서치 도구의 백엔드. FastAPI로 pykrx/DART/네이버 데이터를 감싸서
7개 지표를 제공하고, 로컬 LLM(Ollama)으로 멀티에이전트 토론(BUY/SELL/HOLD)까지
낸다. macOS 앱(`../macapp`)이 이 서버(localhost:8000)를 호출한다.

## 실행 방법

pykrx>=1.2.x는 Python 3.10+가 필요하다. 이 머신 기본 Python은 3.9라
[uv](https://astral.sh/uv)로 3.11을 따로 설치해 venv를 만든다 (sudo/brew 불필요).

```bash
cd backend
curl -LsSf https://astral.sh/uv/install.sh | sh   # 최초 1회만
uv python install 3.11                             # 최초 1회만
uv venv --python 3.11 venv
source venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # KRX_ID/KRX_PW, DART_API_KEY 채우기 (아래 참고)
uvicorn app.main:app --reload
```

서버는 기본적으로 http://localhost:8000 에서 뜬다.

### KRX_ID / KRX_PW가 필요한 이유

pykrx는 **import되는 순간** `KRX_ID`/`KRX_PW` 환경변수로 data.krx.co.kr에 로그인을
시도하고, 성공한 세션으로 이후 모든 요청을 보낸다. 로그인 없이도 개별 종목
시세(`/price`)는 되지만, 종목 전체 목록(`/search`)과 수급 데이터(`/flows`)는
로그인 세션이 없으면 막힌다(400 응답). stock-briefing 프로젝트의 GitHub Actions
Secrets에 이미 등록된 값과 동일한 계정을 쓰면 된다.

`.env`는 pykrx를 (간접적으로라도) import하는 어떤 코드보다도 먼저 로드되어야
해서, `app/main.py` 맨 위에서 다른 import보다 먼저 `load_dotenv()`를 호출한다 —
순서를 바꾸면 로그인이 조용히 실패한다.

### DART_API_KEY가 필요한 이유

`/earnings-calendar`, `/risk-flags`가 DART Open API(opendart.fss.or.kr, 무료
가입)를 쓴다. 종목코드→DART 고유번호 매핑을 처음 요청할 때 한 번 내려받아
캐싱한다(약 3.6MB, ~1.2초).

### 멀티에이전트 토론(`/analysis/{ticker}/debate`) — Ollama 로컬 실행

기본은 `LLM_PROVIDER=ollama`(무료, 로컬)다. 클라우드 API 비용 없이 쓰려면:

```bash
# ollama 앱 설치 후
ollama pull qwen2.5:7b-instruct
```

`.env`의 `LLM_PROVIDER=anthropic`로 바꾸고 `ANTHROPIC_API_KEY`를 채우면
Claude API(유료)로 전환된다 — `ANTHROPIC_MODEL`/`ANTHROPIC_EFFORT`도 같이 설정.

Qwen2.5는 응답이 길어지면 중국어로 드리프트하는 경우가 실측됐다(`app/agents/client.py`
참고) — 시스템 프롬프트에 언어 강제 문구를 추가하고, 한자가 섞여 나오면 자동 재시도하고,
`max_tokens`를 실제 필요한 분량으로 타이트하게 잡아서 대응했다.

## 엔드포인트

- `GET /stocks/search?q=` — 종목명/티커 검색 (KIND 상장법인목록 기반, 로그인 불필요)
- `GET /stocks/{ticker}/price` — 현재가 + 최근 90일 일봉 OHLCV
- `GET /stocks/{ticker}/flows` — 외국인/기관 순매수 추이 (최근 90일, KRX 로그인 필요)
- `GET /stocks/{ticker}/valuation` — PER/PBR 현재값 + 최근 1년 밴드(min/median/max), KRX 로그인 필요
- `GET /stocks/{ticker}/consensus` — 증권사 컨센서스 투자의견·목표주가 (네이버금융/에프앤가이드 인용,
  자체 분석 아님 — `source` 필드로 출처 명시. 커버리지 없는 종목은 404)
- `GET /stocks/{ticker}/technical` — MA20/MA60 이격도, 20일 평균 대비 거래량 배율
- `GET /stocks/{ticker}/volatility` — 베타(KOSPI/KOSDAQ 지수 대비) + 연율화 변동성
- `GET /stocks/{ticker}/peers` — 동종업계(KIND 업종 분류) 종목들과 PER/PBR 비교. 종목 5개 조회하느라
  다소 느림(~9초) — 필요하면 나중에 캐싱 추가
- `GET /stocks/{ticker}/earnings-calendar` — 다음 정기공시 법정 제출기한 D-day
  (회사가 예고한 실적발표일이 아니라 자본시장법상 마감일 추정치 — `note` 필드에 명시)
- `GET /stocks/{ticker}/risk-flags` — 최근 180일 보호예수/의무보유/대량보유(5%+) 관련 공시.
  임원·주요주주 소유상황보고서처럼 일상적으로 나오는 유형은 소음이라 제외했다
- `GET /stocks/{ticker}/news` — 관련 뉴스 (제목+설명+링크, 네이버 뉴스 API)
- `GET /stocks/{ticker}/recovery-history?buy_price=` — **미래 예측 아님, 과거 사실 조회.**
  매수가 대비 지금과 비슷한 낙폭이었던 과거 사례들이 이전 고점을 회복하기까지 걸린
  일수의 평균/중앙값. 매수가보다 지금이 높거나 같으면 `applicable=false`(해당 없음),
  유사 사례가 2건 미만이면 `sufficient_sample=false`(통계 자체를 안 냄). `summary`
  문장은 반드시 과거형("~걸렸습니다")으로만 쓰고, 프론트는 이 문장을 그대로 표시만
  한다 — "다음에도 며칠 걸릴 것이다" 식 표현은 여기서도 프론트에서도 금지
- `POST /analysis/{ticker}/debate` — 4개 분석가(펀더멘털/뉴스/기술적/수급) → bull/bear
  토론(기본 2라운드) → 트레이더 BUY/SELL/HOLD → 리스크 매니저 approve/revise/reject.
  호출 10회가 순차로 도는 구조라 로컬 Ollama 기준 약 2분 걸린다

## 확인

```bash
curl "localhost:8000/stocks/search?q=LG에너지솔루션"
curl "localhost:8000/stocks/373220/price"
curl "localhost:8000/stocks/373220/flows"
curl "localhost:8000/stocks/005930/earnings-calendar"
curl "localhost:8000/stocks/005930/risk-flags"
curl -X POST "localhost:8000/analysis/005930/debate"
```
