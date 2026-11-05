# Installing Cat'sTube2Mp3 🐱🎧

Cat'sTube2Mp3 has **two parts**, and you need both:

| Part | What it does | Install once per… |
|---|---|---|
| **1. Helper** | A small program on your computer that downloads and converts songs to MP3 | computer |
| **2. Extension** | The cat button and popup in your browser | browser |

Install the helper first, then the extension, then restart the browser.

**Jump to your setup:**
[Windows helper](#windows--install-the-helper) ·
[Linux helper](#linux--install-the-helper) ·
[Firefox extension](#firefox--install-the-extension) ·
[Chrome / Edge / Brave extension](#chrome-edge-brave--install-the-extension) ·
[Check it works](#check-that-it-works) ·
[Problems?](#troubleshooting) ·
[Update](#updating) ·
[Uninstall](#uninstalling)

> Please only download content you have the right to download, such as your own uploads or music under a
> Creative Commons or public-domain license.

---

## Windows — install the helper

**You need:** Windows 10 or 11 (64-bit) and an internet connection. No admin rights needed.

1. **Download the project.**
   On the GitHub page, click the green **Code** button → **Download ZIP**.

2. **Unblock the ZIP (avoids security warnings later).**
   Right-click the downloaded ZIP → **Properties** → at the bottom, tick **Unblock** → **OK**.
   (If there is no Unblock box, skip this step.)

3. **Unzip it.**
   Right-click the ZIP → **Extract All…** → **Extract**.

4. **Run the installer.**
   Open the unzipped folder → open the **`install`** folder → double-click **`install.bat`**.

   - If you see **"Windows protected your PC"**: click **More info** → **Run anyway**.
   - A black window opens and shows progress. It downloads Python, yt-dlp and ffmpeg (about 150 MB),
     so it can take a few minutes.

5. **Wait for "Done!"**
   You should see a line like:
   ```
   helper 1.0.0, yt-dlp 2026.10.26, ffmpeg: yes, JavaScript runtime: deno
   ==> Done!
   ```
   Press any key to close the window.

**Where it goes:** `C:\Users\<you>\AppData\Local\CatsTube2Mp3`

**Is it safe?** The installer downloads only from official sources (python.org, PyPI and the yt-dlp ffmpeg builds)
and checks each download's fingerprint. The Python it uses is the official one, signed by the Python Software
Foundation. Everything else is readable Python code you can open in Notepad.

➡️ Now [install the extension](#firefox--install-the-extension).

---

## Linux — install the helper

**You need:** Ubuntu, Debian, Linux Mint or similar, with Python 3.10 or newer (already included in recent versions).

1. **Install ffmpeg and Python's venv module** (asks for your password):
   ```bash
   sudo apt install ffmpeg python3-venv
   ```
   Other distributions: install `ffmpeg` and Python's `venv` with your package manager
   (Fedora: `sudo dnf install ffmpeg python3`, Arch: `sudo pacman -S ffmpeg python`).

2. **Download the project:**
   ```bash
   git clone https://github.com/YOUR-GITHUB-NAME/CatsTube2Mp3.git
   cd CatsTube2Mp3
   ```
   No git? Download the ZIP from GitHub (green **Code** button → **Download ZIP**), unzip it, and open a
   terminal in that folder.

3. **Using Chrome, Chromium, Edge or Brave?** Open that browser once *before* the next step, so its settings
   folder exists. (Firefox users can skip this.)

4. **Run the installer** (no `sudo`):
   ```bash
   ./install/install.sh
   ```

5. **Wait for "Done!"** It should end with:
   ```
   helper 1.0.0, yt-dlp ..., ffmpeg: yes, JavaScript runtime: deno
   ==> Done!
   ```

**Where it goes:** `~/.local/share/catstube2mp3`

If you install another browser later, run `./install/install.sh` again.

➡️ Now install the extension for [Firefox](#firefox--install-the-extension) or
[Chrome / Edge / Brave](#chrome-edge-brave--install-the-extension).

---

## Firefox — install the extension

Works the same on Windows and Linux.

### Normal install (signed version)

1. Go to the project's **Releases** page on GitHub.
2. Download **`catstube2mp3-firefox-<version>.xpi`**.
3. Firefox asks whether to add **Cat'sTube2Mp3** → click **Add**.
   (If Firefox only saves the file: open `about:addons`, click the ⚙ gear → **Install Add-on From File…** →
   pick the `.xpi`.)
4. Optional: pin the cat to the toolbar. Click the 🧩 puzzle button → ⚙ next to Cat'sTube2Mp3 → **Pin to Toolbar**.

### Before a signed version is released (testing)

Regular Firefox only installs extensions that Mozilla has signed. Until a signed `.xpi` is on the Releases page,
load it temporarily. It stays until you close Firefox, so you need to do this again after each restart.

1. In the Firefox address bar, go to: `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on…**
3. Open the project folder → **`extension`** → pick **`manifest.json`**.

**Ubuntu with Snap Firefox:** the first time the extension talks to the helper, Firefox may ask for permission
to run a program outside the browser. Click **Allow**.

---

## Chrome, Edge, Brave — install the extension

Works the same on Windows and Linux. The Chrome Web Store doesn't allow YouTube download extensions, so it is
installed from a folder in **Developer mode**.

1. Go to the project's **Releases** page on GitHub and download **`catstube2mp3-chrome-<version>.zip`**.
2. Unzip it to a folder you will **keep**, for example `Documents\CatsTube2Mp3-extension`.
   ⚠️ Don't delete or move this folder later. The browser loads the extension from it.
3. Open the extensions page:
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
   - Brave: `brave://extensions`
4. Turn on **Developer mode** (top right in Chrome and Brave, left side in Edge).
5. Click **Load unpacked** and pick the unzipped folder (the one that contains `manifest.json`).
6. Optional: click the 🧩 puzzle button → 📌 pin next to Cat'sTube2Mp3.

**No Releases yet?** Build it yourself from the project folder: `python3 scripts/build.py` (Linux) or
`python scripts\build.py` (Windows, if Python is installed), then load the **`dist/chrome`** folder in step 5.

**Notes**
- Chrome may show a warning about developer-mode extensions when it starts. That's normal for extensions
  installed this way.
- Updates are not automatic. See [Updating](#updating).
- Linux: the Snap version of Chromium may block the helper. Google Chrome, Brave, or Chromium from your
  distribution's repository (not Snap) work best.

---

## Check that it works

1. **Restart your browser** (close all windows, then open it again).
2. Click the 🐱 icon → **⚙ Settings**. Under **Helper** you should see:
   ```
   ✔ Helper connected
   ✔ yt-dlp 2026.x.x
   ✔ ffmpeg found
   ✔ JavaScript runtime: deno
   ```
3. Open a YouTube playlist or video, click the 🐱 icon, pick songs, and click **Download**.
4. Your MP3s are saved in your **Music** folder, inside a folder named after the playlist.
   Click **Open folder** in the popup to go there.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| **"The Cat'sTube2Mp3 helper is not installed"** | Run the installer again (`install.bat` or `install.sh`), then fully restart the browser. |
| Chrome on Linux says helper not installed | Open Chrome once, then run `./install/install.sh` again and restart Chrome. |
| Downloads fail with a YouTube error | Settings → **Update yt-dlp**. YouTube changes often, and an update usually fixes it. |
| A song shows **unavailable** | The video is private, deleted, or blocked in your country. It is skipped. |
| Windows: the installer window closes immediately | Right-click `install\install.ps1` → **Run with PowerShell** to see the error message. |
| Windows: antivirus blocks something | Tell us which file was flagged. You can check the code in the `helper` folder. |
| Firefox extension disappeared | The temporary version is removed when Firefox closes. Load it again, or install the signed `.xpi`. |
| Chrome extension stopped working | Check that the unzipped extension folder still exists in the same place. |
| ✖ ffmpeg or ✖ yt-dlp in Settings | Run the installer again. On Linux, check that `ffmpeg` is installed (`sudo apt install ffmpeg`). |

**Log file** (useful when reporting a problem):
- Windows: `%LOCALAPPDATA%\CatsTube2Mp3\state\helper.log` (paste this into the Explorer address bar)
- Linux: `~/.local/share/catstube2mp3/state/helper.log`

Report problems on the GitHub **Issues** page and include the log and what you clicked.

---

## Updating

- **yt-dlp** (the part that breaks most often when YouTube changes): Settings → **Update yt-dlp**.
- **Helper**: download the new version of the project and run the installer again. Your settings and MP3s are kept.
- **Firefox extension**: install the new `.xpi` from Releases over the old one.
- **Chrome extension**: unzip the new version over the old folder (replace the files), then click the ⟳
  reload button on Cat'sTube2Mp3 on the extensions page.

---

## Uninstalling

1. **Remove the extension**
   - Firefox: `about:addons` → Cat'sTube2Mp3 → **⋯** → **Remove**
   - Chrome / Edge / Brave: extensions page → Cat'sTube2Mp3 → **Remove**
2. **Remove the helper**
   - Windows: double-click **`install\uninstall.bat`**
   - Linux: run `./install/uninstall.sh`

Your downloaded MP3 files are **not** deleted.
