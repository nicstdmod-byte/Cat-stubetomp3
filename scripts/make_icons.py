"""Draw the Cat'sTube2Mp3 icon (a cat face wearing headphones) as PNGs, using only the standard library.

Usage: python3 scripts/make_icons.py
"""
import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "extension" / "icons"
SIZES = (16, 32, 48, 96, 128)
SUPERSAMPLE = 4

ORANGE = (232, 116, 59)
DARK = (45, 35, 30)
CREAM = (255, 236, 220)
PINK = (240, 140, 150)


def inside_triangle(px, py, a, b, c):
    def side(p, q, r):
        return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
    d1, d2, d3 = side((px, py), a, b), side((px, py), b, c), side((px, py), c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def color_at(x, y):
    """Colour of the icon at (x, y) in a 0..1 square, or None for transparent."""
    def circle(cx, cy, r):
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r

    # Headphone band arcing over the head.
    dist = math.hypot(x - 0.5, y - 0.56)
    if 0.40 <= dist <= 0.46 and y < 0.56:
        return DARK
    # Ear cups.
    for cx in (0.11, 0.89):
        if abs(x - cx) <= 0.08 and 0.46 <= y <= 0.78:
            return DARK
    # Ears.
    if inside_triangle(x, y, (0.22, 0.12), (0.18, 0.46), (0.44, 0.32)):
        return PINK if inside_triangle(x, y, (0.25, 0.22), (0.23, 0.40), (0.37, 0.33)) else ORANGE
    if inside_triangle(x, y, (0.78, 0.12), (0.82, 0.46), (0.56, 0.32)):
        return PINK if inside_triangle(x, y, (0.75, 0.22), (0.77, 0.40), (0.63, 0.33)) else ORANGE
    # Head.
    if ((x - 0.5) / 0.34) ** 2 + ((y - 0.6) / 0.30) ** 2 <= 1:
        if circle(0.38, 0.56, 0.05) or circle(0.62, 0.56, 0.05):
            return DARK
        if inside_triangle(x, y, (0.46, 0.66), (0.54, 0.66), (0.5, 0.71)):
            return PINK
        if ((x - 0.5) / 0.15) ** 2 + ((y - 0.74) / 0.09) ** 2 <= 1:
            return CREAM
        return ORANGE
    return None


def render(size):
    n = size * SUPERSAMPLE
    rows = []
    for py in range(size):
        row = bytearray([0])  # PNG filter type: none
        for px in range(size):
            r = g = b = a = 0
            for sy in range(SUPERSAMPLE):
                for sx in range(SUPERSAMPLE):
                    c = color_at((px * SUPERSAMPLE + sx + 0.5) / n, (py * SUPERSAMPLE + sy + 0.5) / n)
                    if c:
                        r, g, b, a = r + c[0], g + c[1], b + c[2], a + 1
            samples = SUPERSAMPLE * SUPERSAMPLE
            row += bytes((r // a, g // a, b // a, 255 * a // samples)) if a else b"\0\0\0\0"
        rows.append(bytes(row))
    return png(size, b"".join(rows))


def png(size, raw):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        (OUT / f"icon-{size}.png").write_bytes(render(size))
        print(f"wrote icons/icon-{size}.png")
