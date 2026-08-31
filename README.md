# StockResearchMac

한국 주식(KOSPI·KOSDAQ) 개인용 리서치 앱. 9개 실측 지표부터 멀티에이전트 AI
토론, 픽셀아트 오피스 연출까지 하나의 맥 전용 도구로 묶었다. App Store에는
내지 않는, 본인 맥에서만 쓰는 개인용 도구다.

## 구성

```
backend/    FastAPI 서버 — pykrx/DART/네이버 데이터 + 멀티에이전트 LLM 토론
macapp/     SwiftUI macOS 앱 (Swift Package Manager, Xcode 프로젝트 없음)
assets-gen/ 픽셀아트 캐릭터 스프라이트 생성 파이프라인 (스크립트만 포함)
```

각 하위 디렉터리의 README에 더 자세한 설명이 있다: [backend/README.md](backend/README.md), [macapp/README.md](macapp/README.md)

## 기능

**리서치 지표 (9개 카드)** — 시세·차트, 외국인/기관 수급, PER/PBR 밸류에이션(1년
밴드 포함), 증권사 컨센서스, 기술적 지표(RSI·MACD·볼린저밴드), 변동성/베타,
동종업계 비교, 공시 일정(D-day), 리스크 키워드 필터링, 관련 뉴스.

**AI 멀티에이전트 토론** — 분석가 4인 병렬 분석 → 불/베어 2라운드 토론 →
트레이더 판단 → 리스크 매니저 검토. 리스크 매니저가 반려(reject)·수정요청
(revise)하면 BUY/SELL을 HOLD로 자동 강등하고, 원래 판단은 보존해 화면에
그대로 노출한다(리스크 승인 게이트). LLM은 로컬 Ollama(무료)와 Anthropic
API(유료) 중 환경변수로 전환 가능.

**컴플라이언스 안전장치** — 포지션 현황판은 매수가·매수일 입력 시 현재가
대비 손익을 순수 계산으로만 표시한다(예측 요소 없음). 과거 유사 패턴 참고
기능은 "역사적으로는~" 같은 과거형 문구만 쓰고, 표본이 2건 미만이면
"참고할 만한 과거 사례가 충분하지 않습니다"로 자동 차단한다. 전역 면책
고지는 백엔드가 직접 조립해 프론트가 임의로 문구를 바꿀 수 없다.

**감사·회고** — 토론 단계별 소요시간과 총 LLM 호출 수를 기록. 지난 판단은
JSON Lines로 남겨 실제 주가와 사후 대조한다(예측이 아닌 기록 조회임을
명시).

## 기술 스택

- **백엔드**: FastAPI, Python 3.11(uv로 관리), pykrx, DART Open API, 네이버
  뉴스 API, Ollama / Anthropic API
- **macOS 앱**: SwiftUI, Swift Package Manager, NavigationStack
- **인프라**: launchd로 로그인 시 자동 기동 + 크래시 자동 복구

## 검토했지만 채택하지 않은 것

[Kronos](https://github.com/shiyu-coder/Kronos)(K-line 데이터로 학습한
오픈소스 가격 예측 모델)를 삼성전자로 백테스트했다. "어제 종가가 그대로
유지된다"는 아무 판단도 없는 기준선보다 7배 부정확했고, 정확도를 떠나서도
미래 가격을 숫자로 확정 예측하는 방식이라 이 앱의 "사실 계산 / 과거 조회"
원칙과 맞지 않아 도입하지 않았다.

## 에셋 라이선스

픽셀아트 캐릭터/가구/타일은 [pixel-agents](https://github.com/pixel-agents-hq/pixel-agents)
(MIT License)에서 가져왔다. 자세한 출처는
[macapp/Sources/StockResearchMac/Resources/CREDITS.md](macapp/Sources/StockResearchMac/Resources/CREDITS.md)
참고.

## 라이선스

이 저장소의 코드는 MIT License. [LICENSE](LICENSE) 참고.

## 면책

이 앱과 이 저장소는 투자자문이 아니다. 모든 지표·AI 판단·과거 패턴 정보는
참고 자료일 뿐이며, 투자 판단과 그 책임은 사용자 본인에게 있다.
