# stock-research-app / macapp

A personal macOS stock research app (SwiftUI, built on Swift Package Manager
— built and run from the command line with no Xcode project file). Requires
the backend (`../backend`) to be running at `localhost:8000`.

## Quick checks during development

```bash
cd macapp
swift build      # compile only
swift run        # build + run (opens a window)
```

## Using it like a real double-click app

The process launched by `swift run` isn't a proper `.app` bundle, so it has
no Info.plist — which meant the ATS exception for localhost access
(`http://localhost:8000`, plain HTTP) didn't apply, and the search field
couldn't grab keyboard focus (both problems were actually encountered — the
`AppDelegate` in `StockResearchMacApp.swift` works around the focus issue in
code, but the ATS exception needs an actual Info.plist).

```bash
./build_app.sh
```

What this script does:
1. Builds a release build
2. Assembles the `build/StockResearchMac.app` bundle (including
   `Info.plist`)
3. Ad-hoc code-signs it (no identity signing needed since this isn't for
   distribution)
4. Copies it to `/Applications` and force-registers it with Launch Services

**It must live only in `/Applications`** — if a copy with the same bundle ID
(`com.jaewoo.stockresearch`) is also left in the development folder, Launch
Services gets confused about which one to open from Launchpad/`open -a`, and
the wrong (stale) copy launches instead. On every rebuild, the script
overwrites the `/Applications` copy automatically.

After that, you can launch it directly as "StockResearchMac" from
Launchpad/Spotlight.
