"""File naming for Cat'sTube2Mp3: guess artist/title, clean junk, build safe names."""
import re

# Words that mark a bracketed part of a title as noise, e.g. "(Official Video)".
_JUNK_WORDS = r"official|lyrics?|lyric video|audio|video|visuali[sz]er|music video|m/?v|hd|hq|4k|full song"
_JUNK_BRACKETS = re.compile(
    r"\s*[\(\[]\s*(?:[^\)\]]*\b(?:" + _JUNK_WORDS + r")\b[^\)\]]*)[\)\]]",
    re.IGNORECASE,
)
_SEPARATORS = (" - ", " – ", " — ", " ~ ", " | ")
_CHANNEL_SUFFIXES = re.compile(r"(\s*-\s*topic|\s*vevo|\s*official|\s*music)$", re.IGNORECASE)

_WINDOWS_BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
MAX_NAME_LENGTH = 150

TOKENS = ("title", "artist", "track", "playlist", "channel", "date", "id")


def clean_title(title):
    """Remove noise like "(Official Video)" or "[Lyrics]" from a title."""
    cleaned = _JUNK_BRACKETS.sub("", title)
    return re.sub(r"\s{2,}", " ", cleaned).strip(" -–—|") or title.strip()


def clean_channel(channel):
    """Turn "Artist - Topic" or "ArtistVEVO" into "Artist"."""
    name = (channel or "").strip()
    while True:
        shorter = _CHANNEL_SUFFIXES.sub("", name).strip()
        if shorter == name or not shorter:
            return name
        name = shorter


def split_artist_title(title, channel, clean=True):
    """Guess (artist, title) from a YouTube title like "Artist - Song", else use the channel."""
    text = clean_title(title) if clean else title.strip()
    for sep in _SEPARATORS:
        if sep in text:
            artist, song = text.split(sep, 1)
            if artist.strip() and song.strip():
                return artist.strip(), song.strip()
    return clean_channel(channel) or "Unknown Artist", text


def sanitize_component(text):
    """Make text safe to use as a single file or folder name on Windows and Linux."""
    text = _WINDOWS_BAD_CHARS.sub(lambda m: "-" if m.group() in "/\\|" else "", str(text))
    text = re.sub(r"\s{2,}", " ", text).strip().rstrip(". ")
    if text.upper().split(".")[0] in _WINDOWS_RESERVED:
        text = "_" + text
    return text[:MAX_NAME_LENGTH].rstrip(". ")


def render(pattern, values):
    """Fill {tokens} in pattern; unknown tokens are left as typed."""
    def replace(match):
        key = match.group(1).lower()
        return sanitize_component(values.get(key, "")) if key in TOKENS else match.group(0)
    return re.sub(r"\{(\w+)\}", replace, pattern)


def track_values(entry, settings):
    """Token values for one song. entry: title, channel, id, index, total, playlist, date."""
    artist, title = split_artist_title(entry.get("title", ""), entry.get("channel", ""), settings.get("cleanJunk", True))
    total = entry.get("total") or 1
    width = max(2, len(str(total)))
    return {
        "title": title,
        "artist": artist,
        "track": str(entry.get("index") or 1).zfill(width),
        "playlist": entry.get("playlist", ""),
        "channel": entry.get("channel", ""),
        "date": entry.get("date", ""),
        "id": entry.get("id", ""),
    }


def build_filename(entry, settings):
    """File name without extension, e.g. "Artist - Song"."""
    values = track_values(entry, settings)
    name = sanitize_component(render(settings.get("namePattern") or "{artist} - {title}", values))
    return name or sanitize_component(values["title"]) or values["id"] or "track"


def build_subfolder(playlist, channel, settings):
    """Relative folder parts from the subfolder pattern, e.g. ["My Playlist"]."""
    pattern = settings.get("subfolderPattern", "{playlist}")
    values = {"playlist": playlist, "channel": channel}
    parts = re.split(r"[\\/]+", render(pattern, values))
    return [p for p in (sanitize_component(part) for part in parts) if p]
