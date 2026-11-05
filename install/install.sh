#!/usr/bin/env bash
# Cat'sTube2Mp3 helper installer for Linux.
# Installs the helper into ~/.local/share/catstube2mp3 and registers it with Firefox and Chrome/Chromium.
# No root needed, except to install ffmpeg/python3-venv if they are missing.
set -euo pipefail

HOST_NAME="catstube2mp3.helper"
FIREFOX_ID="catstube2mp3@catstube2mp3.local"
CHROME_ID="ohhfjoepjlifkbodjampofpmdbplgccg"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/catstube2mp3"
LAUNCHER="$APP_DIR/catstube2mp3-host"

say() { printf '\033[1;33m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

say "Checking requirements"
command -v python3 >/dev/null || fail "python3 is not installed. Install it with: sudo apt install python3"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || fail "Python 3.10 or newer is needed."
missing=()
python3 -c 'import ensurepip' 2>/dev/null || missing+=(python3-venv)
command -v ffmpeg >/dev/null || missing+=(ffmpeg)
if ((${#missing[@]})); then
  fail "Missing: ${missing[*]}. Install with: sudo apt install ${missing[*]}  (then run this script again)"
fi

say "Installing helper to $APP_DIR"
mkdir -p "$APP_DIR/helper"
cp "$REPO_DIR"/helper/*.py "$REPO_DIR/helper/requirements.txt" "$APP_DIR/helper/"

if [[ ! -x "$APP_DIR/venv/bin/python" ]]; then
  python3 -m venv "$APP_DIR/venv"
fi
say "Installing yt-dlp and deno (this can take a minute)"
"$APP_DIR/venv/bin/python" -m pip install --quiet --upgrade --disable-pip-version-check -r "$APP_DIR/helper/requirements.txt"

cat > "$LAUNCHER" <<EOF
#!/bin/sh
exec "$APP_DIR/venv/bin/python" "$APP_DIR/helper/catstube2mp3_host.py" "\$@"
EOF
chmod +x "$LAUNCHER"

say "Registering with browsers"
write_manifest() {  # $1 = directory, $2 = "firefox" or "chrome"
  mkdir -p "$1"
  if [[ $2 == firefox ]]; then
    allowed="\"allowed_extensions\": [\"$FIREFOX_ID\"]"
  else
    allowed="\"allowed_origins\": [\"chrome-extension://$CHROME_ID/\"]"
  fi
  cat > "$1/$HOST_NAME.json" <<EOF
{
  "name": "$HOST_NAME",
  "description": "Cat'sTube2Mp3 helper",
  "path": "$LAUNCHER",
  "type": "stdio",
  $allowed
}
EOF
  echo "    $1/$HOST_NAME.json"
}
write_manifest "$HOME/.mozilla/native-messaging-hosts" firefox
# Chrome-family browsers: only those that have been run at least once (their profile folder exists).
# Installed a new browser later? Run this script again.
for profile in \
  "$HOME/.config/google-chrome" \
  "$HOME/.config/chromium" \
  "$HOME/.config/microsoft-edge" \
  "$HOME/.config/BraveSoftware/Brave-Browser" \
  "$HOME/snap/chromium/common/chromium"; do
  if [[ -d "$profile" ]]; then
    write_manifest "$profile/NativeMessagingHosts" chrome
  fi
done

say "Testing the helper"
"$APP_DIR/venv/bin/python" - "$LAUNCHER" <<'EOF'
import json, struct, subprocess, sys
data = json.dumps({"cmd": "ping"}).encode()
out = subprocess.run([sys.argv[1]], input=struct.pack("=I", len(data)) + data, capture_output=True, timeout=60).stdout
reply = json.loads(out[4:])
if not reply.get("ok"):
    sys.exit("Helper test failed: " + str(reply))
print(f"    helper {reply['helper']}, yt-dlp {reply['ytdlp']}, ffmpeg: {'yes' if reply['ffmpeg'] else 'NO'}, "
      f"JavaScript runtime: {reply['jsRuntime'] or 'NONE'}")
EOF

say "Done! Restart your browser, then click the Cat'sTube2Mp3 icon on a YouTube playlist."
