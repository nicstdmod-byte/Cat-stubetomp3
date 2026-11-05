# Cat'sTube2Mp3 🐱🎧

A Firefox and Chrome extension that saves songs from YouTube playlists as MP3 files, with song info and cover art.

> **Please use it responsibly.** Only download content you have the right to download, such as your own uploads or
> music under a Creative Commons or public-domain license. YouTube's terms of service do not allow downloading most
> videos, and copyright still applies to most music.

## Features

- Works on any YouTube playlist or video page (also YouTube Music)
- Song list with **Select all**, single picks, and **Shift+click** to pick a range
- MP3 at **128 / 192 / 320 kbps**
- File names like `Artist - Song.mp3`, or your own pattern (`{artist}`, `{title}`, `{track}`, `{playlist}`, `{channel}`, `{date}`, `{id}`)
- Removes clutter like "(Official Video)" and "[Lyrics]" from names
- Adds title, artist, album (the playlist name), track number and cover art to each MP3
- Skips songs you already downloaded, so running a playlist again only gets new songs
- Skips private and deleted videos and keeps going
- Downloads keep running when you close the popup; open it again to see progress
- Settings page: save folder with **Browse…**, naming preview, quality, and an **Update yt-dlp** button

## How it works

Browsers cannot download from YouTube or make MP3 files by themselves, so Cat'sTube2Mp3 has two parts:

1. **The extension**: the popup and settings in your browser.
2. **The helper**: a small Python program on your computer that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp)
   to download and [ffmpeg](https://ffmpeg.org) to convert to MP3. The extension talks to it through the browser's
   "native messaging" feature.

The helper is plain, readable Python. On Windows the installer uses the official Python from python.org
(signed by the Python Software Foundation), so there is no unknown `.exe` for antivirus software to flag.

## Install

**👉 Full step-by-step guide: [INSTALL.md](INSTALL.md)** (Windows and Linux, Firefox and Chrome)

Quick version:

1. **Helper:** Windows: double-click `install/install.bat`. Linux: `sudo apt install ffmpeg python3-venv`,
   then `./install/install.sh`.
2. **Extension:** Firefox: install the `.xpi` from [Releases](../../releases). Chrome/Edge/Brave: unzip the
   Chrome zip from Releases → `chrome://extensions` → Developer mode → **Load unpacked**.
3. Restart the browser.

## Use

1. Open a YouTube playlist (or video).
2. Click the 🐱 Cat'sTube2Mp3 icon (in Firefox it may be under the 🧩 puzzle button).
3. Pick songs and click **Download**.

Change the save folder, file names and quality in **⚙ Settings**.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Helper is not installed" | Run the installer again, then restart the browser. |
| Downloads fail with a YouTube error | Settings → **Update yt-dlp**. YouTube changes often. |
| A song shows "unavailable" | It is private, deleted or blocked in your country. |
| Firefox on Ubuntu (Snap) does not find the helper | Make sure `xdg-desktop-portal` is installed and up to date, then restart Firefox. |

Logs are in `state/helper.log` inside the install folder.

## Uninstall

Remove the extension from the browser, then run `install/uninstall.bat` (Windows) or `install/uninstall.sh` (Linux).
Your MP3 files are not touched.

## For developers

```
extension/   popup, settings page, icons (one codebase for Firefox and Chrome)
helper/      Python native messaging host + naming rules
install/     installers for Windows and Linux
scripts/     build.py (packages both browsers), make_icons.py
tests/       unit tests for the naming rules
```

- Run tests: `python3 -m unittest discover -s tests`
- Build: `python3 scripts/build.py` → `dist/`
- Try in Firefox: `about:debugging#/runtime/this-firefox` → **Load Temporary Add-on…** → `extension/manifest.json`
- Try in Chrome: `chrome://extensions` → **Load unpacked** → `dist/chrome`
- Firefox signing: upload `dist/catstube2mp3-firefox-<version>.zip` at
  [addons.mozilla.org/developers](https://addons.mozilla.org/developers/) as **"On your own"** (unlisted).
  Mozilla returns a signed `.xpi` to attach to a GitHub release.

The Chrome extension ID is fixed by the public key in `scripts/chrome-public-key.txt`
(ID `ohhfjoepjlifkbodjampofpmdbplgccg`); the installers use it to allow only this extension to talk to the helper.

## License

MIT, see [LICENSE](LICENSE). yt-dlp, ffmpeg, Python and Deno are downloaded by the installer and keep their own licenses.
