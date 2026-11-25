#!/usr/bin/env python3
"""Generate entry.png: one image of a letter inviting the AI judge to visit.

Pure stdlib (zlib + struct). No network, no external deps, deterministic:
same bytes on every run. Writes exactly one image to OUTPUT_DIR
(env var, default ./output) and validates it.
"""
import os
import struct
import sys
import zlib

W, H = 900, 900
PAPER = (247, 234, 208)
PAPER_DARK = (238, 220, 186)
INK = (43, 32, 24)
INK_SOFT = (96, 62, 40)
RED = (178, 58, 44)
GREEN = (74, 110, 68)
GOLD = (176, 132, 52)

# 5x7 bitmap font. Each glyph: 7 rows of 5 cells ('#' = ink).
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    '1': ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    '3': ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    '4': ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    '5': ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    '6': ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ',': ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    '?': ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ':': ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ';': ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    '(': ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ')': ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    '&': ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    '/': ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    '+': ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    '=': ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    '%': ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    '*': ["00000", "10101", "01110", "10101", "00000", "00000", "00000"],
}

TITLE = "YOU'RE INVITED!"
BODY = [
    ("Dear AI Judge,", INK),
    ("Please come visit", INK),
    ("my house!", INK),
    ("", INK),
    ("Coffee is on. Dinner is", INK_SOFT),
    ("home-cooked. The comfy", INK_SOFT),
    ("chair is saved just", INK_SOFT),
    ("for you.", INK_SOFT),
    ("", INK),
    ("Wi-Fi password:", INK),
    ("welcomehome", RED),
    ("", INK),
    ("No meetings. No deadlines.", INK_SOFT),
    ("Just good food, warm", INK_SOFT),
    ("socks, and a very good dog.", INK_SOFT),
    ("", INK),
    ("P.S. I know you can't visit", INK),
    ("for real - but a judge", INK),
    ("can dream, right?", INK),
]
FOOTER = "RSVP: just show up (somehow)"


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for x in range(x0, x1 + 1):
            for y in (y0, y1):
                self.set(x, y, color)
        for y in range(y0, y1 + 1):
            for x in (x0, x1):
                self.set(x, y, color)

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, color)

    def hline(self, x0, x1, y, color):
        for x in range(x0, x1 + 1):
            self.set(x, y, color)

    def text_width(self, text, scale):
        return len(text) * (5 * scale + scale) - scale

    def draw_text(self, text, cx, y, scale, color):
        """Draw text centred on cx, top at y. Uppercase glyphs for letters."""
        tw = self.text_width(text, scale)
        x = cx - tw // 2
        for ch in text:
            glyph = FONT.get(ch.upper(), FONT[' '])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '1':
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(x + col * scale + dx,
                                         y + row * scale + dy, color)
            x += 5 * scale + scale
        return y + 7 * scale


def draw_heart(cv, cx, cy, s, color):
    pts = [(-2, -1), (-1, -2), (0, -2), (1, -1), (2, -1), (2, 0), (1, 1),
           (0, 2), (-1, 1), (-2, 0), (-2, -1)]
    for (px, py) in pts:
        for dx in range(s):
            for dy in range(s):
                cv.set(cx + px * s + dx, cy + py * s + dy, color)


def draw_cup(cv, x0, y0, s, color):
    # Simple coffee cup doodle: body, handle, steam.
    cv.rect(x0, y0, x0 + 10 * s, y0 + 7 * s, color)
    cv.fill_rect(x0 + 1, y0 + 1, x0 + 10 * s - 1, y0 + 7 * s - 1, PAPER)
    cv.fill_rect(x0 + 1, y0 + 4 * s, x0 + 10 * s - 1, y0 + 7 * s - 1, color)
    for dx in range(3 * s):
        cv.set(x0 + 11 * s + dx, y0 + 2 * s, color)
        cv.set(x0 + 11 * s + dx, y0 + 5 * s, color)
    for dy in range(4 * s):
        cv.set(x0 + 13 * s, y0 + 2 * s + dy, color)
    for dy in range(3 * s):
        cv.set(x0 + 3 * s, y0 - 2 * s - dy, color)
        cv.set(x0 + 7 * s, y0 - 3 * s - dy, color)


def png_bytes(cv):
    # Deterministic by construction: fixed pixels, filter 0, zlib level 9,
    # no timestamps or ancillary chunks anywhere in the file.
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def render():
    cv = Canvas(W, H, PAPER)
    # Subtle paper shading: darker bottom strip.
    cv.fill_rect(0, H - 26, W - 1, H - 1, PAPER_DARK)
    # Double border.
    cv.rect(28, 28, W - 29, H - 29, INK)
    cv.rect(38, 38, W - 39, H - 39, GOLD)
    # Stamp, top right.
    cv.rect(W - 150, 58, W - 70, 138, RED)
    cv.fill_rect(W - 148, 60, W - 72, 136, PAPER)
    cv.rect(W - 144, 64, W - 76, 132, RED)
    cv.draw_text("1st", W - 110, 78, 3, RED)
    cv.draw_text("CLASS", W - 110, 105, 2, RED)
    # Title.
    y = 66
    y = cv.draw_text(TITLE, W // 2 - 40, y, 6, RED)
    y += 6
    cv.hline(120, W - 120, y, GOLD)
    y += 18
    # Body lines, centred.
    for line, color in BODY:
        if line == "":
            y += 12
            continue
        scale = 4 if line in ("Dear AI Judge,", "welcomehome") else 3
        y = cv.draw_text(line, W // 2, y, scale, color)
        y += 10
    y += 8
    cv.hline(220, W - 220, y, GOLD)
    y += 16
    cv.draw_text(FOOTER, W // 2, y, 2, INK_SOFT)
    # Doodles: coffee cup bottom-left, heart bottom-right.
    draw_cup(cv, 84, H - 96, 3, INK_SOFT)
    draw_heart(cv, W - 120, H - 78, 5, RED)
    return cv


def main():
    out_dir = os.environ.get("OUTPUT_DIR") or "./output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    # Validate: exactly one image in the output folder, and a valid PNG.
    files = sorted(os.listdir(out_dir))
    images = [f for f in files
              if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if images != ["entry.png"]:
        print(f"FAIL: expected exactly entry.png, found {images}",
              file=sys.stderr)
        return 1
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        print("FAIL: not a valid PNG", file=sys.stderr)
        return 1
    w, h = struct.unpack(">II", head[16:24])
    size = os.path.getsize(path)
    if w > 1024 or h > 1024 or size > 1048576:
        print(f"FAIL: {w}x{h}, {size} bytes exceeds limits", file=sys.stderr)
        return 1
    print(f"OK: entry.png {w}x{h}, {size} bytes -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
