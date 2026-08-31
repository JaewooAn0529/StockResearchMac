# StockResearchMac

A personal research app for Korean stocks (KOSPI/KOSDAQ). Bundles 9
empirically-grounded indicators, multi-agent AI debate, and a pixel-art office
scene into a single Mac-only tool. It isn't shipped to the App Store — a
personal tool meant to run only on the owner's own Mac.

## Structure

```
backend/    FastAPI server — pykrx/DART/Naver data + multi-agent LLM debate
macapp/     SwiftUI macOS app (Swift Package Manager, no Xcode project)
assets-gen/ Pixel-art character sprite generation pipeline (scripts only)
```

Each subdirectory's README has more detail: [backend/README.md](backend/README.md), [macapp/README.md](macapp/README.md)

## Features

**Research indicators (9 cards)** — price/chart, foreign/institutional flows,
PER/PBR valuation (including a 1-year band), brokerage consensus, technical
indicators (RSI, MACD, Bollinger Bands), volatility/beta, peer comparison,
disclosure calendar (D-day), risk-keyword filtering, related news.

**AI multi-agent debate** — 4 analysts run in parallel → bull/bear debate over
2 rounds → trader decision → risk manager review. If the risk manager rejects
or requests a revision, BUY/SELL is automatically downgraded to HOLD, while the
original decision is preserved and still shown on screen (a risk approval
gate). The LLM can be switched via environment variable between local Ollama
(free) and the Anthropic API (paid).

**Compliance safeguards** — once a buy price and buy date are entered, the
position dashboard shows profit/loss versus the current price as a pure
calculation only (no predictive element). The past-pattern reference feature
only uses past-tense phrasing ("historically, ...") and automatically blocks
itself with "not enough historical cases to reference" whenever the sample is
fewer than 2 cases. The global disclaimer notice is assembled directly by the
backend, so the frontend can't alter its wording.

**Audit & retrospective** — records the time spent on each debate stage and
the total number of LLM calls. Past decisions are logged as JSON Lines and
compared against actual stock prices after the fact (explicitly a record
lookup, not a prediction).

## Tech stack

- **Backend**: FastAPI, Python 3.11 (managed with uv), pykrx, DART Open API,
  Naver News API, Ollama / Anthropic API
- **macOS app**: SwiftUI, Swift Package Manager, NavigationStack
- **Infrastructure**: launchd for auto-start at login + automatic crash
  recovery

## Considered but not adopted

Backtested [Kronos](https://github.com/shiyu-coder/Kronos) (an open-source
price forecasting model trained on K-line data) on Samsung Electronics. It was
7x less accurate than the naive baseline of "yesterday's closing price stays
the same" — and setting accuracy aside, its approach of predicting a definite
future price as a number conflicts with this app's "fact-based calculation /
historical lookup only" principle, so it wasn't adopted.

## Asset licensing

The pixel-art character/furniture/tile sprites are sourced from
[pixel-agents](https://github.com/pixel-agents-hq/pixel-agents) (MIT License).
See [macapp/Sources/StockResearchMac/Resources/CREDITS.md](macapp/Sources/StockResearchMac/Resources/CREDITS.md)
for full attribution.

## License

The code in this repository is under the MIT License. See [LICENSE](LICENSE).

## Disclaimer

This app and this repository do not constitute investment advice. All
indicators, AI decisions, and historical pattern information are for
reference only — investment decisions, and responsibility for them, rest
solely with the user.
