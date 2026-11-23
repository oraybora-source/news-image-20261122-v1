#!/usr/bin/env python3
"""news-image-20261122 V1 renderer — rule-based, deterministic.
Build-time only. The graded entrypoint (main.py) copies the PNG this
script produces; this script itself never ships in the repo.
Draws entry.png 1024x1024, <1 MiB, byte-identical across runs.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
NAVY = (31, 58, 95)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)
BRICK = (166, 58, 43)
LAND = (216, 208, 188)
LAND_LINE = (190, 182, 160)
LIGHT_LINE = (200, 192, 170)

REGION = {"EU": (51, 86, 127), "ME": (166, 58, 43), "AS": (47, 107, 79),
          "AF": (150, 100, 8), "AM": (110, 74, 138), "OC": (23, 129, 123),
          "WORLD": (85, 85, 85)}
REGION_NAME = {"EU": "EUROPE", "ME": "MID EAST", "AS": "ASIA", "AF": "AFRICA",
               "AM": "AMERICAS", "OC": "OCEANIA", "WORLD": "WORLD"}

FONT_DIR = "/usr/share/fonts/truetype/liberation"
_fonts = {}


def _font(name, size):
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    return _fonts[key]


def F_MAST(size):
    return _font("LiberationSerif-Bold.ttf", size)


def F_SANS(size):
    return _font("LiberationSans-Regular.ttf", size)


def F_SANSB(size):
    return _font("LiberationSans-Bold.ttf", size)


def F_SERIF(size):
    return _font("LiberationSerif-Regular.ttf", size)


def text_w(draw, s, font):
    return int(draw.textlength(s, font=font))


def tint(rgb, amount):
    """Mix a region colour toward the paper colour."""
    return tuple(int(round(rgb[i] + (PAPER[i] - rgb[i]) * amount))
                 for i in range(3))


def contrast(c1, c2):
    def lum(c):
        def f(v):
            v = v / 255
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = f(c[0]), f(c[1]), f(c[2])
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1, l2 = sorted((lum(c1), lum(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, font, max_w, max_lines):
    lines = wrap(draw, text, font, max_w)
    if len(lines) <= max_lines:
        return lines
    out = lines[:max_lines]
    while out and text_w(draw, out[-1] + " …", font) > max_w:
        out[-1] = out[-1].rsplit(" ", 1)[0] if " " in out[-1] else out[-1][:-1]
    out[-1] = out[-1] + " …"
    return out


# ---------------------------------------------------------------- data
# 13 stories, all verified Sunday 22 Nov 2026 (see notes/sumber.md).
# num = the story's number, baked into its illustration on a paper chip.
STORIES = [
    {"n": 1, "hero": True, "region": "EU", "place": "ANTALYA",
     "title": "COP31 COLLAPSES", "num": "NO DEAL",
     "summary": "Climate talks end with no deal; the EU rejects a draft with no fossil fuels.",
     "source": "REUTERS", "status": "CONFIRMED", "art": "cop31"},
    {"n": 2, "hero": True, "region": "ME", "place": "MANAMA",
     "title": "IRAN STRIKES BAHRAIN", "num": "2",
     "summary": "Bahrain says two were hurt; the Gulf condemns the attack.",
     "source": "REUTERS", "status": "CONFIRMED", "art": "bahrain"},
    {"n": 3, "hero": True, "region": "EU", "place": "DYMER",
     "title": "DRONE HITS FLATS NEAR KYIV", "num": "14",
     "summary": "A Russian drone strikes a five-storey block in Dymer; 14 people are missing.",
     "source": "AP", "status": "CONFIRMED", "art": "dymer"},
    {"n": 4, "hero": False, "region": "WORLD", "place": "MERCURY",
     "title": "BEPICOLOMBO IN ORBIT", "num": "8",
     "summary": "ESA confirms orbit after 8 years — with a thruster glitch.",
     "source": "ESA / REUTERS", "status": "CONFIRMED", "art": "bepi"},
    {"n": 5, "hero": False, "region": "AS", "place": "CIKANDE",
     "title": "SEARCH FOR 36 MISSING", "num": "36",
     "summary": "Rescuers comb a burned factory; 3 dead, 15 alive.",
     "source": "AP / REUTERS", "status": "CONFIRMED", "art": "cikande"},
    {"n": 6, "hero": False, "region": "EU", "place": "ANFIELD",
     "title": "LIVERPOOL ROUT UNITED", "num": "4–0",
     "summary": "Four goals, no reply, in the Sunday derby at Anfield.",
     "source": "NBC SPORTS", "status": "CONFIRMED", "art": "liverpool"},
    {"n": 7, "hero": False, "region": "AS", "place": "NEW DELHI",
     "title": "NEPAL'S PM LANDS IN DELHI", "num": "34",
     "summary": "Balen Shah begins his first foreign visit; Modi talks Monday.",
     "source": "MEA INDIA", "status": "CONFIRMED", "art": "nepal"},
    {"n": 8, "hero": False, "region": "ME", "place": "RAMALLAH",
     "title": "SETTLERS TORCH 12 VEHICLES", "num": "12",
     "summary": "Settlers torch cars in four villages; Israel opens an inquiry.",
     "source": "AP", "status": "CONFIRMED", "art": "westbank"},
    {"n": 9, "hero": False, "region": "AF", "place": "KHARTOUM",
     "title": "DRONES HIT KHARTOUM", "num": "4",
     "summary": "Four killed as drones hit homes and a UN building at dawn.",
     "source": "UN / AFP", "status": "CONFIRMED", "art": "khartoum"},
    {"n": 10, "hero": False, "region": "AM", "place": "KANSAS CITY",
     "title": "CHIEFS CRUSH CARDINALS", "num": "34",
     "summary": "Kansas City runs away with it at Arrowhead in Week 11.",
     "source": "SPORTRADAR", "status": "CONFIRMED", "art": "chiefs"},
    {"n": 11, "hero": False, "region": "AM", "place": "ASUNCIÓN",
     "title": "BOCA LIFT THE COPA", "num": "2–0",
     "summary": "Boca beat Atlético Mineiro 2–0 to win the Copa Sudamericana.",
     "source": "LIVESCORE", "status": "CONFIRMED", "art": "boca"},
    {"n": 12, "hero": False, "region": "AS", "place": "LAHORE",
     "title": "LAHORE CHOKES AT 500 AQI", "num": "500",
     "summary": "The world's most polluted city tops 500 as smog grips Punjab.",
     "source": "REPORTED", "status": "REPORTED", "art": "lahore"},
    {"n": 13, "hero": False, "region": "OC", "place": "WELLINGTON",
     "title": "INDIA 720/9 IN NZ", "num": "720",
     "summary": "Record Test total on Kiwi soil: Rahul 136, Pant 128.",
     "source": "LIVESCORE", "status": "CONFIRMED", "art": "cricket"},
]

MORE = [
    "Sparta II still smouldering in the Gulf of Finland, a day after a drone strike.",
    "Gaza: an IDF strike in the north leaves one person critically hurt.",
    "Lebanon's army arrests three over 264 kg of explosives smuggled from Syria.",
    "Poland reveals Russia twice tried to kill a Ukrainian-American rapper; Denmark expelled a Russian official.",
    "New Zealand: one killed, four hurt as a house slips off its supports in Ruatōria.",
    "NFL Sunday: Cowboys 51–30 Titans; Panthers 35–33 Ravens.",
    "Football: Barcelona come back from 2–0 down to beat Villarreal 3–2.",
    "Australia's dollar tipped to rebound against the Kiwi after its worst month since 2022.",
]

TIMELINE = [
    ("00:00–02:30", "Khartoum drones"),
    ("00:56", "BepiColombo confirmed"),
    ("~09:45", "Nepal PM lands in Delhi"),
    ("16:30", "Liverpool–Man Utd KO"),
    ("~17:00", "COP31: no deal"),
]

BIGNUMS = [("NO DEAL", "COP31 climate talks"),
           ("2 HURT", "Iran strikes Bahrain"),
           ("14 MISSING", "Drone hits flats near Kyiv"),
           ("36 MISSING", "Cikande factory fire"),
           ("720", "India's record Test total")]

DATECHECK = [
    "DATE CHECK — NOT SUNDAY: El Chapo captured Sat 21 Nov · ICJ Rohingya verdict Thu 19 Nov",
    "EU–Indonesia deal Sat 21 Nov · FBI hack first reported Fri 20 Nov · Maluku quake Sat 21 Nov",
    "S&P 500 −3.7% Fri close · Trump–Xi–Putin summit 19–20 Nov · BepiColombo burn Sat 21 Nov",
]

HOWCHECKED = ("HOW WE CHECKED — Every story dated 22 Nov 2026 from primary reporting; "
              "claims labelled CLAIM. Sources: Reuters · AP · AFP · ESA · UN · NBC Sports.")

# ---------------------------------------------------------------- illustrations
# Every painter fills its box (x0, y0, x1, y1) with flat solid shapes and
# then bakes the story's number in as a paper chip at the bottom-left —
# drawn last, so the number can never be covered by the scene (ni21
# lesson: card 9 "136" was ~79% covered). No thin-line human figures.

def big_num(draw, box, st):
    """Paper chip with the story's number, bottom-left of the box."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    s = st["num"]
    size = 30 if w > 250 else 24
    while size > 12 and text_w(draw, s, F_SANSB(size)) > 0.55 * w:
        size -= 2
    f = F_SANSB(size)
    tw = text_w(draw, s, f)
    ch, cw = size + 12, tw + 18
    cx, cy = x0 + 6, y1 - 6 - ch
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=4,
                           fill=PAPER, outline=REGION[st["region"]], width=2)
    col = BRICK if s == "NO DEAL" else INK
    draw.text((cx + 9, cy + 5), s, font=f, fill=col)


