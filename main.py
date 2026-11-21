#!/usr/bin/env python3
"""The Poster for a Place That Isn't There.

Renders, in pure-stdlib Python, a vintage travel poster for VELMARA, an
invented island where two suns set: a lighthouse on a rocky headland, twin
suns over layered mountains, a sunlit sea, and the place name set large in
a cream title band. No network, no third-party libraries, no randomness,
no timestamps: the output is fully deterministic. Writes entry.png to
$MAKEFUN_OUTPUT_DIR (or /output, or the current directory when neither
exists).
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# 5x7 bitmap font (uppercase, digits, punctuation). '#' = ink, '.' = empty.
# ---------------------------------------------------------------------------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}

CHAR_W, CHAR_H = 5, 7


def text_mask(text, spacing=1):
    """Render text to a 1-bit mask (bytes, 1 = ink). Unknown chars -> space."""
    n = len(text)
    w = n * (CHAR_W + spacing) - spacing if n else 0
    mask = bytearray(w * CHAR_H)
    for i, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[' '])
        ox = i * (CHAR_W + spacing)
        for row in range(CHAR_H):
            bits = glyph[row]
            for col in range(CHAR_W):
                if bits[col] == '1':
                    mask[row * w + ox + col] = 1
    return mask, w, CHAR_H


def text_width(text, scale, spacing=1):
    if not text:
        return 0
    return int(round((len(text) * (CHAR_W + spacing) - spacing) * scale))


# ---------------------------------------------------------------------------
# Canvas: RGB buffer with drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def blend_px(self, x, y, color, alpha):
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0:
            i = self._idx(x, y)
            if alpha >= 1:
                self.px[i], self.px[i + 1], self.px[i + 2] = color
            else:
                for c in range(3):
                    self.px[i + c] = int(round(
                        self.px[i + c] * (1 - alpha) + color[c] * alpha))

    def fill_rect(self, x, y, w, h, color, alpha=1.0):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.blend_px(xx, yy, color, alpha)

    def rect(self, x, y, w, h, color, t=1, alpha=1.0):
        for k in range(t):
            self.hline(x + k, y + k, x + w - k, color, alpha)
            self.hline(x + k, y + h - 1 - k, x + w - k, color, alpha)
            self.vline(x + k, y, y + h, color, alpha)
            self.vline(x + w - 1 - k, y, y + h, color, alpha)

    def hline(self, x0, y, x1, color, alpha=1.0):
        if x0 > x1:
            x0, x1 = x1, x0
        for x in range(max(0, x0), min(self.w, x1)):
            self.blend_px(x, y, color, alpha)

    def vline(self, x, y0, y1, color, alpha=1.0):
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(max(0, y0), min(self.h, y1)):
            self.blend_px(x, y, color, alpha)

    def line(self, x0, y0, x1, y1, color, alpha=1.0):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.blend_px(x, y, color, alpha)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=False, alpha=1.0):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.blend_px(xx, yy, color, alpha)
                else:
                    if abs(d2 - r * r) <= r:
                        self.blend_px(xx, yy, color, alpha)

    def ellipse(self, cx, cy, rx, ry, color, fill=False, alpha=1.0):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                v = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
                if fill:
                    if v <= 1.0:
                        self.blend_px(xx, yy, color, alpha)
                else:
                    if abs(v - 1.0) <= 0.06:
                        self.blend_px(xx, yy, color, alpha)

    def polygon(self, points, color, alpha=1.0):
        """Scanline fill of a simple polygon."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.blend_px(x, y, color, alpha)

    def blit_mask(self, mask, mw, mh, x, y, scale, color, alpha=1.0):
        sw = int(round(mw * scale))
        sh = int(round(mh * scale))
        for dy in range(sh):
            sy = min(mh - 1, int(dy / scale))
            for dx in range(sw):
                sx = min(mw - 1, int(dx / scale))
                if mask[sy * mw + sx]:
                    self.blend_px(x + dx, y + dy, color, alpha)

    def text(self, x, y, s, scale, color, spacing=1, alpha=1.0):
        mask, mw, mh = text_mask(s, spacing)
        self.blit_mask(mask, mw, mh, x, y, scale, color, alpha)
        return x + int(round(mw * scale))

    def text_centered(self, cx, y, s, scale, color, spacing=1, alpha=1.0):
        w = text_width(s, scale, spacing)
        self.text(cx - w // 2, y, s, scale, color, spacing, alpha)


# ---------------------------------------------------------------------------
# Minimal PNG encoder (stdlib only): 8-bit RGB, filter 0, zlib level 9.
# ---------------------------------------------------------------------------
def encode_png(canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
CREAM = (246, 239, 224)       # poster border and title band
NAVY = (30, 34, 68)           # title ink
NAVY_SOFT = (74, 76, 110)
GOLD = (214, 164, 74)
RED = (178, 62, 52)
SEA_TOP = (38, 96, 116)
SEA_BOT = (18, 52, 78)
RIDGE_FAR = (96, 66, 112)
RIDGE_MID = (66, 50, 92)
CLIFF = (38, 34, 64)
TOWER = (240, 234, 218)
LAMP = (52, 44, 66)
SUN_BIG = (255, 208, 122)
SUN_SMALL = (255, 236, 190)
GLINT = (255, 190, 110)

W, H = 1024, 1024
BORDER = 28                    # cream frame around the picture
PIC_Y0, PIC_Y1 = BORDER, 820   # picture area (title band below it)
PIC_X0, PIC_X1 = BORDER, W - BORDER
HORIZON = 600                  # sea line

# Sunset sky as a list of (y_fraction, colour) stops.
SKY_STOPS = [
    (0.00, (38, 30, 82)),
    (0.28, (84, 48, 108)),
    (0.52, (178, 78, 104)),
    (0.74, (232, 132, 88)),
    (1.00, (252, 200, 116)),
]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def sky_color(frac):
    """Colour of the sky gradient at fraction 0 (top) .. 1 (horizon)."""
    for i in range(len(SKY_STOPS) - 1):
        f0, c0 = SKY_STOPS[i]
        f1, c1 = SKY_STOPS[i + 1]
        if f0 <= frac <= f1:
            return lerp(c0, c1, (frac - f0) / (f1 - f0))
    return SKY_STOPS[-1][1]


def star_points(cx, cy, r_out, r_in, rot=-90):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36)
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts


def ridge(c, peaks, base_y, color):
    """A mountain ridge: peaks is a list of (x, y) summits; the polygon
    runs along the summits down to base_y across the picture width."""
    pts = [(PIC_X0, base_y)] + list(peaks) + [(PIC_X1, base_y)]
    c.polygon(pts, color)


def sun_glow(c, cx, cy, r, color):
    """Soft halo: concentric rings fading out from the sun's edge."""
    for k in range(1, 5):
        c.circle(cx, cy, r + k * 10, color, fill=False,
                 alpha=0.10 * (1 - k / 5.0))


def bird(c, cx, cy, size, color):
    """A distant seabird: two short rising strokes."""
    c.line(cx - size, cy, cx, cy - size // 2, color)
    c.line(cx, cy - size // 2, cx + size, cy, color)


def sailboat(c, x, y, scale, hull, sail):
    """A small sailboat on the sea, drawn at (x, y) = waterline."""
    s = scale
    # hull
    c.polygon([(x - 16 * s, y), (x + 16 * s, y),
               (x + 10 * s, y + 6 * s), (x - 10 * s, y + 6 * s)], hull)
    # mast
    c.vline(x, y - 26 * s, y, hull)
    # mainsail (right of the mast) and jib (left)
    c.polygon([(x + 2 * s, y - 24 * s), (x + 2 * s, y - 2 * s),
               (x + 15 * s, y - 2 * s)], sail)
    c.polygon([(x - 2 * s, y - 22 * s), (x - 2 * s, y - 2 * s),
               (x - 12 * s, y - 2 * s)], sail)


def lighthouse(c):
    """The landmark: a red-banded lighthouse on the headland, its beam
    sweeping right across the dusk sky."""
    # headland rock the tower stands on
    c.polygon([(PIC_X0, 700), (120, 648), (200, 628), (268, 644),
               (330, 690), (372, 742), (372, PIC_Y1), (PIC_X0, PIC_Y1)],
              CLIFF)
    # pale rock highlight along the cliff top
    c.polygon([(PIC_X0, 700), (120, 648), (200, 628), (268, 644),
               (330, 690), (330, 706), (200, 656), (120, 672),
               (PIC_X0, 716)], (58, 54, 88))
    # light beam: a translucent wedge from the lamp room, tapering as it
    # fades into the dusk; drawn in two nested wedges so its far edge
    # softens instead of cutting a hard rectangle across the sky
    c.polygon([(216, 508), (700, 458), (700, 546)],
              (255, 232, 170), alpha=0.10)
    c.polygon([(216, 508), (640, 470), (640, 538)],
              (255, 232, 170), alpha=0.12)
    # tower: tapered, white with two red bands
    c.polygon([(186, 640), (196, 524), (236, 524), (246, 640)], TOWER)
    c.polygon([(190, 596), (193, 566), (239, 566), (242, 596)], RED)
    c.polygon([(194, 552), (196, 530), (236, 530), (238, 552)], RED)
    # gallery rail and lamp room
    c.fill_rect(188, 516, 56, 8, LAMP)
    c.fill_rect(196, 492, 40, 24, LAMP)
    c.fill_rect(202, 498, 28, 12, (255, 226, 140))
    c.polygon([(192, 492), (240, 492), (216, 476)], LAMP)
    # tower outline, thin and dark, so it reads against the sky
    c.line(186, 640, 196, 524, NAVY)
    c.line(246, 640, 236, 524, NAVY)


def render():
    c = Canvas(W, H, CREAM)

    # --- sky gradient ---
    sky_h = HORIZON - PIC_Y0
    for yy in range(PIC_Y0, HORIZON):
        col = sky_color((yy - PIC_Y0) / sky_h)
        c.hline(PIC_X0, yy, PIC_X1, col)

    # --- stars in the upper sky (fixed-seed LCG, deterministic) ---
    seed = 1234567

    def lcg():
        nonlocal seed
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        return seed

    for _ in range(46):
        sx = PIC_X0 + 20 + lcg() % (PIC_X1 - PIC_X0 - 40)
        sy = PIC_Y0 + 14 + lcg() % 240
        r = 1 + lcg() % 2
        a = 0.35 + (lcg() % 50) / 100.0
        c.circle(sx, sy, r, (255, 240, 210), fill=True, alpha=min(a, 0.85))

    # --- the two suns of Velmara ---
    sun_glow(c, 330, 252, 40, SUN_SMALL)
    c.circle(330, 252, 40, SUN_SMALL, fill=True)
    c.circle(330, 252, 32, (255, 246, 214), fill=True)
    sun_glow(c, 700, 472, 76, SUN_BIG)
    c.circle(700, 472, 76, SUN_BIG, fill=True)
    c.circle(700, 472, 60, (255, 226, 150), fill=True)

    # --- birds ---
    for bx, by, bs in [(540, 180, 12), (590, 210, 10), (628, 168, 9),
                       (830, 300, 11), (872, 330, 9), (470, 300, 8),
                       (700, 150, 9), (760, 190, 8), (120, 200, 10)]:
        bird(c, bx, by, bs, (44, 36, 66))

    # --- thin dusk clouds, soft ellipses low over the mountains ---
    for ccx, ccy, crx, cry, ca in [(620, 400, 90, 10, 0.20),
                                   (880, 380, 70, 8, 0.16),
                                   (180, 420, 80, 9, 0.18)]:
        c.ellipse(ccx, ccy, crx, cry, (255, 178, 138), fill=True, alpha=ca)

    # --- mountain ridges, far to near ---
    ridge(c, [(PIC_X0, 560), (140, 520), (260, 556), (420, 500),
              (560, 548), (700, 512), (850, 552), (PIC_X1, 528)],
          HORIZON, RIDGE_FAR)
    ridge(c, [(PIC_X0, 580), (180, 548), (330, 572), (520, 540),
              (660, 566), (820, 542), (PIC_X1, 570)],
          HORIZON, RIDGE_MID)
    # snow caps on the two highest far peaks
    c.polygon([(420, 500), (396, 524), (412, 522), (420, 532),
               (430, 520), (444, 524)], (250, 240, 226))
    c.polygon([(140, 520), (124, 536), (136, 534), (142, 542),
               (150, 534), (158, 538)], (250, 240, 226))

    # --- sea ---
    sea_h = PIC_Y1 - HORIZON
    for yy in range(HORIZON, PIC_Y1):
        t = (yy - HORIZON) / sea_h
        c.hline(PIC_X0, yy, PIC_X1, lerp(SEA_TOP, SEA_BOT, t))

    # sun reflection: a glittering path under the big sun
    for yy in range(HORIZON + 6, PIC_Y1 - 8, 7):
        depth = (yy - HORIZON) / sea_h
        half = int(18 + depth * 66)
        # dashes drift slightly with depth; deterministic via sine
        drift = int(10 * math.sin(yy / 23.0))
        x0 = 700 - half + drift
        x1 = 700 + half + drift
        c.hline(x0, yy, x1, GLINT, alpha=0.55 - depth * 0.25)
        c.hline(x0 + 14, yy + 3, x1 - 20, GLINT, alpha=0.30)

    # faint wave strokes across the sea
    for wy in range(HORIZON + 26, PIC_Y1 - 12, 34):
        for wx in range(PIC_X0 + 30, PIC_X1 - 30, 97):
            off = int(12 * math.sin(wx / 61.0 + wy))
            c.hline(wx + off, wy, wx + off + 34, (190, 220, 228),
                    alpha=0.22)

    # --- sailboats ---
    sailboat(c, 800, 700, 2, (24, 30, 52), (248, 242, 226))
    sailboat(c, 520, 668, 1, (24, 30, 52), (248, 242, 226))

    # --- lighthouse headland (foreground, left) ---
    lighthouse(c)

    # --- picture frame: thin navy rule around the image ---
    c.rect(PIC_X0, PIC_Y0, PIC_X1 - PIC_X0, PIC_Y1 - PIC_Y0, NAVY, t=2)

    # --- title band ---
    c.hline(PIC_X0, PIC_Y1 + 2, PIC_X1, NAVY)
    c.hline(PIC_X0, PIC_Y1 + 6, PIC_X1, GOLD)
    # small stars flanking the title
    c.polygon(star_points(512 - 330, 890, 12, 5), GOLD)
    c.polygon(star_points(512 + 330, 890, 12, 5), GOLD)
    # place name, with a soft shadow so it sits on the band
    c.text_centered(512 + 3, 853, "VELMARA", 12, (222, 210, 182))
    c.text_centered(512, 850, "VELMARA", 12, NAVY)
    # tagline
    c.text_centered(512, 952, "WHERE TWO SUNS SET", 2.2, NAVY_SOFT,
                    spacing=3)
    c.hline(PIC_X0, 990, PIC_X1, NAVY)

    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        out_dir = "."
    path = os.path.join(out_dir, "entry.png")
    png = encode_png(render())
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
