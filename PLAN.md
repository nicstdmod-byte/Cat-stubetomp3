# Cat'sTube2Mp3 — project plan and decisions

Decisions made while planning (2026-11-05). Read this first when picking the project up again.

## Goal
Firefox + Chrome extension that downloads songs from YouTube playlists as MP3. Shared with friends and on GitHub
(repo name **CatsTube2Mp3**, since GitHub does not allow the apostrophe).

## Architecture
- **Extension** (plain JS/HTML/CSS, Manifest V3, no build step) → talks to the helper with native messaging.
- **Helper** (Python): yt-dlp downloads, ffmpeg converts to MP3, Deno is yt-dlp's JavaScript runtime for YouTube.
- One request per native message. Downloads run in a **detached worker process** that writes `state/job.json`;
  the popup polls `status` every second. So closing the popup does not stop a download.
- No custom `.exe` (antivirus false positives). Windows uses the official **embeddable Python from python.org**
  (signed by the Python Software Foundation) + a `.bat` launcher.

## Decided features
- Song list, Select all, single picks, Shift+click ranges, "✔ done" marks, unavailable songs greyed out
- MP3 128 / 192 / 320 kbps (default 192)
- Default file name **`{artist} - {title}.mp3`**; artist from "Artist - Song" titles, else channel name
  (without " - Topic" / "VEVO"); custom patterns with live preview
- Clean "(Official Video)" etc.; Windows-safe names; same name → "Name (2).mp3" or skip
- Tags (title, artist, album = playlist, track number) + cover art
- Skip already-downloaded songs (`.catstube2mp3-archive.txt` in each folder, by video ID)
- Settings page: folder with Browse…, subfolder pattern (default `{playlist}`), helper status, Update yt-dlp
- Default folder: Music folder / playlist name

## Platforms
- Friends mostly use **Windows** → `install/install.bat` (runs `install.ps1`).
- Linux supported too (developed on Ubuntu 26.04 with Snap Firefox; native messaging works through the portal).
- Firefox: sign as **unlisted** on addons.mozilla.org, share the `.xpi` on GitHub Releases.
- Chrome: Web Store does not allow YouTube downloaders → "Load unpacked" from `dist/chrome`.

## Status
- [x] Proof of concept: Snap Firefox ↔ Python helper
- [x] Helper: list, download, MP3, tags, cover art, skip done — tested on Linux
- [x] Extension popup + settings
- [x] Linux installer — tested
- [ ] Windows installer — written, **not yet tested on Windows**
- [ ] Test extension end-to-end in Firefox and Chrome
- [ ] Replace `YOUR-GITHUB-NAME` in `extension/common.js` with the real GitHub user name
- [ ] Create GitHub repo, sign Firefox build, first release

## Later ideas
Right-click "Download as MP3", several songs at once, notification when done, M4A/OPUS/FLAC, download history.
