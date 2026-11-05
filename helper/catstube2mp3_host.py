#!/usr/bin/env python3
"""Cat'sTube2Mp3 native messaging host.

The browser extension starts this script for every request (one JSON message in,
one JSON reply out). Downloads run in a separate detached worker process, so they
keep going after the popup closes; the popup polls "status" to show progress.
"""
import importlib.metadata
import json
import logging
import os
import platform
import shutil
import struct
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import naming  # noqa: E402

HELPER_VERSION = "1.0.0"
IS_WINDOWS = platform.system() == "Windows"
APP_DIR = Path(__file__).resolve().parent.parent  # install root: helper/, python/ or venv/, ffmpeg/
STATE_DIR = APP_DIR / "state"
JOB_FILE = STATE_DIR / "job.json"
CANCEL_FILE = STATE_DIR / "cancel"
ARCHIVE_NAME = ".catstube2mp3-archive.txt"

DEFAULT_SETTINGS = {
    "baseFolder": "",
    "subfolderPattern": "{playlist}",
    "namePattern": "{artist} - {title}",
    "quality": "192",
    "cleanJunk": True,
    "embedMetadata": True,
    "embedThumbnail": True,
    "onExisting": "number",  # "number" -> "Name (2).mp3", "skip" -> leave the old file
}
UNAVAILABLE_TITLES = {"[private video]", "[deleted video]", "[unavailable video]"}

STATE_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=STATE_DIR / "helper.log",
    level=logging.INFO,
    format="%(asctime)s %(process)d %(levelname)s %(message)s",
)
log = logging.getLogger("catstube2mp3")


# ---------------------------------------------------------------- messaging

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) < 4:
        return None
    length = struct.unpack("=I", raw_length)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def send_message(message):
    data = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


# ---------------------------------------------------------------- helpers

def merged_settings(settings):
    return {**DEFAULT_SETTINGS, **{k: v for k, v in (settings or {}).items() if v not in (None, "")}}


def default_music_dir():
    if IS_WINDOWS:
        try:
            import ctypes
            from ctypes import wintypes
            # FOLDERID_Music
            guid = (ctypes.c_byte * 16)(*uuid.UUID("{4BD8D571-6D19-48D3-BE97-422220080E43}").bytes_le)
            path_ptr = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(path_ptr)) == 0:
                path = path_ptr.value
                ctypes.windll.ole32.CoTaskMemFree(path_ptr)
                return path
        except Exception:
            log.exception("SHGetKnownFolderPath failed")
    elif shutil.which("xdg-user-dir"):
        try:
            path = subprocess.run(["xdg-user-dir", "MUSIC"], capture_output=True, text=True, timeout=5).stdout.strip()
            if path and path != str(Path.home()):
                return path
        except Exception:
            log.exception("xdg-user-dir failed")
    return str(Path.home() / "Music")


def base_folder(settings):
    return Path(settings.get("baseFolder") or default_music_dir()).expanduser()


def find_ffmpeg():
    bundled = APP_DIR / "ffmpeg" / "bin" / ("ffmpeg.exe" if IS_WINDOWS else "ffmpeg")
    if bundled.exists():
        return str(bundled)
    return shutil.which("ffmpeg")


def find_deno():
    scripts = Path(sys.executable).parent
    for candidate in (scripts / "deno", scripts / "deno.exe", scripts / "Scripts" / "deno.exe"):
        if candidate.exists():
            return str(candidate)
    return shutil.which("deno")


def ytdlp_version():
    try:
        return importlib.metadata.version("yt-dlp")
    except importlib.metadata.PackageNotFoundError:
        return None


def base_ydl_options():
    options = {"quiet": True, "no_warnings": True, "noprogress": True}
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        options["ffmpeg_location"] = ffmpeg
    deno = find_deno()
    if deno:
        options["js_runtimes"] = {"deno": {"path": deno}}
    elif shutil.which("node"):
        options["js_runtimes"] = {"node": {}}
    return options


def read_archive(folder):
    try:
        return set((folder / ARCHIVE_NAME).read_text(encoding="utf-8").split())
    except FileNotFoundError:
        return set()


