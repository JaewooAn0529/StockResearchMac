#!/bin/bash
# StockResearchMac.app 번들을 조립한다. 더블클릭으로 바로 실행하려면
# swift run 대신 이걸로 빌드해야 한다(Info.plist 없이는 창 활성화/네트워크
# 예외 같은 게 제대로 안 먹는다).
set -euo pipefail
cd "$(dirname "$0")"

# 실행 중인 사본을 확실히 종료하고 기다린다. pkill 직후 바로 rm -rf/cp를 돌리면
# 프로세스가 아직 안 죽은 상태라 /Applications 복사가 조용히 씹히는 걸 실측함
# (몇 번의 재빌드가 화면에 전혀 반영이 안 됐던 원인이 이거였다).
pkill -f "StockResearchMac.app/Contents/MacOS/StockResearchMac" 2>/dev/null || true
for i in 1 2 3 4 5; do
    pgrep -f "StockResearchMac.app/Contents/MacOS/StockResearchMac" > /dev/null || break
    sleep 0.5
done

swift build -c release

APP="StockResearchMac.app"
BUILD_DIR="build"
rm -rf "$BUILD_DIR/$APP"
mkdir -p "$BUILD_DIR/$APP/Contents/MacOS" "$BUILD_DIR/$APP/Contents/Resources"
cp .build/release/StockResearchMac "$BUILD_DIR/$APP/Contents/MacOS/"
cp Info.plist "$BUILD_DIR/$APP/Contents/Info.plist"
cp AppIcon.icns "$BUILD_DIR/$APP/Contents/Resources/"
# SPM이 만든 리소스 번들(캐릭터/배경 픽셀아트 이미지)도 넣어야 한다. 생성된
# resource_bundle_accessor.swift가 Bundle.main.bundleURL(=.app 최상위, Contents와
# 같은 레벨)에서 찾게 되어 있어서 Contents/Resources가 아니라 .app 바로 밑에 둔다
# (실제로 Contents/Resources에 뒀다가 이미지 로딩이 안 되는 걸 확인함)
cp -R .build/release/StockResearchMac_StockResearchMac.bundle "$BUILD_DIR/$APP/"

# 배포용 서명이 아니라 로컬에서만 도는 앱이라 ad-hoc 서명(신원 없이)으로 충분하다.
# 리소스 번들이 .app 최상위(Contents 밖)에 있어서 codesign이 "unsealed contents
# present" 경고를 내는데, 이게 종료코드까지 1로 나온다 — set -e 때문에 스크립트가
# 여기서 조용히 죽고 /Applications 복사·검증이 한 번도 안 도는 걸 한참 헤매고 찾음.
# 서명 자체는 실제로 성공하니(리소스만 unsealed, 실행파일은 정상 서명됨) 여기선
# 실패로 안 친다.
codesign --force --deep --sign - "$BUILD_DIR/$APP" || true

# 실제 실행은 항상 /Applications 사본으로 한다 — 두 군데 동시에 있으면
# 번들 ID가 같아서 Launch Services가 launchpad/open -a에서 어느 걸 열지
# 헷갈려 한다(실제로 겪은 문제).
rm -rf "/Applications/$APP"
cp -R "$BUILD_DIR/$APP" "/Applications/"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "/Applications/$APP"
touch "/Applications/$APP"
killall Dock 2>/dev/null || true  # 아이콘 캐시가 안 갱신될 때가 있어 Dock을 재시작한다(자동 재기동됨)

# 배포가 조용히 씹히는 걸 다시 겪지 않으려고, 실제로 새 바이너리로 갱신됐는지
# 검증한다. .build/release(서명 전)와 비교하면 코드사인 때문에 항상 달라서
# 의미가 없다 — 방금 서명한 build/ 사본과 /Applications 사본을 비교해야 한다.
if ! cmp -s "$BUILD_DIR/$APP/Contents/MacOS/StockResearchMac" "/Applications/$APP/Contents/MacOS/StockResearchMac"; then
    echo "오류: /Applications 사본이 방금 빌드한 것과 다릅니다 — 배포 실패" >&2
    exit 1
fi

# 새 바이너리로 다시 띄운다. `open -a`는 이미 떠 있는 프로세스가 있으면
# 재시작하지 않고 앞으로 가져오기만 해서, 옛 바이너리가 계속 돌며 새 에셋을
# 못 찾는 상황을 겪었다(캐릭터가 person.fill 플레이스홀더로 보였다).
# 반드시 /Applications 사본을 연다 — build/ 사본을 열면 번들 ID가 겹쳐서
# Launch Services가 어느 걸 열지 헷갈려 한다.
open "/Applications/$APP"

echo "설치 완료 및 검증됨 + 재실행: /Applications/$APP"