def _flag(draw, x, y, w, h, colors):
    n = len(colors)
    for i, c in enumerate(colors):
        draw.rectangle([x, y + i * h // n, x + w, y + (i + 1) * h // n], fill=c)


def paint_cop31(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(24, 45, 75))
    draw.rectangle([x0, y0 + h - 14, x1, y1], fill=(60, 70, 60))
    fw, fh = 34, 22
    draw.line([x0 + 14 + fw // 2, y0 + 10, x0 + 14 + fw // 2, y0 + 10 + fh + 26],
              fill=(200, 200, 200), width=2)
    draw.rectangle([x0 + 14, y0 + 10, x0 + 14 + fw, y0 + 10 + fh], fill=(0, 51, 153))
    for i in range(6):
        ang = i * 60
        import math
        cx = x0 + 14 + fw // 2 + int(7 * math.cos(math.radians(ang)))
        cy = y0 + 10 + fh // 2 + int(7 * math.sin(math.radians(ang)))
        draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(255, 204, 0))
    draw.line([x1 - 14 - fw // 2, y0 + 10, x1 - 14 - fw // 2, y0 + 10 + fh + 26],
              fill=(200, 200, 200), width=2)
    draw.rectangle([x1 - 14 - fw, y0 + 10, x1 - 14, y0 + 10 + fh], fill=(227, 10, 23))
    draw.rectangle([x1 - 14 - fw, y0 + 10, x1 - 14 - fw + 6, y0 + 10 + fh],
                   fill=WHITE)
    dx = x0 + int(w * 0.52)
    dw, dh = int(w * 0.44), 24
    dy = y1 - 30
    draw.rectangle([dx, dy, dx + dw, dy + dh], fill=WHITE)
    draw.rectangle([dx, dy, dx + dw, dy + dh], outline=(150, 150, 150), width=1)
    for i in range(3):
        draw.line([dx + 8, dy + 6 + i * 6, dx + dw - 8, dy + 6 + i * 6],
                  fill=(120, 120, 120), width=1)
    draw.line([dx + dw - 22, dy + 4, dx + dw - 6, dy + dh - 4], fill=BRICK, width=3)
    draw.line([dx + dw - 6, dy + 4, dx + dw - 22, dy + dh - 4], fill=BRICK, width=3)
    big_num(draw, box, st)


def paint_bahrain(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(30, 32, 48))
    for sx, sy in [(0.12, 0.15), (0.25, 0.08), (0.5, 0.12), (0.7, 0.07),
                   (0.85, 0.18), (0.95, 0.1)]:
        draw.ellipse([x0 + w * sx - 1, y0 + h * sy - 1,
                      x0 + w * sx + 1, y0 + h * sy + 1], fill=WHITE)
    bx = x0 + int(w * 0.34)
    bw, by, bh = int(w * 0.42), y0 + int(h * 0.42), int(h * 0.58)
    draw.rectangle([bx, by, bx + bw, y1], fill=(70, 75, 95))
    draw.rectangle([bx, by, bx + bw, by + 6], fill=(50, 55, 75))
    for r in range(4):
        for c in range(5):
            wx = bx + 8 + c * (bw - 16) // 5
            wy = by + 14 + r * (bh - 20) // 4
            draw.rectangle([wx, wy, wx + 7, wy + 9],
                           fill=(255, 210, 90) if (r + c) % 3 else (40, 45, 65))
    dx, dy = x1 - 40, y0 + 14
    draw.line([dx, dy, dx - 22, dy + 18], fill=(150, 160, 190), width=3)
    draw.ellipse([dx - 14, dy - 6, dx + 14, dy + 6], fill=(150, 160, 190))
    for r in (18, 30, 42):
        draw.arc([dx - r, dy - r, dx + r, dy + r], start=180, end=270,
                 fill=(255, 210, 90), width=2)
    fx, fy = bx + bw - 10, by - 4
    draw.polygon([(fx, fy), (fx - 8, fy + 12), (fx + 8, fy + 12)],
                 fill=(255, 140, 40))
    draw.rectangle([x0, y1 - 4, x1, y1], fill=(20, 22, 34))
    big_num(draw, box, st)


def paint_dymer(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(36, 40, 52))
    for sx, sy in [(0.1, 0.12), (0.3, 0.06), (0.6, 0.14), (0.85, 0.08)]:
        draw.ellipse([x0 + w * sx - 1, y0 + h * sy - 1,
                      x0 + w * sx + 1, y0 + h * sy + 1], fill=WHITE)
    draw.polygon([(x1 - 8, y0 + 4), (x1 - 30, y0 + 4),
                  (x0 + w * 0.25, y1 - 6), (x0 + w * 0.45, y1 - 6)],
                 fill=(240, 225, 160))
    bx = x0 + int(w * 0.30)
    by, bw, bh = y0 + int(h * 0.22), int(w * 0.52), int(h * 0.62)
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(90, 85, 80))
    draw.rectangle([bx, by, bx + bw, by + 5], fill=(60, 56, 52))
    draw.rectangle([bx + bw // 2 - 10, by + 10, bx + bw // 2 + 12, by + 34],
                   fill=(20, 18, 16))
    for r in range(3):
        for c in range(4):
            wx = bx + 8 + c * (bw - 16) // 4
            wy = by + 8 + r * (bh - 16) // 3
            if (r, c) in ((0, 1), (0, 2), (1, 1)):
                continue
            draw.rectangle([wx, wy, wx + 8, wy + 9],
                           fill=(255, 210, 90) if (r + c) % 2 else (55, 52, 48))
    for i, (rx, rw) in enumerate([(0.30, 14), (0.42, 10), (0.52, 16)]):
        draw.polygon([(x0 + w * rx, y1 - 4), (x0 + w * rx + rw // 2, y1 - 12),
                      (x0 + w * rx + rw, y1 - 4)], fill=(60, 56, 52))
    big_num(draw, box, st)


def paint_bepi(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(12, 14, 28))
    for sx, sy in [(0.08, 0.1), (0.2, 0.25), (0.35, 0.08), (0.55, 0.15),
                   (0.7, 0.06), (0.88, 0.2), (0.95, 0.35)]:
        draw.ellipse([x0 + w * sx - 1, y0 + h * sy - 1,
                      x0 + w * sx + 1, y0 + h * sy + 1], fill=WHITE)
    draw.arc([x0 + w * 0.05, y0 + h * 0.1, x1 - w * 0.05, y1 - h * 0.1],
             start=200, end=340, fill=(120, 140, 180), width=2)
    r = min(20, int(h * 0.30))
    cx, cy = x1 - r - 10, y1 - r - 6
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 170, 120))
    draw.ellipse([cx - r // 2, cy - r // 3, cx - r // 4, cy], fill=(170, 140, 95))
    draw.ellipse([cx + r // 4, cy + r // 4, cx + r // 2, cy + r // 2],
                 fill=(170, 140, 95))
    sx, sy = x0 + int(w * 0.30), y0 + int(h * 0.30)
    draw.rectangle([sx - 16, sy - 4, sx - 4, sy + 4], fill=(120, 140, 170))
    draw.rectangle([sx + 4, sy - 4, sx + 16, sy + 4], fill=(120, 140, 170))
    draw.rectangle([sx - 6, sy - 8, sx + 6, sy + 8], fill=(180, 190, 200))
    draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 210, 90))
    bx, by = x0 + int(w * 0.58), y0 + int(h * 0.45)
    draw.polygon([(bx, by), (bx + 8, by + 10), (bx, by + 20), (bx + 8, by + 30)],
                 fill=(255, 210, 90))
    big_num(draw, box, st)


def paint_cikande(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for i, c in enumerate([(70, 45, 35), (90, 55, 40), (110, 65, 45)]):
        draw.rectangle([x0, y0 + i * h // 3, x1, y0 + (i + 1) * h // 3], fill=c)
    fy = y0 + int(h * 0.55)
    for sx, sy, sr in [(0.35, 6, 7), (0.55, 12, 9), (0.75, 18, 11)]:
        draw.ellipse([x0 + w * sx - sr, fy - sy - sr, x0 + w * sx + sr,
                      fy - sy + sr], fill=(120, 110, 105))
    draw.rectangle([x0, fy, x1, y1], fill=(40, 32, 28))
    for i in range(6):
        tx = x0 + i * w // 6
        draw.polygon([(tx, fy), (tx + w // 12, fy - 8), (tx + w // 6, fy)],
                     fill=(55, 45, 40))
    for i in range(5):
        wx = x0 + 10 + i * (w - 20) // 5
        draw.rectangle([wx, fy + 8, wx + 12, fy + 18],
                       fill=(255, 150, 50) if i % 2 else (60, 50, 45))
    fx = x1 - int(w * 0.25)
    draw.polygon([(fx, fy - int(h * 0.22)), (fx - 10, fy), (fx + 10, fy)],
                 fill=(255, 140, 40))
    draw.polygon([(fx, fy - int(h * 0.12)), (fx - 5, fy), (fx + 5, fy)],
                 fill=(255, 220, 90))
    big_num(draw, box, st)


def paint_liverpool(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for i in range(5):
        c = (34, 120, 60) if i % 2 == 0 else (28, 100, 52)
        draw.rectangle([x0, y0 + i * h // 5, x1, y0 + (i + 1) * h // 5], fill=c)
    gx = x1 - int(w * 0.30)
    gy, gw, gh = y0 + int(h * 0.28), int(w * 0.26), int(h * 0.44)
    draw.rectangle([gx, gy, gx + gw, gy + gh], outline=WHITE, width=3)
    for i in range(1, 4):
        draw.line([gx + i * gw // 4, gy, gx + i * gw // 4, gy + gh],
                  fill=WHITE, width=1)
    for i in range(1, 3):
        draw.line([gx, gy + i * gh // 3, gx + gw, gy + i * gh // 3],
                  fill=WHITE, width=1)
    bx, by = x0 + int(w * 0.62), y0 + int(h * 0.68)
    draw.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=WHITE)
    draw.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=INK)
    big_num(draw, box, st)


def paint_nepal(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(135, 180, 220))
    draw.polygon([(x0, y1), (x0 + w * 0.30, y0 + h * 0.45),
                  (x0 + w * 0.62, y1)], fill=(110, 130, 160))
    draw.polygon([(x0 + w * 0.45, y1), (x0 + w * 0.72, y0 + h * 0.55),
                  (x1, y1)], fill=(90, 110, 140))
    draw.rectangle([x0, y1 - 6, x1, y1], fill=(80, 120, 70))
    fx1, fx2 = x0 + int(w * 0.18), x1 - int(w * 0.28)
    fy = y0 + int(h * 0.18)
    fh = 24
    draw.line([fx1, fy, fx1, y0 + int(h * 0.85)], fill=(80, 70, 60), width=2)
    draw.polygon([(fx1, fy), (fx1 + 26, fy + fh // 2), (fx1, fy + fh)],
                 fill=(220, 20, 60))
    draw.line([fx2, fy, fx2, y0 + int(h * 0.85)], fill=(80, 70, 60), width=2)
    _flag(draw, fx2, fy, 30, fh, [(255, 153, 51), WHITE, (19, 136, 8)])
    draw.ellipse([fx2 + 12, fy + 9, fx2 + 18, fy + 15], fill=NAVY)
    # dashed route arc between the flag tops (clamped inside the box)
    pts = []
    for t in range(0, 21):
        u = t / 20
        px = fx1 + 13 + u * (fx2 + 15 - (fx1 + 13))
        py = fy - int(h * 0.22) * 4 * u * (1 - u)
        pts.append((px, max(py, y0 + 6)))
    for i in range(0, len(pts) - 1, 2):
        draw.line([pts[i], pts[i + 1]], fill=(60, 60, 60), width=2)
    mx, my = pts[10]
    draw.polygon([(mx - 7, my), (mx + 7, my), (mx, my + 6)], fill=WHITE)
    big_num(draw, box, st)


def paint_westbank(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(220, 200, 170))
    draw.ellipse([x0, y1 - int(h * 0.35), x0 + int(w * 0.55), y1 + int(h * 0.1)],
                 fill=(150, 160, 100))
    draw.ellipse([x0 + int(w * 0.45), y1 - int(h * 0.30), x1, y1 + int(h * 0.1)],
                 fill=(130, 140, 85))
    base = y1 - 8
    for hx, hw, hh in [(0.30, 0.16, 0.30), (0.50, 0.14, 0.24), (0.68, 0.18, 0.34)]:
        hx0 = x0 + int(w * hx)
        hw0, hh0 = int(w * hw), int(h * hh)
        draw.rectangle([hx0, base - hh0, hx0 + hw0, base], fill=(200, 180, 150))
        draw.polygon([(hx0 - 3, base - hh0), (hx0 + hw0 // 2, base - hh0 - 12),
                      (hx0 + hw0 + 3, base - hh0)], fill=(170, 70, 50))
    cx, cy = x0 + int(w * 0.55), y1 - int(h * 0.22)
    draw.polygon([(cx, cy - 26), (cx - 7, cy - 8), (cx + 7, cy - 8)],
                 fill=(255, 140, 40))
    draw.ellipse([cx - 8, cy - 34, cx + 8, cy - 22], fill=(140, 130, 125))
    draw.rectangle([cx - 17, cy - 6, cx + 17, cy + 4], fill=(40, 40, 45))
    draw.polygon([(cx - 10, cy - 6), (cx - 6, cy - 14), (cx + 8, cy - 14),
                  (cx + 12, cy - 6)], fill=(60, 60, 70))
    for wx in (cx - 11, cx + 7):
        draw.ellipse([wx, cy + 2, wx + 8, cy + 10], fill=INK)
    big_num(draw, box, st)


def paint_khartoum(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(45, 45, 60))
    for sx, sy in [(0.12, 0.1), (0.3, 0.18), (0.55, 0.08), (0.8, 0.14),
                   (0.92, 0.06)]:
        draw.ellipse([x0 + w * sx - 1, y0 + h * sy - 1,
                      x0 + w * sx + 1, y0 + h * sy + 1], fill=WHITE)
    base = y1 - int(h * 0.18)
    for bx, bw, bh in [(0.32, 0.18, 0.42), (0.54, 0.15, 0.55), (0.73, 0.20, 0.38)]:
        bx0 = x0 + int(w * bx)
        bw0, bh0 = int(w * bw), int(h * bh)
        draw.rectangle([bx0, base - bh0, bx0 + bw0, base], fill=(25, 25, 35))
        for r in range(3):
            for c in range(3):
                if (r + c) % 2:
                    draw.rectangle([bx0 + 4 + c * (bw0 - 8) // 3,
                                    base - bh0 + 6 + r * (bh0 - 12) // 3,
                                    bx0 + 9 + c * (bw0 - 8) // 3,
                                    base - bh0 + 11 + r * (bh0 - 12) // 3],
                                   fill=(255, 210, 90))
    ex, ey = x0 + int(w * 0.61), base - int(h * 0.55)
    for ang in range(0, 360, 45):
        import math
        x2 = ex + int(12 * math.cos(math.radians(ang)))
        y2 = ey + int(12 * math.sin(math.radians(ang)))
        draw.line([ex, ey, x2, y2], fill=(255, 140, 40), width=3)
    draw.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=(255, 220, 90))
    fx = x1 - int(w * 0.12)
    fy = y0 + int(h * 0.12)
    draw.line([fx, fy, fx, y0 + int(h * 0.45)], fill=(150, 150, 150), width=2)
    draw.rectangle([fx, fy, fx + 22, fy + 13], fill=(0, 91, 172))
    draw.ellipse([fx + 8, fy + 3, fx + 14, fy + 9], fill=WHITE)
    dx, dy = x0 + int(w * 0.55), y0 + int(h * 0.25)
    draw.line([dx - 8, dy - 8, dx + 8, dy + 8], fill=(150, 160, 190), width=2)
    draw.line([dx - 8, dy + 8, dx + 8, dy - 8], fill=(150, 160, 190), width=2)
    draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(255, 60, 40))
    big_num(draw, box, st)


def paint_chiefs(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for i in range(6):
        c = (34, 120, 60) if i % 2 == 0 else (28, 100, 52)
        draw.rectangle([x0 + i * w // 6, y0, x0 + (i + 1) * w // 6, y1], fill=c)
    draw.rectangle([x0, y0, x0 + int(w * 0.12), y1], fill=(200, 40, 40))
    for i in range(1, 5):
        lx = x0 + i * w // 5
        draw.line([lx, y0, lx, y1], fill=WHITE, width=2)
    bx, by = x0 + int(w * 0.5), y0 + h // 2
    draw.ellipse([bx - 22, by - 12, bx + 22, by + 12], fill=(120, 70, 30))
    draw.line([bx - 12, by, bx + 12, by], fill=WHITE, width=2)
    for lx in (-8, -3, 2, 7):
        draw.line([bx + lx, by - 4, bx + lx, by + 4], fill=WHITE, width=1)
    big_num(draw, box, st)


def paint_boca(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(20, 30, 60))
    draw.pieslice([x0 + w * 0.04, y0 - h * 0.45, x1 - w * 0.04, y0 + h * 0.8],
                  start=0, end=180, fill=(40, 60, 110))
    for i in range(5):
        for j in range(9):
            dx = x0 + w * (0.10 + j * 0.10)
            dy = y0 + h * (0.10 + i * 0.08)
            c = [(255, 220, 90), (255, 255, 255), (200, 60, 60),
                 (120, 180, 255)][(i * 9 + j) % 4]
            draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=c)
    draw.rectangle([x0, y0 + int(h * 0.62), x1, y1], fill=(34, 120, 60))
    draw.line([x0, y0 + int(h * 0.62), x1, y0 + int(h * 0.62)], fill=WHITE, width=1)
    tx, ty = x0 + w // 2, y0 + int(h * 0.45)
    draw.polygon([(tx - 14, ty - 12), (tx + 14, ty - 12), (tx + 10, ty + 2),
                  (tx - 10, ty + 2)], fill=(230, 190, 60))
    draw.rectangle([tx - 3, ty + 2, tx + 3, ty + 10], fill=(230, 190, 60))
    draw.rectangle([tx - 12, ty + 10, tx + 12, ty + 14], fill=(200, 160, 40))
    big_num(draw, box, st)


def paint_lahore(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for i, c in enumerate([(200, 170, 120), (190, 150, 100),
                           (170, 130, 85), (150, 115, 75)]):
        draw.rectangle([x0, y0 + i * h // 4, x1, y0 + (i + 1) * h // 4], fill=c)
    sx, sy, sr = x1 - int(w * 0.22), y0 + int(h * 0.28), int(h * 0.22)
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(240, 200, 120))
    tx, ty = x0 + 10, y0 + 8
    th = int(h * 0.45)
    draw.rectangle([tx, ty, tx + 8, ty + th], fill=WHITE)
    draw.rectangle([tx + 2, ty + th // 5, tx + 6, ty + th], fill=(200, 60, 40))
    draw.ellipse([tx - 3, ty + th - 4, tx + 11, ty + th + 10], fill=(200, 60, 40))
    base = y1 - int(h * 0.08)
    for i, bhf in enumerate([0.34, 0.44, 0.28, 0.40, 0.32]):
        bx0 = x0 + int(w * (0.05 + i * 0.18))
        bw0, bh0 = int(w * 0.16), int(h * bhf)
        draw.rectangle([bx0, base - bh0, bx0 + bw0, base], fill=(90, 70, 55))
        draw.rectangle([bx0 + 3, base - bh0 + 4, bx0 + 7, base - bh0 + 8],
                       fill=(200, 170, 120))
    big_num(draw, box, st)


def paint_cricket(draw, box, st):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle(box, fill=(60, 130, 70))
    draw.rectangle([x0 + int(w * 0.38), y0, x0 + int(w * 0.62), y1],
                   fill=(200, 180, 130))
    draw.line([x0 + int(w * 0.38), y0, x0 + int(w * 0.38), y1], fill=WHITE, width=1)
    draw.line([x0 + int(w * 0.62), y0, x0 + int(w * 0.62), y1], fill=WHITE, width=1)
    sx = x0 + w // 2
    sy = y0 + int(h * 0.28)
    for dx in (-8, 0, 8):
        draw.rectangle([sx + dx - 2, sy, sx + dx + 2, sy + 16], fill=(255, 220, 90))
    draw.polygon([(x0 + int(w * 0.30), y0 + int(h * 0.55)),
                  (x0 + int(w * 0.38), y0 + int(h * 0.50)),
                  (x0 + int(w * 0.42), y0 + int(h * 0.72)),
                  (x0 + int(w * 0.34), y0 + int(h * 0.77))], fill=(160, 110, 60))
    bx, by = x0 + int(w * 0.72), y0 + int(h * 0.62)
    draw.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=(200, 40, 40))
    draw.arc([bx - 8, by - 8, bx + 8, by + 8], start=200, end=340, fill=WHITE, width=1)
    big_num(draw, box, st)


PAINTERS = {"cop31": paint_cop31, "bahrain": paint_bahrain, "dymer": paint_dymer,
            "bepi": paint_bepi, "cikande": paint_cikande,
            "liverpool": paint_liverpool, "nepal": paint_nepal,
            "westbank": paint_westbank, "khartoum": paint_khartoum,
            "chiefs": paint_chiefs, "boca": paint_boca, "lahore": paint_lahore,
            "cricket": paint_cricket}

# ---------------------------------------------------------------- layout
MX, GUT = 16, 12
CW = W - 2 * MX  # 992 content width

def status_color(s):
    return {"CONFIRMED": (47, 107, 79), "REPORTED": (51, 86, 127),
            "CLAIM": (166, 58, 43)}[s]

def draw_band(draw, x0, y0, x1, y1, st, big=False):
    """Top band: number badge + region + place + status tag."""
    rc = REGION[st["region"]]
    draw.rectangle([x0, y0, x1, y1], fill=rc)
    fs = 15 if big else 12
    fnum = F_SANSB(fs)
    num = str(st["n"])
    d = y1 - y0 - 4
    cx, cy = x0 + 4 + d // 2, y0 + (y1 - y0) // 2
    draw.ellipse([cx - d // 2, cy - d // 2, cx + d // 2, cy + d // 2], fill=WHITE)
    nw = text_w(draw, num, fnum)
    draw.text((cx - nw / 2, cy - fs / 2 - 1), num, font=fnum, fill=rc)
    fx = x0 + 4 + d + 6
    fplace = F_SANSB(12 if big else 10)
    place = st["place"]
    while text_w(draw, place, fplace) > (x1 - x0) - (fx - x0) - 92 and len(place) > 4:
        place = place[:-1].strip()
    draw.text((fx, y0 + (y1 - y0) / 2 - (12 if big else 10) / 2 - 1),
              place, font=fplace, fill=WHITE)
    tag = st["status"]
    ft = F_SANSB(9 if big else 8)
    tw = text_w(draw, tag, ft) + 10
    tx = x1 - tw - 4
    ty = y0 + 3
    draw.rounded_rectangle([tx, ty, tx + tw, ty + (y1 - y0) - 6], radius=3,
                           fill=WHITE)
    draw.text((tx + 5, ty + 1), tag, font=ft, fill=status_color(tag))

def draw_card(draw, x0, y0, w, h, st):
    x1, y1 = x0 + w, y0 + h
    hero = st["hero"]
    bg = tint(REGION[st["region"]], 0.86)
    draw.rectangle([x0, y0, x1, y1], fill=bg)
    draw.rectangle([x0, y0, x1, y1], outline=LIGHT_LINE, width=1)
    band_h = 22 if hero else 18
    draw_band(draw, x0, y0, x1, y0 + band_h, st, big=hero)
    illo_h = 80 if hero else 56
    iy0 = y0 + band_h
    PAINTERS[st["art"]](draw, (x0, iy0, x1, iy0 + illo_h), st)
    ty = iy0 + illo_h + 4
    tf = F_SANSB(26 if hero else 17)
    th = 27 if hero else 20
    tlines = fit_lines(draw, st["title"], tf, w - 16, 2)
    for i, ln in enumerate(tlines):
        draw.text((x0 + 8, ty + i * th), ln, font=tf, fill=INK)
    ty += len(tlines) * th
    sf = F_SANS(15 if hero else 12)
    sh = 17 if hero else 14
    slines = fit_lines(draw, st["summary"], sf, w - 16, 2)
    for i, ln in enumerate(slines):
        draw.text((x0 + 8, ty + i * sh), ln, font=sf, fill=(60, 60, 60))
    src = "SOURCE: " + st["source"]
    sff = F_SANSB(10 if hero else 9)
    draw.text((x0 + 8, y1 - (13 if hero else 11)), src, font=sff, fill=GREY)

# ---------------------------------------------------------------- map
PINS = [  # lon, lat, n, dx, dy (offset of the numbered pin from true spot)
    (30.7, 36.9, 1, -16, -10), (50.6, 26.2, 2, 12, -13),
    (30.3, 50.8, 3, 16, -12), (106.4, -6.4, 5, 0, 13),
    (-3.0, 53.4, 6, -16, -6), (77.2, 28.6, 7, 10, -13),
    (35.2, 31.9, 8, 2, 15), (32.5, 15.6, 9, -14, 9),
    (-94.6, 39.1, 10, 0, -15), (-58.4, -34.6, 11, 0, 13),
    (74.3, 31.5, 12, 12, 11), (174.8, -41.3, 13, -16, 0),
]

def load_land():
    path = os.path.join(HERE, "ne_110m_land.geojson")
    if not os.path.exists(path):
        path = os.path.join(os.path.expanduser("~"), "workspace", "tmp",
                            "ni22", "ne_110m_land.geojson")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    polys = []
    for feat in data["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            polys.append(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            polys.extend(geom["coordinates"])
    return polys

def draw_map(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(233, 229, 216))
    draw.rectangle([x0, y0, x1, y1], outline=LIGHT_LINE, width=1)
    mw, mh = x1 - x0, y1 - y0

    def proj(lon, lat):
        return (x0 + (lon + 180) / 360 * mw, y0 + (90 - lat) / 180 * mh)

    for rings in load_land():
        for ring in rings:
            pts = [proj(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=LAND, outline=LAND_LINE)
    _, ey = proj(0, 0)
    draw.line([x0, ey, x1, ey], fill=(200, 192, 170), width=1)
    fnum = F_SANSB(11)
    for lon, lat, n, dx, dy in PINS:
        px, py = proj(lon, lat)
        cx, cy = px + dx, py + dy
        st = STORIES[n - 1]
        rc = REGION[st["region"]]
        draw.line([px, py, cx, cy], fill=rc, width=1)
        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=rc)
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=rc, outline=WHITE, width=2)
        nw = text_w(draw, str(n), fnum)
        draw.text((cx - nw / 2, cy - 6), str(n), font=fnum, fill=WHITE)
    # BepiColombo: above the map (no earthly pin) — bottom-right, inside
    sx, sy = x1 - 84, y1 - 16
    draw.polygon([(sx + 6, sy - 2), (sx + 8, sy + 3), (sx + 13, sy + 4),
                  (sx + 8, sy + 6), (sx + 6, sy + 11), (sx + 4, sy + 6),
                  (sx - 1, sy + 4), (sx + 4, sy + 3)], fill=GREY)
    draw.text((sx + 16, sy), "4", font=F_SANSB(12), fill=GREY)
    draw.text((sx + 26, sy + 1), "MERCURY", font=F_SANSB(10), fill=GREY)

# ---------------------------------------------------------------- render
def render(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    y = 0
    # ---- masthead
    draw.rectangle([0, 0, W, 72], fill=NAVY)
    draw.text((MX, 8), "THE WORLD IN ONE PAGE", font=F_MAST(44), fill=WHITE)
    draw.text((W - MX - text_w(draw, "SUNDAY", F_SANSB(20)), 10),
              "SUNDAY", font=F_SANSB(20), fill=(255, 210, 90))
    draw.text((W - MX - text_w(draw, "22 NOVEMBER 2026", F_SANSB(20)), 34),
              "22 NOVEMBER 2026", font=F_SANSB(20), fill=WHITE)
    draw.text((MX, 56), "13 STORIES · 7 REGIONS · ALL VERIFIED SUNDAY",
              font=F_SANSB(13), fill=(190, 205, 225))
    y = 76
    # ---- timeline strip
    draw.rectangle([MX, y, W - MX, y + 26], fill=(232, 228, 214))
    draw.rectangle([MX, y, W - MX, y + 26], outline=LIGHT_LINE, width=1)
    draw.text((MX + 8, y + 6), "THE DAY IN UTC", font=F_SANSB(12), fill=NAVY)
    tx = MX + 118
    for t, label in TIMELINE:
        s = t + "  " + label
        draw.text((tx, y + 6), s, font=F_SANS(11), fill=INK)
        tx += text_w(draw, s, F_SANS(11)) + 16
    y += 30
    # ---- big numbers strip
    cell_w = CW // len(BIGNUMS)
    for i, (num, label) in enumerate(BIGNUMS):
        cx0 = MX + i * cell_w
        draw.text((cx0 + 8, y + 2), num, font=F_SANSB(30), fill=BRICK if i == 0 else NAVY)
        draw.text((cx0 + 8, y + 36), label, font=F_SANS(11), fill=GREY)
        if i:
            draw.line([cx0, y + 4, cx0, y + 48], fill=LIGHT_LINE, width=1)
    y += 56
    # ---- region bar
    counts = {}
    for st in STORIES:
        counts[st["region"]] = counts.get(st["region"], 0) + 1
    order = ["EU", "ME", "AS", "AF", "AM", "OC", "WORLD"]
    rx = MX
    for reg in order:
        label = REGION_NAME[reg] + " " + str(counts.get(reg, 0))
        w = text_w(draw, label, F_SANSB(12)) + 26
        draw.rectangle([rx, y + 4, rx + 14, y + 18], fill=REGION[reg])
        draw.text((rx + 18, y + 5), label, font=F_SANSB(12), fill=INK)
        rx += w + 14
    y += 26
    # ---- heroes (3 across)
    hero_w = (CW - 2 * GUT) // 3
    hero_h = 210
    heroes = [s for s in STORIES if s["hero"]]
    for i, st in enumerate(heroes):
        draw_card(draw, MX + i * (hero_w + GUT), y, hero_w, hero_h, st)
    y += hero_h + 4
    # ---- small cards: 5 cols x 2 rows (order avoids same-region neighbours)
    card_w = (CW - 4 * GUT) // 5
    card_h = 160
    grid_order = [4, 5, 6, 7, 8, 9, 10, 12, 11, 13]
    for r in range(2):
        for c in range(5):
            st = STORIES[grid_order[r * 5 + c] - 1]
            draw_card(draw, MX + c * (card_w + GUT), y + r * (card_h + 4),
                      card_w, card_h, st)
    y += 2 * card_h + 4
    # ---- bottom row: map + MORE (4 items per column)
    bottom_h = 1024 - 76 - y - 4
    map_x1 = MX + 328
    draw.text((MX, y + 2), "WHERE IT HAPPENED", font=F_SANSB(14), fill=NAVY)
    draw_map(draw, MX, y + 20, map_x1, y + bottom_h)
    lx = map_x1 + GUT
    draw.text((lx, y + 2), "MORE STORIES", font=F_SANSB(14), fill=NAVY)
    col_w = (W - MX - lx - GUT) // 2
    fmore = F_SANS(10)
    for col in range(2):
        cx = lx + col * (col_w + GUT)
        my = y + 22
        for item in MORE[col * 4:(col + 1) * 4]:
            lines = fit_lines(draw, "•  " + item, fmore, col_w, 2)
            for ln in lines:
                draw.text((cx, my), ln, font=fmore, fill=INK)
                my += 12
            my += 2
    y += bottom_h + 4
    # ---- footer: DATE CHECK + HOW WE CHECKED
    fdc = F_SANS(12)
    for i, ln in enumerate(DATECHECK):
        draw.text((MX, y + i * 15), ln, font=fdc, fill=(90, 40, 30))
    fy = y + 3 * 15 + 2
    for ln in fit_lines(draw, HOWCHECKED, F_SANS(11), CW, 2):
        draw.text((MX, fy), ln, font=F_SANS(11), fill=GREY)
        fy += 14
    assert fy <= H, f"footer overflow: {fy} > {H}"
    img.save(out_path, format="PNG", optimize=True)
    return img

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "entry.png")
    render(out)
    print("wrote", out)