def write_json_atomic(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def read_job():
    try:
        return json.loads(JOB_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def pid_alive(pid):
    if not pid:
        return False
    if IS_WINDOWS:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def job_is_running(job):
    return bool(job) and job.get("state") == "running" and pid_alive(job.get("pid"))


def friendly_error(err):
    text = str(err).replace("ERROR: ", "").strip()
    return text.split("\n")[0][:300] or err.__class__.__name__


def open_path(path):
    if IS_WINDOWS:
        os.startfile(path)  # noqa: S606 - opens Explorer
    else:
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- commands

def cmd_ping(_msg):
    return {
        "helper": HELPER_VERSION,
        "python": platform.python_version(),
        "system": platform.system(),
        "ytdlp": ytdlp_version(),
        "ffmpeg": bool(find_ffmpeg()),
        "jsRuntime": "deno" if find_deno() else ("node" if shutil.which("node") else None),
        "musicDir": default_music_dir(),
    }


def cmd_preview(msg):
    settings = merged_settings(msg.get("settings"))
    samples = msg.get("samples") or []
    return {
        "names": [naming.build_filename(sample, settings) + ".mp3" for sample in samples],
        "folder": str(base_folder(settings).joinpath(*naming.build_subfolder("My Playlist", "Channel", settings))),
    }


def cmd_list(msg):
    import yt_dlp

    url = msg["url"]
    settings = merged_settings(msg.get("settings"))
    options = {**base_ydl_options(), "extract_flat": "in_playlist", "skip_download": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("Could not read this page. Is it a YouTube video or playlist?")

    is_playlist = info.get("_type") == "playlist"
    raw_entries = [e for e in (info.get("entries") or []) if e] if is_playlist else [info]
    playlist = info.get("title", "") if is_playlist else ""
    playlist_channel = info.get("channel") or info.get("uploader") or ""
    folder = base_folder(settings).joinpath(*naming.build_subfolder(playlist, playlist_channel, settings))
    archive = read_archive(folder)

    entries = []
    for index, raw in enumerate(raw_entries, start=1):
        title = raw.get("title") or ""
        entry = {
            "id": raw.get("id", ""),
            "url": raw.get("url") or raw.get("webpage_url") or f"https://www.youtube.com/watch?v={raw.get('id', '')}",
            "title": title,
            "channel": raw.get("channel") or raw.get("uploader") or "",
            "duration": raw.get("duration"),
            "index": index,
            "total": len(raw_entries),
            "playlist": playlist,
        }
        entry["filename"] = naming.build_filename(entry, settings) + ".mp3"
        entry["unavailable"] = title.lower() in UNAVAILABLE_TITLES or raw.get("availability") in {"private", "needs_auth"}
        entry["done"] = entry["id"] in archive or (folder / entry["filename"]).exists()
        entries.append(entry)

    return {"playlist": playlist, "isPlaylist": is_playlist, "folder": str(folder), "entries": entries}


def cmd_start(msg):
    job = read_job()
    if job_is_running(job):
        raise RuntimeError("A download is already running. Wait for it to finish or cancel it.")

    settings = merged_settings(msg.get("settings"))
    entries = msg.get("entries") or []
    if not entries:
        raise RuntimeError("No songs selected.")

    folder = Path(msg["folder"])
    job = {
        "id": uuid.uuid4().hex,
        "state": "running",
        "pid": None,
        "playlist": msg.get("playlist", ""),
        "folder": str(folder),
        "settings": settings,
        "started": time.time(),
        "items": [
            {**entry, "status": "queued", "percent": 0, "error": None}
            for entry in entries
        ],
    }
    CANCEL_FILE.unlink(missing_ok=True)
    write_json_atomic(JOB_FILE, job)

    command = [sys.executable, str(Path(__file__).resolve()), "--worker"]
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    if IS_WINDOWS:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if pythonw.exists():
            command[0] = str(pythonw)
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        try:
            # Break out of the browser's job object so closing the popup does not kill the download.
            process = subprocess.Popen(command, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB, **kwargs)
        except OSError:
            process = subprocess.Popen(command, creationflags=flags, **kwargs)
    else:
        process = subprocess.Popen(command, start_new_session=True, **kwargs)

    # The worker records its own pid too; fill it in here only if it has not started writing yet.
    current = read_job() or job
    if not current.get("pid"):
        current["pid"] = process.pid
        write_json_atomic(JOB_FILE, current)
    return {"jobId": job["id"]}


def cmd_status(_msg):
    job = read_job()
    if job and job.get("state") == "running" and job.get("pid") and not pid_alive(job["pid"]):
        job["state"] = "error"
        job["error"] = "The download stopped unexpectedly. See helper.log for details."
        write_json_atomic(JOB_FILE, job)
    return {"job": job}


def cmd_cancel(_msg):
    CANCEL_FILE.write_text("1")
    return {"ok": True}


def cmd_clear(_msg):
    job = read_job()
    if job_is_running(job):
        raise RuntimeError("Cannot clear a running download.")
    JOB_FILE.unlink(missing_ok=True)
    return {"ok": True}


def cmd_pick_folder(msg):
    start = msg.get("current") or default_music_dir()
    if IS_WINDOWS:
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
            "$d.Description = 'Choose where Cat''sTube2Mp3 saves MP3 files';"
            "$d.SelectedPath = $env:CT2M_START;"
            "$f = New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
            "if ($d.ShowDialog($f) -eq 'OK') { [Console]::Out.Write($d.SelectedPath) }"
        )
        command = ["powershell", "-NoProfile", "-STA", "-Command", script]
        env = {**os.environ, "CT2M_START": start}
        result = subprocess.run(command, capture_output=True, text=True, env=env,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    elif shutil.which("zenity"):
        result = subprocess.run(
            ["zenity", "--file-selection", "--directory", "--title=Choose where Cat'sTube2Mp3 saves MP3 files",
             f"--filename={start.rstrip('/')}/"],
            capture_output=True, text=True)
    elif shutil.which("kdialog"):
        result = subprocess.run(["kdialog", "--getexistingdirectory", start], capture_output=True, text=True)
    else:
        raise RuntimeError("No folder picker found. Install zenity, or type the folder path instead.")
    path = result.stdout.strip()
    return {"path": path or None}


def cmd_open_folder(msg):
    folder = Path(msg["folder"])
    folder.mkdir(parents=True, exist_ok=True)
    open_path(folder)
    return {"ok": True}


def cmd_update_ytdlp(_msg):
    if job_is_running(read_job()):
        raise RuntimeError("Wait for the current download to finish before updating.")
    before = ytdlp_version()
    command = [sys.executable, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check",
               "--no-warn-script-location", "yt-dlp[default]"]
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if IS_WINDOWS else {}
    result = subprocess.run(command, capture_output=True, text=True, timeout=600, **kwargs)
    if result.returncode != 0:
        log.error("pip update failed: %s", result.stderr)
        raise RuntimeError("Update failed: " + (result.stderr.strip().splitlines() or ["unknown error"])[-1])
    after = subprocess.run([sys.executable, "-c", "import importlib.metadata as m; print(m.version('yt-dlp'))"],
                           capture_output=True, text=True, **kwargs).stdout.strip()
    return {"before": before, "after": after or before}


COMMANDS = {
    "ping": cmd_ping,
    "preview": cmd_preview,
    "list": cmd_list,
    "start": cmd_start,
    "status": cmd_status,
    "cancel": cmd_cancel,
    "clear": cmd_clear,
    "pick_folder": cmd_pick_folder,
    "open_folder": cmd_open_folder,
    "update_ytdlp": cmd_update_ytdlp,
}


def serve():
    message = read_message()
    if message is None:
        return
    command = message.get("cmd")
    try:
        handler = COMMANDS.get(command)
        if not handler:
            raise RuntimeError(f"Unknown command: {command}")
        send_message({"ok": True, **handler(message)})
    except Exception as err:
        log.error("Command %s failed:\n%s", command, traceback.format_exc())
        send_message({"ok": False, "error": friendly_error(err)})


# ---------------------------------------------------------------- worker

class Cancelled(Exception):
    pass


def unique_path(folder, name, settings, video_id, archive):
    """Path for name.mp3, or None to skip because a different file already uses that name."""
    path = folder / f"{name}.mp3"
    if not path.exists():
        return path
    if video_id in archive or settings["onExisting"] == "skip":
        return None
    number = 2
    while (folder / f"{name} ({number}).mp3").exists():
        number += 1
    return folder / f"{name} ({number}).mp3"


def run_worker():
    import yt_dlp
    from yt_dlp.postprocessor.common import PostProcessor

    job = read_job()
    job["pid"] = os.getpid()
    settings = job["settings"]
    folder = Path(job["folder"])
    folder.mkdir(parents=True, exist_ok=True)
    archive = read_archive(folder)
    last_write = 0.0

    def save(force=False):
        nonlocal last_write
        if force or time.monotonic() - last_write > 0.5:
            write_json_atomic(JOB_FILE, job)
            last_write = time.monotonic()

    def check_cancel():
        if CANCEL_FILE.exists():
            raise Cancelled()

    class SetTags(PostProcessor):
        """Replace YouTube's metadata with our artist/title guess before tagging the MP3."""

        def __init__(self, tags):
            super().__init__()
            self.tags = tags

        def run(self, info):
            info.update(self.tags)
            return [], info

    log.info("Worker started: %d items -> %s", len(job["items"]), folder)
    save(force=True)
    try:
        for item in job["items"]:
            check_cancel()
            if item.get("unavailable"):
                item["status"] = "skipped"
                item["error"] = "Video is private or deleted"
                save(force=True)
                continue

            name = naming.build_filename(item, settings)
            target = unique_path(folder, name, settings, item["id"], archive)
            if target is None:
                item["status"] = "skipped"
                item["error"] = "Already downloaded"
                save(force=True)
                continue

            item["status"] = "downloading"
            item["filename"] = target.name
            save(force=True)

            def on_progress(d, item=item):
                check_cancel()
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        item["percent"] = round(d.get("downloaded_bytes", 0) * 100 / total)
                    save()

            def on_postprocess(d, item=item):
                if d["status"] == "started" and d.get("postprocessor") == "ExtractAudio":
                    item["status"] = "converting"
                    item["percent"] = 100
                    save(force=True)

            artist, title = naming.split_artist_title(item["title"], item.get("channel", ""), settings["cleanJunk"])
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                               "preferredquality": str(settings["quality"])}]
            if settings["embedMetadata"]:
                postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
            if settings["embedThumbnail"]:
                postprocessors.insert(0, {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"})
                postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

            stem = str(target.with_suffix("")).replace("%", "%%")
            options = {
                **base_ydl_options(),
                "format": "bestaudio/best",
                "outtmpl": {"default": stem + ".%(ext)s"},
                "noplaylist": True,
                "writethumbnail": settings["embedThumbnail"],
                "postprocessors": postprocessors,
                "progress_hooks": [on_progress],
                "postprocessor_hooks": [on_postprocess],
            }
            tags = {"track": title, "artist": artist, "artists": [artist],
                    "album": job.get("playlist") or None, "track_number": item.get("index") if job.get("playlist") else None,
                    "description": None, "synopsis": None}
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.add_post_processor(SetTags(tags), when="pre_process")
                    ydl.download([item["url"]])
                item["status"] = "done"
                with open(folder / ARCHIVE_NAME, "a", encoding="utf-8") as fh:
                    fh.write(item["id"] + "\n")
                archive.add(item["id"])
            except Cancelled:
                raise
            except Exception as err:
                if isinstance(err.__context__, Cancelled) or CANCEL_FILE.exists():
                    raise Cancelled() from err
                log.error("Item %s failed:\n%s", item["id"], traceback.format_exc())
                item["status"] = "error"
                item["error"] = friendly_error(err)
            save(force=True)
        job["state"] = "done"
    except Cancelled:
        for item in job["items"]:
            if item["status"] in ("queued", "downloading", "converting"):
                item["status"] = "cancelled"
        job["state"] = "cancelled"
        for leftover in folder.glob("*.part"):
            leftover.unlink(missing_ok=True)
    except Exception as err:
        log.error("Worker crashed:\n%s", traceback.format_exc())
        job["state"] = "error"
        job["error"] = friendly_error(err)
    finally:
        job["finished"] = time.time()
        save(force=True)
        CANCEL_FILE.unlink(missing_ok=True)
        log.info("Worker finished: %s", job["state"])


if __name__ == "__main__":
    if "--worker" in sys.argv:
        run_worker()
    else:
        serve()
