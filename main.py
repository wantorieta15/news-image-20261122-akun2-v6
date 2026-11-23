#!/usr/bin/env python3
"""news-image-20261122 v6 - Akun 2 (@wantorieta15).
One-page newspaper: Sunday 22 November 2026, 36 stories, 7 regions.
Pure stdlib (zlib + struct PNG). 1024x1024.
Design: back to the proven v4 family, incremental fixes only -
cleaner, heavier bitmap font, one-line number labels, no overlaps.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM   = (250, 244, 230)   # page
PAPER   = (253, 248, 236)   # card paper
INK     = (26, 26, 26)
GREY    = (90, 86, 78)
LGREY   = (200, 192, 176)
NAVY    = (31, 42, 68)     # top strip
TEAL    = (18, 77, 70)     # timeline strip
RED     = (192, 57, 43)    # headline red
DRED    = (158, 32, 24)
YELLOW  = (245, 203, 66)
WHITE   = (255, 255, 255)
BLACK   = (10, 10, 14)
NIGHT   = (11, 16, 38)     # ukraine sky
SKY     = (191, 227, 240)  # antalya sky
SUNSET  = (245, 158, 11)
SEA     = (29, 78, 216)
GREEN   = (21, 128, 61)    # confirmed
BLUE    = (29, 78, 216)    # reported
ORANGE  = (194, 65, 12)    # claim
STONE   = (87, 83, 78)     # pending
BORDER  = (60, 56, 48)

# region bar colours
C_EU  = (37, 99, 235)
C_ME  = (220, 38, 38)
C_AP  = (234, 123, 30)
C_AF  = (217, 164, 4)
C_AM  = (22, 163, 74)
C_OC  = (13, 148, 136)
C_WO  = (51, 65, 85)

# ---------------------------------------------------------------- canvas
canvas = bytearray(W * H * 3)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = c[0]
        canvas[i + 1] = c[1]
        canvas[i + 2] = c[2]


def fill(x, y, w, h, c):
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        s = (yy * W + x0) * 3
        canvas[s:s + len(row)] = row


def hline(x, y, w, c):
    fill(x, y, w, 1, c)


def vline(x, y, h, c):
    fill(x, y, 1, h, c)


def box(x, y, w, h, c, t=1):
    fill(x, y, w, t, c)
    fill(x, y + h - t, w, t, c)
    fill(x, y, t, h, c)
    fill(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int(math.isqrt(r * r - dy * dy))
        fill(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def circle_outline(cx, cy, r, c):
    x = 0
    y = r
    d = 3 - 2 * r
    while y >= x:
        for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                       (cx + x, cy - y), (cx - x, cy - y),
                       (cx + y, cy + x), (cx - y, cy + x),
                       (cx + y, cy - x), (cx - y, cy - x)):
            put(px, py, c)
        x += 1
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6


def poly(points, c):
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = points[i]
            x1, yy1 = points[(i + 1) % n]
            if yy0 == yy1:
                continue
            if min(yy0, yy1) <= y < max(yy0, yy1):
                t = (y - yy0) / (yy1 - yy0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = int(xs[k])
            xb = int(xs[k + 1])
            fill(xa, y, xb - xa + 1, 1, c)


# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, hand-drawn for this build: heavier, consistent strokes.
# '#' = on, '.' = off. Rows top to bottom.
FONT = {
'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
'c': (".....", ".....", ".###.", "#....", "#....", "#...#", ".###."),
'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
'f': ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
'g': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
'j': ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
'y': (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
'0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
'1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
'2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
'3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
'4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
'5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
'6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
'7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
'8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
'9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
'.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
',': (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
';': (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
"'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
'"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
'!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
'?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
'-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
'\u2014': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
'\u00b7': (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
'(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
'/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
'%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
'&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
'+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
'=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
'*': (".....", "..#..", "#.#.#", ".###.", "#.#.#", "..#..", "....."),
'#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
'_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
'@': (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
'$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
'[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
'~': (".....", ".....", ".#..#", "#.#.#", ".....", ".....", "....."),
'<': ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
'>': (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
}


def gap_of(scale):
    return max(1, scale // 2)


def text_w(s, scale=1, bold=False):
    if not s:
        return 0
    w = len(s) * (5 * scale + gap_of(scale)) - gap_of(scale)
    if bold:
        w += 1 if scale <= 2 else 2
    return w


def draw_text(x, y, s, scale=1, color=INK, bold=False, align='left'):
    if align == 'center':
        x -= text_w(s, scale, bold) // 2
    elif align == 'right':
        x -= text_w(s, scale, bold)
    gap = gap_of(scale)
    adv = 5 * scale + gap
    bdx = 1 if scale <= 2 else 2
    cx = x
    for ch in s:
        rows = FONT.get(ch, FONT['?'])
        for r, row in enumerate(rows):
            for cc in range(5):
                if row[cc] == '#':
                    px0 = cx + cc * scale
                    py0 = y + r * scale
                    fill(px0, py0, scale, scale, color)
                    if bold:
                        fill(px0 + bdx, py0, scale, scale, color)
        cx += adv
    return x + text_w(s, scale, bold)


def wrap_text(s, max_w, scale=1, bold=False):
    lines = []
    cur = ''
    for wd in s.split(' '):
        trial = wd if not cur else cur + ' ' + wd
        if text_w(trial, scale, bold) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def chip(x, y, label, bg, fg=WHITE, scale=1):
    w = text_w(label, scale, True) + 10
    h = 7 * scale + 6
    fill(x, y, w, h, bg)
    draw_text(x + 5, y + 3, label, scale, fg, True)
    return w


def num_badge(cx, cy, n, r=9):
    disc(cx, cy, r, WHITE)
    circle_outline(cx, cy, r, INK)
    s = str(n)
    draw_text(cx, cy - 3, s, 1, INK, True, align='center')


# ---------------------------------------------------------------- png output
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += canvas[y * W * 3:(y + 1) * W * 3]

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 6))
            + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)


# ---------------------------------------------------------------- header
def draw_header():
    # top navy strip
    fill(0, 0, W, 20, NAVY)
    draw_text(W // 2, 6, "THE WORLD IN ONE DAY    36 STORIES    7 REGIONS    "
              "EVERY ONE DATED SUNDAY 22 NOVEMBER 2026",
              1, WHITE, True, align='center')
    # title
    draw_text(W // 2, 24, "Sunday 22 November 2026", 7, INK, True,
              align='center')
    # red sub-headline, two lines, centred
    draw_text(W // 2, 78,
              "186 drones over Ukraine in the night \u00b7 COP31's deal "
              "names no fossil fuels \u00b7",
              2, RED, True, align='center')
    draw_text(W // 2, 97, "Iran's radar claim meets Bahrain's denial",
              2, RED, True, align='center')
    # timeline strip
    fill(0, 116, W, 22, TEAL)
    draw_text(8, 123, "THE DAY IN UTC", 1, YELLOW, True)
    tx = 8 + text_w("THE DAY IN UTC", 1, True) + 12
    items = [("01:00", "HK polls open"),
             ("03:00", "COP31 objections"),
             ("05:11", "Hamas seeks talks"),
             ("05:30", "Vegas GP ends"),
             ("06:00", "COP31 approval")]
    for t, label in items:
        tx = draw_text(tx, 123, t, 1, YELLOW, True)
        tx = draw_text(tx + 4, 123, label, 1, WHITE, True)
        tx += 18


NUMBERS = [
    ("186", "drones fired at Ukraine"),
    ("161", "downed or suppressed"),
    ("98.37%", "Hong Kong turnout"),
    ("720/9", "India's Test total in NZ"),
    ("50", "Wembanyama points"),
    ("14", "may be trapped in Dymer"),
]


def draw_numbers():
    draw_text(8, 144, "THE DAY IN NUMBERS", 2, RED, True)
    colw = 170
    for i, (num, label) in enumerate(NUMBERS):
        x = 8 + i * colw
        if i > 0:
            vline(x - 6, 162, 40, LGREY)
        draw_text(x, 162, num, 4, RED, True)
        draw_text(x, 194, label, 1, INK, False)


REGIONS = [
    ("EUROPE 8", C_EU, 200),
    ("MIDDLE EAST 5", C_ME, 150),
    ("ASIA-PACIFIC 7", C_AP, 180),
    ("AFRICA 4", C_AF, 120),
    ("AMERICAS 5", C_AM, 150),
    ("OCEANIA 3", C_OC, 110),
    ("WORLD 4", C_WO, 114),
]


def draw_region_bar():
    x = 0
    for label, col, w in REGIONS:
        fill(x, 206, w, 22, col)
        draw_text(x + w // 2, 211, label, 2, WHITE, True, align='center')
        x += w


# ---------------------------------------------------------------- big cards
BADGE_COL = {"CONFIRMED": GREEN, "REPORTED": BLUE,
             "CLAIM": ORANGE, "PENDING": STONE}


def illus_ukraine(x, y, w, h):
    fill(x, y, w, h, NIGHT)
    # stars
    for sx, sy in ((14, 8), (52, 16), (96, 6), (140, 14), (188, 8),
                   (232, 18), (276, 6), (306, 14), (40, 30), (120, 26),
                   (200, 30), (260, 26), (170, 44), (70, 44), (300, 40)):
        fill(x + sx, y + sy, 2, 2, WHITE)
    # moon (kept clear of the REPORTED badge at top right)
    disc(x + w - 64, y + 30, 10, (240, 236, 210))
    disc(x + w - 68, y + 27, 3, (214, 208, 180))
    # drones: grey dots with short trails
    for dx, dy in ((60, 34), (110, 22), (170, 38), (230, 26), (290, 40)):
        line(x + dx - 12, y + dy + 2, x + dx - 2, y + dy, (120, 124, 140))
        disc(x + dx, y + dy, 3, (150, 154, 168))
    # city skyline with lit windows
    base = y + h
    for bx, bw, bh in ((0, 34, 26), (38, 26, 38), (68, 30, 22),
                       (102, 24, 34), (130, 36, 26), (170, 28, 40),
                       (202, 30, 24), (236, 26, 36), (266, 30, 28),
                       (300, 28, 34)):
        fill(x + bx, base - bh, bw, bh, (24, 28, 52))
        for wy in range(base - bh + 5, base - 4, 8):
            for wx in range(bx + 5, bx + bw - 4, 9):
                fill(x + wx, wy, 2, 3, (245, 203, 66))
    # fires: orange triangles on the ground
    for fx in (48, 150, 248):
        poly([(x + fx, base - 2), (x + fx + 11, base - 2),
              (x + fx + 5, base - 20)], (245, 158, 11))
        poly([(x + fx + 2, base - 2), (x + fx + 9, base - 2),
              (x + fx + 5, base - 13)], (220, 38, 38))


def illus_antalya(x, y, w, h):
    fill(x, y, w, h, SKY)
    disc(x + w - 40, y + 20, 12, (250, 214, 90))
    # parliament building: white block, red roof, columns
    bx, by = x + 16, y + 26
    poly([(bx - 6, by), (bx + 118, by), (bx + 56, by - 18)], (178, 34, 34))
    fill(bx, by, 112, 44, (248, 248, 244))
    fill(bx, by + 44, 112, 5, (210, 205, 190))
    for cx in range(bx + 8, bx + 106, 20):
        fill(cx, by + 6, 7, 36, (226, 222, 210))
    # table with three small flags
    fill(x + 130, y + h - 16, 150, 4, (146, 96, 48))
    fill(x + 136, y + h - 12, 4, 12, (120, 80, 40))
    fill(x + 214, y + h - 12, 4, 12, (120, 80, 40))
    for fx, fc in ((150, (37, 99, 235)), (180, (220, 38, 38)),
                   (210, (22, 163, 74)), (240, (234, 123, 30))):
        fill(x + fx, y + h - 30, 2, 14, (90, 80, 60))
        fill(x + fx + 2, y + h - 30, 14, 9, fc)
    # globe
    gx, gy = x + w - 52, y + 52
    disc(gx, gy, 24, (59, 130, 246))
    disc(gx - 8, gy - 6, 7, (34, 197, 94))
    disc(gx + 7, gy + 8, 6, (34, 197, 94))
    disc(gx + 9, gy - 10, 4, (34, 197, 94))
    circle_outline(gx, gy, 24, (30, 64, 175))
    # clock
    cx, cy = x + w - 118, y + 24
    disc(cx, cy, 13, WHITE)
    circle_outline(cx, cy, 13, INK)
    line(cx, cy, cx, cy - 8, INK)
    line(cx, cy, cx + 6, cy + 3, INK)


def illus_manama(x, y, w, h):
    fill(x, y, w, h, (249, 178, 84))
    fill(x, y + 22, w, 18, (244, 140, 60))
    disc(x + w - 44, y + 26, 15, (250, 214, 90))
    # sea
    fill(x, y + 52, w, h - 52, SEA)
    for wy in (62, 72, 82):
        for wx in range(8, w - 8, 34):
            line(x + wx, y + wy, x + wx + 18, y + wy, (147, 197, 253))
    # radar mast + dish on the left
    line(x + 26, y + 52, x + 26, y + 14, (90, 96, 108))
    line(x + 14, y + 52, x + 26, y + 20, (90, 96, 108))
    line(x + 38, y + 52, x + 26, y + 20, (90, 96, 108))
    poly([(x + 12, y + 12), (x + 40, y + 12), (x + 26, y + 26)],
         (160, 166, 178))
    # ship: red hull, containers, flames
    hx, hy = x + 96, y + 58
    poly([(hx, hy), (hx + 150, hy), (hx + 138, hy + 20),
          (hx + 12, hy + 20)], (178, 34, 34))
    for cx, cc in ((hx + 12, (120, 126, 138)), (hx + 44, (250, 204, 21)),
                   (hx + 76, (34, 197, 94)), (hx + 108, (120, 126, 138))):
        fill(cx, hy - 14, 28, 14, cc)
    for fx in (hx + 22, hx + 88, hx + 128):
        poly([(fx, hy - 14), (fx + 10, hy - 14), (fx + 5, hy - 30)],
             (245, 158, 11))
        poly([(fx + 2, hy - 14), (fx + 8, hy - 14), (fx + 5, hy - 24)],
             (220, 38, 38))


BIG_CARDS = [
    dict(no=1, loc="KYIV REGION, UKRAINE", tag="UKRAINE \u00b7 OVERNIGHT",
         badge="REPORTED", illus=illus_ukraine,
         head="Russia fires 186 drones; a Kyiv block is destroyed",
         body="Air defences down or jam 161 of 186 drones. A five-storey "
              "block in Dymer is destroyed: seven feared trapped, two "
              "injured. (Reuters)"),
    dict(no=2, loc="ANTALYA, TURKIYE", tag="ANTALYA \u00b7 CLIMATE",
         badge="PENDING", illus=illus_antalya,
         head="Climate deal lands with no mention of fossil fuels",
         body="The final text keeps the 35% electricity goal for 2035, "
              "drops the $120bn adaptation target and admits 1.5C will be "
              "overshot. (Reuters)"),
    dict(no=3, loc="MANAMA, BAHRAIN", tag="MANAMA \u00b7 IRAN",
         badge="CLAIM", illus=illus_manama,
         head="Iran claims two US radars hit; Bahrain denies it",
         body="The IRGC says it destroyed two Patriot radars. Bahrain: the "
              "target was a civilian site \u2014 a fire, no injuries. "
              "(Khaleej Times)"),
]


def draw_big_cards():
    cw = 330
    gap = 7
    y = 234
    h = 190
    for i, c in enumerate(BIG_CARDS):
        x = 8 + i * (cw + gap)
        fill(x, y, cw, h, PAPER)
        box(x, y, cw, h, BORDER, 1)
        c['illus'](x + 1, y + 1, cw - 2, 90)
        chip(x + cw - 92, y + 6, c['badge'], BADGE_COL[c['badge']])
        # location line with circled number
        num_badge(x + 14, y + 105, c['no'], 8)
        draw_text(x + 28, y + 102, c['loc'], 1, INK, True)
        # headline, 2 lines
        lines = wrap_text(c['head'], cw - 16, 2, True)
        for k, ln in enumerate(lines[:2]):
            draw_text(x + 8, y + 116 + k * 18, ln, 2, INK, True)
        # body, 3 lines
        blines = wrap_text(c['body'], cw - 16, 1, False)
        for k, ln in enumerate(blines[:3]):
            draw_text(x + 8, y + 154 + k * 12, ln, 1, INK, False)


# ---------------------------------------------------------------- small cards
def strip_hk(x, y, w):
    fill(x, y, w, 22, (191, 227, 240))
    fill(x + 78, y + 3, 34, 16, (29, 78, 216))
    draw_text(x + 83, y + 7, "VOTE", 1, WHITE, True)
    fill(x + 120, y + 12, 60, 3, (120, 126, 138))
    fill(x + 126, y + 5, 8, 8, (220, 38, 38))


def strip_cricket(x, y, w):
    fill(x, y, w, 22, (217, 234, 211))
    poly([(x + 82, y + 18), (x + 88, y + 18), (x + 108, y + 4),
          (x + 102, y + 2)], (146, 96, 48))
    disc(x + 118, y + 13, 4, (220, 38, 38))
    line(x + 128, y + 18, x + 168, y + 18, (120, 126, 138))


def strip_f1(x, y, w):
    fill(x, y, w, 22, (229, 231, 235))
    fill(x + 80, y + 10, 66, 6, (220, 38, 38))
    poly([(x + 96, y + 10), (x + 108, y + 4), (x + 124, y + 4),
          (x + 130, y + 10)], (220, 38, 38))
    disc(x + 92, y + 17, 4, BLACK)
    disc(x + 134, y + 17, 4, BLACK)
    line(x + 74, y + 20, x + 152, y + 20, (120, 126, 138))


def strip_nba(x, y, w):
    fill(x, y, w, 22, (253, 230, 138))
    disc(x + 108, y + 11, 9, (234, 123, 30))
    circle_outline(x + 108, y + 11, 9, (120, 60, 10))
    line(x + 99, y + 11, x + 117, y + 11, (120, 60, 10))
    line(x + 108, y + 2, x + 108, y + 20, (120, 60, 10))


def strip_ship(x, y, w):
    fill(x, y, w, 22, (191, 219, 254))
    fill(x, y + 16, w, 6, (59, 130, 246))
    poly([(x + 78, y + 15), (x + 140, y + 15), (x + 132, y + 8),
          (x + 86, y + 8)], (90, 96, 108))
    fill(x + 96, y + 2, 4, 6, (90, 96, 108))
    for fx in (96, 116):
        poly([(x + fx, y + 8), (x + fx + 8, y + 8), (x + fx + 4, y + 1)],
             (245, 158, 11))


def strip_tehran(x, y, w):
    fill(x, y, w, 22, (254, 243, 199))
    line(x + 84, y + 20, x + 94, y + 2, (90, 96, 108))
    line(x + 124, y + 20, x + 114, y + 2, (90, 96, 108))
    line(x + 88, y + 12, x + 120, y + 12, (90, 96, 108))
    poly([(x + 140, y + 2), (x + 130, y + 12), (x + 137, y + 12),
          (x + 130, y + 20), (x + 146, y + 9), (x + 139, y + 9)],
         (250, 204, 21))


def strip_brasilia(x, y, w):
    fill(x, y, w, 22, (209, 250, 229))
    fill(x + 84, y + 5, 44, 12, WHITE)
    fill(x + 102, y + 2, 8, 18, WHITE)
    fill(x + 99, y + 6, 14, 5, (220, 38, 38))
    fill(x + 104, y + 2, 4, 13, (220, 38, 38))
    line(x + 140, y + 18, x + 168, y + 18, (120, 126, 138))


def strip_washington(x, y, w):
    fill(x, y, w, 22, WHITE)
    for bx, bh in ((84, 6), (94, 10), (104, 8), (114, 14)):
        fill(x + bx, y + 20 - bh, 7, bh, (180, 184, 190))
    line(x + 82, y + 5, x + 100, y + 9, (220, 38, 38))
    line(x + 100, y + 9, x + 118, y + 7, (220, 38, 38))
    line(x + 118, y + 7, x + 140, y + 15, (220, 38, 38))
    disc(x + 140, y + 15, 2, (220, 38, 38))


def strip_nairobi(x, y, w):
    fill(x, y, w, 22, (209, 250, 229))
    poly([(x + 96, y + 3), (x + 120, y + 3), (x + 116, y + 12),
          (x + 108, y + 19), (x + 100, y + 12)], (22, 163, 74))
    line(x + 102, y + 11, x + 106, y + 15, WHITE)
    line(x + 106, y + 15, x + 114, y + 6, WHITE)


SMALL_CARDS = [
    dict(no=4, loc="HONG KONG \u00b7 ELECTION", tag="ELECTION",
         badge="CONFIRMED", strip=strip_hk,
         head="Hong Kong elects its Election Committee",
         body="856 points, 723 seats, 5,700 voters; polls 09:00-18:00. "
              "(SCMP)"),
    dict(no=5, loc="WELLINGTON \u00b7 CRICKET", tag="CRICKET",
         badge="CONFIRMED", strip=strip_cricket,
         head="India declare on 720/9, a record in New Zealand",
         body="Rahul 136, Pant 128, Gill 98; hosts 119/2, trailing by 235. "
              "(ESPN)"),
    dict(no=6, loc="LAS VEGAS \u00b7 FORMULA 1", tag="FORMULA 1",
         badge="CONFIRMED", strip=strip_f1,
         head="Verstappen takes the Las Vegas Grand Prix",
         body="From pole in 1:37:59.24; Norris +0.638, Piastri +1:35.8. "
              "(FIA)"),
    dict(no=7, loc="SAN ANTONIO \u00b7 NBA", tag="NBA",
         badge="CONFIRMED", strip=strip_nba,
         head="Wembanyama scores 50 as the Spurs roll on",
         body="50 pts, 19 rebounds, 5 blocks; 114-91 over New Orleans. "
              "(Reuters)"),
    dict(no=8, loc="GULF OF FINLAND \u00b7 SEA", tag="SEA",
         badge="REPORTED", strip=strip_ship,
         head="Russian cargo ship Sparta II still burning",
         body="Hit by drones Saturday. Finland leads salvage, 16 crew safe. "
              "(Reuters)"),
    dict(no=9, loc="TEHRAN \u00b7 ENERGY", tag="ENERGY",
         badge="CONFIRMED", strip=strip_tehran,
         head="Iran begins rationing electricity",
         body="Rolling cuts up to two hours a day as winter damage bites. "
              "(Wires)"),
    dict(no=10, loc="BRASILIA \u00b7 HEALTH", tag="HEALTH",
         badge="CONFIRMED", strip=strip_brasilia,
         head="Bolsonaro in intensive care in Brasilia",
         body="Acute bowel obstruction, stable; surgery possible. "
              "(Reuters)"),
    dict(no=11, loc="WASHINGTON \u00b7 TECH", tag="TECH",
         badge="REPORTED", strip=strip_washington,
         head="Nvidia faces a US accounting probe",
         body="SEC inquiry at an early stage; shares slide. "
              "(Straits Times)"),
    dict(no=12, loc="NAIROBI \u00b7 HEALTH", tag="HEALTH",
         badge="CONFIRMED", strip=strip_nairobi,
         head="Kenya discharges its last Ebola patient",
         body="Last patient leaves treatment centre; outbreak over. "
              "(Wires)"),
]


def draw_small_cards():
    cw = 328
    gap = 8
    rh = 92
    for i, c in enumerate(SMALL_CARDS):
        row, col = divmod(i, 3)
        x = 8 + col * (cw + gap)
        y = 430 + row * (rh + 6)
        fill(x, y, cw, rh, PAPER)
        box(x, y, cw, rh, BORDER, 1)
        c['strip'](x + 1, y + 1, cw - 2)
        chip(x + 5, y + 5, c['tag'], (185, 28, 28))
        bw = chip(x + cw - 30 - text_w(c['badge'], 1, True) - 10,
                  y + 5, c['badge'], BADGE_COL[c['badge']])
        num_badge(x + cw - 13, y + 12, c['no'], 9)
        draw_text(x + 8, y + 27, c['loc'], 1, INK, True)
        lines = wrap_text(c['head'], cw - 16, 2, True)
        for k, ln in enumerate(lines[:2]):
            draw_text(x + 8, y + 39 + k * 18, ln, 2, INK, True)
        blines = wrap_text(c['body'], cw - 16, 1, False)
        for k, ln in enumerate(blines[:2]):
            draw_text(x + 8, y + 73 + k * 11, ln, 1, INK, False)


# ---------------------------------------------------------------- map + also on
MAP_ART = [
    "                                                ",
    "      ......                       .........    ",
    "   ............                  ...............",
    "  ..............      ....       ...............",
    "  .............       ......     .............. ",
    "   ...........        ......      ............  ",
    "    .........          ....        ..........   ",
    "     .......            ..          ........    ",
    "      .....      ....               ......      ",
    "       ...      ......      ...      ....       ",
    "        ..      ........    ...      ..         ",
    "               .........    ..                  ",
    "               ..........                       ",
    "                .........                       ",
    "                 .......           ....         ",
    "                  .....           ......        ",
    "                   ...             ....         ",
    "                    ..              ..          ",
]

# (lon, lat) of the 12 card stories, in card order
PINS = [
    (30.5, 50.4), (30.7, 36.9), (50.6, 26.2), (114.2, 22.3),
    (174.8, -41.3), (-115.1, 36.2), (-98.5, 29.4), (25.0, 60.0),
    (51.4, 35.7), (-47.9, -15.8), (-77.0, 38.9), (36.8, -1.3),
]

ALSO_ON = [
    ("Vatican City \u2014 Pope Leo XIV hosts 1,300 poor guests "
     "(Vatican News)"),
    ("Belgium \u2014 Controllers join Monday's national strike (Wires)"),
    ("Turin \u2014 ATP Finals title match later today (AP)"),
    ("Denmark \u2014 Expels Russian attache over plot claim "
     "(Guardian)"),
    ("Estonia \u2014 To shut Russia border crossings 1 Dec (AP)"),
    ("Jerusalem \u2014 Eshkolot invites Likud to coalition talks "
     "(Reuters)"),
    ("Gaza City \u2014 Hamas seeks urgent talks after aid strike "
     "(Al Jazeera)"),
    ("Saudi Arabia \u2014 Downs Houthi missile aimed at Riyadh "
     "(Anadolu)"),
    ("Cikande, Indonesia \u2014 Candy-factory fire kills 3 (AFP)"),
    ("Manipur, India \u2014 Toxic-liquor toll climbs to 18 (Xinhua)"),
    ("Seoul \u2014 Education minister's resignation accepted (Reuters)"),
    ("Nepal \u2014 PM Balendra Shah begins India visit (Reuters)"),
    ("Japan \u2014 Snow strands about 1,500 in Hokkaido village (dpa)"),
    ("Taipei \u2014 Taiwan tracks 18 Chinese aircraft near island "
     "(Reuters)"),
    ("Somalia \u2014 Expels UAE ambassador, recalls envoy (Wires)"),
    ("South Africa \u2014 Thembiile Mtambo-Ngcuka dies at 71 (Reuters)"),
    ("Cairo \u2014 Grand Museum draws record crowds (AP)"),
    ("US \u2014 Tornadoes and ice batter; FBI rescues girl (BBC)"),
    ("Canberra \u2014 Musk's US budget attack 'wrong', in AUKUS "
     "(Reuters)"),
    ("Melbourne \u2014 70 years since the 1956 Olympics opened (ABC)"),
    ("Moscow \u2014 Russia says it downed 110 Ukrainian drones "
     "(Reuters)"),
    ("The Hague \u2014 World court: Myanmar committed genocide "
     "(Guardian)"),
    ("Trade \u2014 EU and Indonesia sign deal after 10 years (AP)"),
    ("Ukraine \u2014 IMF approves $8bn of funding for Kyiv (Reuters)"),
]


def draw_bottom():
    draw_text(8, 726, "WHERE IT HAPPENED", 2, INK, True)
    draw_text(280, 726, "ALSO ON SUNDAY 22 NOVEMBER \u2014 24 MORE STORIES",
              2, INK, True)
    # dotted world map
    mx, my = 8, 748
    cellw = 260 / 48.0
    cellh = 128 / 18.0
    for r, row in enumerate(MAP_ART):
        for cc, ch in enumerate(row):
            if ch == '.':
                fill(int(mx + cc * cellw) + 1, int(my + r * cellh) + 1,
                     3, 3, (168, 152, 120))
    # pins with numbers; crowded pins get their label moved aside
    lab_off = {2: (-14, -4), 3: (6, 3), 5: (-14, -4)}
    for i, (lon, lat) in enumerate(PINS):
        px = mx + (lon + 180.0) / 360.0 * 260
        py = my + (90.0 - lat) / 180.0 * 128
        disc(int(px), int(py), 4, RED)
        circle_outline(int(px), int(py), 4, WHITE)
        dx, dy = lab_off.get(i + 1, (6, -4))
        draw_text(int(px) + dx, int(py) + dy, str(i + 1), 1, RED, True)
    # legend
    draw_text(8, 882, "TAGS: CONFIRMED 2+ outlets \u00b7", 1, INK, True)
    draw_text(8, 893, "CLAIM one side's claim \u00b7", 1, INK, True)
    draw_text(8, 904, "REPORTED 1 source \u00b7 PENDING not settled",
              1, INK, True)
    # ALSO ON, 3 columns of 8
    for col in range(3):
        cx = 280 + col * 248
        for k in range(8):
            idx = col * 8 + k
            no = 13 + idx
            ey = 748 + k * 22
            draw_text(cx, ey, str(no), 1, RED, True)
            lines = wrap_text(ALSO_ON[idx], 222, 1, False)
            for j, ln in enumerate(lines[:2]):
                draw_text(cx + 18, ey + j * 11, ln, 1, INK, False)


def draw_datecheck():
    box(8, 926, 1008, 68, DRED, 2)
    draw_text(16, 932, "DATE CHECK \u2014 READ FIRST!", 2, DRED, True)
    body = ("Wires read up to 08:45 UTC, Sunday 22 November 2026. Every "
            "story here happened on 22 November 2026 (UTC). Left out on "
            "purpose \u2014 they belong to other days: the 400-drone, "
            "110-missile barrage (Thu 19-Fri 20 Nov) \u00b7 the Peru quake "
            "(Fri 20 Nov) \u00b7 'El Chapo Isidro' captured (Fri 21 Nov) "
            "\u00b7 the Bayelsa boat, 24 dead (Fri 21 Nov) \u00b7 the Gaza "
            "aid-van strike (Sat 21 Nov) \u00b7 BepiColombo's Mercury burn "
            "(Sat 21 Nov) \u00b7 the Kryvyi Rih double-tap (Fri 20-Sat 21 "
            "Nov). Tonight's real count: 186 drones, 161 downed.")
    lines = wrap_text(body, 976, 1, False)
    for k, ln in enumerate(lines[:4]):
        draw_text(16, 950 + k * 11, ln, 1, INK, False)


def draw_footer():
    draw_text(8, 998,
              "Sources: Reuters, BBC, Al Jazeera, The Guardian, AP, AFP, "
              "SCMP, ESPN, FIA, Xinhua, dpa, Anadolu, Vatican News. "
              "Pictures and map: original, drawn in code.",
              1, GREY, False)
    hline(8, 1008, 1008, LGREY)
    draw_text(8, 1012, "THE WORLD IN ONE DAY", 1, INK, True)
    draw_text(W // 2, 1012, "SUNDAY 22 NOVEMBER 2026", 1, INK, True,
              align='center')
    draw_text(1016, 1012, "ONE PAGE", 1, INK, True, align='right')


def draw_page():
    fill(0, 0, W, H, CREAM)
    draw_header()
    draw_numbers()
    draw_region_bar()
    draw_big_cards()
    draw_small_cards()
    draw_bottom()
    draw_datecheck()
    draw_footer()


if __name__ == '__main__':
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    draw_page()
    path = os.path.join(out_dir, 'entry.png')
    write_png(path)
    print('wrote', path, os.path.getsize(path), 'bytes')
