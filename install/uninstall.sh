#!/usr/bin/env bash
# Removes the Cat'sTube2Mp3 helper. Your downloaded MP3 files are not touched.
set -euo pipefail

HOST_NAME="catstube2mp3.helper"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/catstube2mp3"

for dir in \
  "$HOME/.mozilla/native-messaging-hosts" \
  "$HOME/.config/google-chrome/NativeMessagingHosts" \
  "$HOME/.config/chromium/NativeMessagingHosts" \
  "$HOME/.config/microsoft-edge/NativeMessagingHosts" \
  "$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts" \
  "$HOME/snap/chromium/common/chromium/NativeMessagingHosts"; do
  rm -f "$dir/$HOST_NAME.json"
done
rm -rf "$APP_DIR"
echo "Cat'sTube2Mp3 helper removed. Remove the browser extension from the browser's add-ons page."
