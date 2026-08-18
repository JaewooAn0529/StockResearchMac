# stock-research-app / macapp

개인용 macOS 주식 리서치 앱 (SwiftUI, Swift Package Manager 기반 — Xcode
프로젝트 파일 없이 커맨드라인으로 빌드/실행된다). 백엔드(`../backend`)가
`localhost:8000`에 떠 있어야 동작한다.

## 개발 중 빠르게 확인할 때

```bash
cd macapp
swift build      # 컴파일만
swift run        # 빌드 + 실행 (창이 뜬다)
```

## 진짜 앱처럼 더블클릭으로 쓸 때

`swift run`으로 띄운 프로세스는 제대로 된 `.app` 번들이 아니라서 Info.plist가
없다 — 그래서 로컬호스트(`http://localhost:8000`, 평문 HTTP) 접근을 위한
ATS 예외가 안 먹히고, 검색창에 키보드 포커스가 안 잡히는 문제가 있었다
(둘 다 실제로 겪은 문제 — `StockResearchMacApp.swift`의 `AppDelegate`가
포커스 문제는 코드로 우회했지만, ATS 예외는 Info.plist가 있어야 한다).

```bash
./build_app.sh
```

이 스크립트가 하는 일:
1. release 빌드
2. `build/StockResearchMac.app` 번들 조립 (`Info.plist` 포함)
3. ad-hoc 코드사인 (배포용 아니라 신원 서명 불필요)
4. `/Applications`로 복사 + Launch Services에 강제 등록

**`/Applications`에만 있어야 한다** — 개발 폴더에도 같은 번들 ID(`com.jaewoo.stockresearch`)
사본이 남아있으면 Launch Services가 launchpad/`open -a`에서 어느 걸 열지
헷갈려서 엉뚱한(오래된) 사본이 뜬다. 재빌드할 때마다 스크립트가 알아서
`/Applications` 사본을 덮어쓴다.

이후로는 런치패드/스포트라이트에서 "StockResearchMac"으로 바로 실행 가능.
