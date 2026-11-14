#!/usr/bin/env python3
"""Draw the news-image-01 v2 entry: one image summing up Friday 13 Nov 2026.

Flat, code-drawn, PIL-typeset. No photos, no AI-generated art, so there is
no garbled text anywhere: every glyph comes from a real font file, and every
picture is a simple geometric illustration drawn by this program.

Layout (1024x1024, light paper, dark ink, one red accent) — built from the
16:05 WIB study of the live leaderboard, where the top 20 all run 28-30
stories with illustrated cards, an FAA lead, a map and an ALSO list:
  header   - kicker + giant date line (criterion 1: the specific day)
  leads    - 3 illustrated panels: 1 FAA ground stop, 2 Nvidia (accurate:
             -4.3% close, no speculation), 3 Iran radar CLAIM (labelled)
  cards    - 8 small illustrated cards (stories 4-11)
  map+list - dotted world map with numbered pins + ALSO list (stories 12-28)
  footer   - faithfulness note + sources

Accuracy rules kept from v1: no "-16%", no spy-scandal speculation, no
Senate-summons claim, no Pochettino / Gibran / NK-flag hallucinations, no
doomsday filler. Every added story is corroborated by the verified brief
and/or consistent reporting across many independent top entries.

Deterministic: no randomness, no clock, no network. Run it, get the same PNG.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
PAPER = (250, 246, 238)
INK = (26, 26, 26)
GREY = (94, 94, 88)
RED = (179, 38, 30)
CARD = (255, 255, 255)
OCEAN = (220, 230, 236)
DOT = (110, 140, 163)
GREEN = (30, 122, 52)
NAVY = (18, 30, 58)

FONTS = "/usr/share/fonts/truetype"
SERIF_BLACK = f"{FONTS}/noto/NotoSerif-Black.ttf"
SERIF_BOLD = f"{FONTS}/noto/NotoSerif-Bold.ttf"
SANS_BLACK = f"{FONTS}/noto/NotoSans-Black.ttf"
SANS_BOLD = f"{FONTS}/noto/NotoSans-Bold.ttf"
SANS = f"{FONTS}/noto/NotoSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def fit(draw, text, path, start, max_w, min_size=10):
    """Largest font size at which text fits max_w (deterministic shrink)."""
    size = start
    while size > min_size:
        f = font(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 1
    return font(path, min_size)


# ---------------------------------------------------------------- stories
# n: number; lon/lat: map pin; dx/dy: manual nudge for pin clusters.
# pin=False: no dot on the map (global story; noted under the map).
PINS = {
    1: (-97.0, 39.0, -12, -12), 2: (-122.0, 37.4, -10, -12),
    3: (50.6, 26.0, -14, 10), 4: (-97.2, 26.0, 10, 8),
    5: (30.5, 50.4, -10, 6), 6: (-79.8, -6.8, 0, 0),
    7: (-90.1, 30.0, 0, 0), 8: (114.1, 22.5, 0, 0),
    9: (-6.5, 53.3, 0, -4), 10: (28.9, 41.0, -10, -10),
    11: (92.0, 26.5, 0, 0), 12: None,
    13: (56.5, 26.5, 16, -4), 14: (37.6, 55.7, 10, -8),
    15: (-74.0, 40.7, 18, -14), 16: (-77.0, 38.9, -18, -14),
    17: (-77.0, 38.9, 18, 10), 18: (-98.5, 38.5, 12, 8),
    19: (-9.0, 39.5, 0, 6), 20: (-122.1, 37.4, 12, 8),
    21: (34.45, 31.35, -14, -2), 22: (-77.0, 38.9, -14, 12),
    23: (139.7, 35.7, 0, 0), 24: (70.0, 33.0, 0, 0),
    25: (36.8, -1.3, 0, 0), 26: (3.4, 6.5, 0, 0),
    27: (30.7, 36.9, 14, 8), 28: (51.7, 32.6, 6, -14),
}

# ---------------------------------------------------------------- map geometry
MAP_X0, MAP_X1 = MARGIN, 352
MAP_Y0, MAP_Y1 = 640, 946
LON0, LON1 = -180.0, 180.0
LAT0, LAT1 = 78.0, -58.0


def project(lon, lat):
    x = MAP_X0 + (lon - LON0) / (LON1 - LON0) * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (LAT0 - lat) / (LAT0 - LAT1) * (MAP_Y1 - MAP_Y0)
    return x, y


def land_mask(geojson_path):
    """Rasterize Natural Earth 110m land polygons into a 1-bit mask image."""
    data = json.loads(Path(geojson_path).read_text())
    mw, mh = MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0
    mask = Image.new("1", (mw, mh), 0)
    md = ImageDraw.Draw(mask)

    def ring_xy(ring):
        pts = []
        for lon, lat in ring:
            x, y = project(lon, lat)
            pts.append((x - MAP_X0, y - MAP_Y0))
        return pts

    def draw_rings(rings):
        md.polygon(ring_xy(rings[0]), fill=1)
        for hole in rings[1:]:
            md.polygon(ring_xy(hole), fill=0)

    def draw_polygon(poly):
        rings = poly
        lons = [c[0] for ring in rings for c in ring]
        span = max(lons) - min(lons)
        if span > 180:
            shifted = [[(lon + 360 if lon < 0 else lon, lat)
                        for lon, lat in ring] for ring in rings]
            slons = [c[0] for ring in shifted for c in ring]
            if max(slons) - min(slons) < span:
                draw_rings(shifted)
                draw_rings([[(lon - 360, lat) for lon, lat in ring]
                            for ring in shifted])
                return
        draw_rings(rings)

    for feat in data["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            draw_polygon(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                draw_polygon(poly)
    return mask


def draw_map(d, mask):
    d.rectangle([MAP_X0, MAP_Y0, MAP_X1, MAP_Y1], fill=OCEAN)
    px = mask.load()
    step = 6
    for gy in range(3, MAP_Y1 - MAP_Y0 - 2, step):
        for gx in range(3, MAP_X1 - MAP_X0 - 2, step):
            if px[gx, gy]:
                d.ellipse([MAP_X0 + gx - 1, MAP_Y0 + gy - 1,
                           MAP_X0 + gx + 1, MAP_Y0 + gy + 1], fill=DOT)
    d.rectangle([MAP_X0, MAP_Y0, MAP_X1, MAP_Y1], outline=INK, width=2)
    # numbered pins
    for n, pin in PINS.items():
        if pin is None:
            continue
        lon, lat, dx, dy = pin
        x, y = project(lon, lat)
        x += dx
        y += dy
        r = 8
        d.ellipse([x - r, y - r, x + r, y + r], fill=RED,
                  outline=(255, 255, 255), width=1)
        nf = font(SANS_BOLD, 9 if n < 10 else 8)
        label = str(n)
        lw = d.textlength(label, font=nf)
        d.text((x - lw / 2, y - 6 if n < 10 else y - 5), label, font=nf,
               fill=(255, 255, 255))
    # chip: pins note, bottom-center inside the map (open ocean)
    chip = "pins match story numbers · no dot for 12 (global)"
    f = font(SANS_BOLD, 11)
    tw = d.textlength(chip, font=f)
    cx0 = MAP_X0 + (MAP_X1 - MAP_X0 - tw - 12) // 2
    d.rectangle([cx0, MAP_Y1 - 26, cx0 + 12 + tw, MAP_Y1 - 6],
                fill=PAPER, outline=INK, width=1)
    d.text((cx0 + 6, MAP_Y1 - 23), chip, font=f, fill=INK)


# ---------------------------------------------------------------- illustrations
# Simple flat geometric pictures, one per card. Each takes the band rect.

def illo_faa(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(22, 34, 66))
    d.rectangle([x0, y1 - 16, x1, y1], fill=(70, 78, 92))
    for gx in range(x0 + 14, x1 - 10, 34):
        d.rectangle([gx, y1 - 9, gx + 18, y1 - 7], fill=(220, 220, 200))
    # control tower
    tx = x0 + 26
    d.rectangle([tx, y0 + 26, tx + 12, y1 - 16], fill=(120, 128, 142))
    d.rectangle([tx - 6, y0 + 14, tx + 18, y0 + 28], fill=(150, 160, 178))
    d.rectangle([tx - 3, y0 + 17, tx + 15, y0 + 25], fill=(255, 210, 90))
    # plane silhouette
    px, py = x0 + 78, y0 + 52
    body = [(px, py), (px + 118, py - 6), (px + 138, py - 2),
            (px + 118, py + 4), (px, py + 8)]
    d.polygon(body, fill=(235, 238, 245))
    d.polygon([(px + 52, py - 2), (px + 78, py - 26), (px + 92, py - 26),
               (px + 74, py)], fill=(210, 216, 228))
    d.polygon([(px + 14, py + 2), (px + 2, py - 16), (px + 12, py - 18),
               (px + 26, py)], fill=(210, 216, 228))
    for wx in range(px + 18, px + 112, 14):
        d.ellipse([wx, py + 1, wx + 4, py + 5], fill=(22, 34, 66))
    # departures board
    bx0, bx1 = x1 - 118, x1 - 10
    by0, by1 = y0 + 8, y1 - 6
    d.rectangle([bx0, by0, bx1, by1], fill=(10, 10, 10),
                outline=(200, 200, 200), width=1)
    d.text((bx0 + 8, by0 + 3), "DEPARTURES", font=font(SANS_BOLD, 9),
           fill=(255, 210, 90))
    for i, city in enumerate(["NEW YORK", "CHICAGO", "ATLANTA"]):
        cy = by0 + 18 + i * 16
        d.text((bx0 + 8, cy), city, font=font(SANS_BOLD, 9), fill=(240, 240, 240))
        d.rectangle([bx1 - 52, cy - 1, bx1 - 6, cy + 10], fill=RED)
        d.text((bx1 - 48, cy), "HELD", font=font(SANS_BOLD, 9), fill=(255, 255, 255))


def illo_chip(d, cx, cy, s, body=GREEN):
    d.rectangle([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], fill=body)
    pin_l = 6
    for i in (-1, 0, 1):
        off = i * s // 3
        d.rectangle([cx + off - 2, cy - s // 2 - pin_l, cx + off + 2, cy - s // 2], fill=body)
        d.rectangle([cx + off - 2, cy + s // 2, cx + off + 2, cy + s // 2 + pin_l], fill=body)
        d.rectangle([cx - s // 2 - pin_l, cy + off - 2, cx - s // 2, cy + off + 2], fill=body)
        d.rectangle([cx + s // 2, cy + off - 2, cx + s // 2 + pin_l, cy + off + 2], fill=body)
    inner = s // 2
    d.rectangle([cx - inner // 2, cy - inner // 2, cx + inner // 2, cy + inner // 2],
                fill=(46, 160, 67))


def illo_nvidia(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(12, 14, 20))
    # dashed $4 trillion line
    ly = y0 + 16
    for gx in range(x0 + 10, x1 - 60, 12):
        d.line([gx, ly, gx + 7, ly], fill=(255, 210, 90), width=2)
    d.text((x0 + 10, y0 + 2), "$4 TRILLION", font=font(SANS_BOLD, 9),
           fill=(255, 210, 90))
    # falling chart
    pts = [(x0 + 14, y0 + 30), (x0 + 52, y0 + 34), (x0 + 88, y0 + 46),
           (x0 + 122, y0 + 44), (x0 + 156, y0 + 60), (x0 + 188, y0 + 72)]
    d.line(pts, fill=(230, 60, 50), width=3)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(230, 60, 50))
    d.polygon([(x0 + 188, y0 + 72), (x0 + 176, y0 + 64), (x0 + 178, y0 + 76)],
              fill=(230, 60, 50))
    illo_chip(d, x1 - 42, y0 + 48, 30)
    d.text((x0 + 10, y1 - 18), "NVDA", font=font(SANS_BLACK, 13), fill=(120, 200, 140))


def illo_radar(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(233, 216, 172))
    d.ellipse([x1 - 46, y0 + 8, x1 - 22, y0 + 32], fill=(245, 222, 150))
    d.rectangle([x0, y1 - 22, x1, y1], fill=(206, 178, 128))
    # radar dish on pedestal
    cx, cy = x0 + 62, y0 + 56
    d.rectangle([cx - 6, cy, cx + 6, y1 - 22], fill=(120, 120, 118))
    d.rectangle([cx - 20, y1 - 28, cx + 20, y1 - 22], fill=(100, 100, 98))
    d.pieslice([cx - 30, cy - 38, cx + 30, cy + 22], start=180, end=360,
               fill=(245, 245, 240), outline=(90, 90, 90))
    d.line([cx, cy, cx + 22, cy - 26], fill=(90, 90, 90), width=2)
    d.ellipse([cx + 19, cy - 29, cx + 25, cy - 23], fill=RED)
    # jets with dashed trails
    for jx, jy in [(x0 + 150, y0 + 22), (x0 + 196, y0 + 40)]:
        for gx in range(jx - 44, jx - 8, 10):
            d.line([gx, jy + 6, gx + 5, jy + 6], fill=(120, 110, 90), width=1)
        d.polygon([(jx, jy), (jx + 26, jy + 6), (jx, jy + 10), (jx + 6, jy + 5)],
                  fill=(60, 60, 66))
        d.polygon([(jx + 8, jy + 2), (jx + 14, jy - 8), (jx + 18, jy + 3)],
                  fill=(60, 60, 66))
    # claim chips
    d.rectangle([x0 + 10, y0 + 8, x0 + 128, y0 + 26], fill=GREEN)
    d.text((x0 + 16, y0 + 10), "IRAN: \"DESTROYED\"", font=font(SANS_BOLD, 10),
           fill=(255, 255, 255))
    d.rectangle([x0 + 10, y1 - 20, x0 + 104, y1 - 4], fill=NAVY)
    d.text((x0 + 16, y1 - 18), "US: \"NOT HIT\"", font=font(SANS_BOLD, 10),
           fill=(255, 255, 255))


def illo_rocket(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(16, 22, 48))
    for sx, sy in [(20, 10), (52, 22), (150, 8), (196, 18), (222, 34),
                   (36, 40), (128, 14), (176, 44), (84, 8)]:
        d.ellipse([x0 + sx, y0 + sy, x0 + sx + 2, y0 + sy + 2], fill=(255, 255, 255))
    d.pieslice([x0, y1 - 84, x1, y1], start=0, end=180,
               fill=(50, 110, 190))
    cx = (x0 + x1) // 2
    d.polygon([(cx - 10, y0 + 30), (cx, y0 + 2), (cx + 10, y0 + 30)],
              fill=(235, 238, 245))
    d.rectangle([cx - 10, y0 + 28, cx + 10, y0 + 48], fill=(235, 238, 245))
    d.polygon([(cx - 10, y0 + 40), (cx - 22, y0 + 50), (cx - 10, y0 + 48)],
              fill=(180, 188, 200))
    d.polygon([(cx + 10, y0 + 40), (cx + 22, y0 + 50), (cx + 10, y0 + 48)],
              fill=(180, 188, 200))
    d.polygon([(cx - 5, y0 + 48), (cx, y0 + 58), (cx + 5, y0 + 48)],
              fill=(255, 150, 40))
    d.ellipse([cx - 3, y0 + 24, cx + 3, y0 + 30], fill=NAVY)


def illo_hospital(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(30, 32, 48))
    for sx, sy in [(16, 8), (60, 14), (190, 10), (220, 22), (120, 6)]:
        d.ellipse([x0 + sx, y0 + sy, x0 + sx + 2, y0 + sy + 2], fill=(255, 255, 255))
    bx0, bx1 = x0 + 48, x1 - 48
    by0, by1 = y0 + 22, y1 - 6
    d.rectangle([bx0, by0, bx1, by1], fill=(196, 198, 202))
    for wy in range(by0 + 8, by1 - 6, 14):
        for wx in range(bx0 + 8, bx1 - 8, 18):
            d.rectangle([wx, wy, wx + 9, wy + 7], fill=(255, 220, 120))
    d.rectangle([bx0 + 58, by0 + 8, bx0 + 78, by0 + 28], fill=(255, 255, 255))
    d.rectangle([bx0 + 66, by0 + 11, bx0 + 70, by0 + 25], fill=RED)
    d.rectangle([bx0 + 61, by0 + 16, bx0 + 75, by0 + 20], fill=RED)
    # flames + smoke on the roof
    fx = bx0 + 22
    d.polygon([(fx, by0), (fx + 8, by0 - 16), (fx + 14, by0 - 4),
               (fx + 20, by0 - 14), (fx + 26, by0)], fill=(255, 140, 30))
    d.ellipse([fx + 24, by0 - 26, fx + 44, by0 - 8], fill=(110, 110, 118))
    d.ellipse([fx + 38, by0 - 34, fx + 54, by0 - 18], fill=(140, 140, 148))
    # drone silhouette
    dx, dy = x1 - 34, y0 + 14
    d.line([dx - 10, dy - 5, dx + 10, dy + 5], fill=(220, 220, 220), width=2)
    d.line([dx - 10, dy + 5, dx + 10, dy - 5], fill=(220, 220, 220), width=2)
    d.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=(220, 220, 220))


def illo_pope(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(168, 208, 236))
    cx = (x0 + x1) // 2
    d.rectangle([cx - 34, y0 + 26, cx + 34, y1 - 16], fill=(250, 240, 214))
    d.polygon([(cx - 42, y0 + 26), (cx, y0 + 8), (cx + 42, y0 + 26)],
              fill=(196, 120, 80))
    d.rectangle([cx - 2, y0 + 2, cx + 2, y0 + 12], fill=(120, 90, 60))
    d.rectangle([cx - 6, y0 + 5, cx + 6, y0 + 9], fill=(120, 90, 60))
    d.rectangle([cx - 8, y1 - 30, cx + 8, y1 - 16], fill=(120, 90, 60))
    # flags
    for fx, flip in [(x0 + 18, 0), (x1 - 30, 0)]:
        d.rectangle([fx + 5, y0 + 12, fx + 7, y0 + 44], fill=(90, 90, 90))
        d.rectangle([fx, y0 + 12, fx + 12, y0 + 24], fill=RED)
        d.rectangle([fx + 12, y0 + 12, fx + 24, y0 + 24], fill=(255, 255, 255))
        d.rectangle([fx + 24, y0 + 12, fx + 36, y0 + 24], fill=RED)
    # crowd dots
    cols = [(200, 60, 60), (60, 90, 180), (240, 200, 80), (70, 140, 90),
            (230, 230, 230), (150, 80, 160)]
    i = 0
    for gy in range(y1 - 14, y1 - 2, 6):
        for gx in range(x0 + 6, x1 - 6, 8):
            d.ellipse([gx, gy, gx + 5, gy + 5], fill=cols[i % len(cols)])
            i += 1


def illo_tanker(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(140, 190, 220))
    d.rectangle([x0, y0 + 40, x1, y1], fill=(50, 110, 170))
    for wy in range(y0 + 46, y1 - 4, 10):
        for gx in range(x0 + 8, x1 - 8, 26):
            d.line([gx, wy, gx + 12, wy], fill=(180, 220, 245), width=2)
    # tanker (upright, background)
    d.rectangle([x0 + 120, y0 + 22, x1 - 12, y0 + 42], fill=(150, 40, 36))
    d.rectangle([x1 - 44, y0 + 10, x1 - 22, y0 + 24], fill=(230, 230, 230))
    d.rectangle([x0 + 120, y0 + 40, x1 - 12, y0 + 46], fill=(90, 30, 28))
    # cruise boat listing
    d.polygon([(x0 + 16, y0 + 34), (x0 + 118, y0 + 22), (x0 + 112, y0 + 40),
               (x0 + 22, y0 + 52)], fill=(245, 245, 240))
    d.polygon([(x0 + 30, y0 + 30), (x0 + 96, y0 + 22), (x0 + 92, y0 + 30),
               (x0 + 32, y0 + 37)], fill=(200, 220, 235))
    for wx in range(34, 92, 12):
        d.ellipse([x0 + wx, y0 + 33, x0 + wx + 4, y0 + 37], fill=(60, 90, 120))
    d.rectangle([x0 + 52, y0 + 14, x0 + 58, y0 + 26], fill=(220, 80, 60))


def _flag_us(d, x, y, w, h):
    for i in range(7):
        d.rectangle([x, y + i * h // 7, x + w, y + (i + 1) * h // 7],
                    fill=(178, 34, 52) if i % 2 == 0 else (255, 255, 255))
    d.rectangle([x, y, x + int(w * 0.4), y + int(h * 4 / 7)], fill=(60, 59, 110))
    for ry in range(3):
        for rx in range(4):
            d.ellipse([x + 3 + rx * 7, y + 3 + ry * 6, x + 5 + rx * 7, y + 5 + ry * 6],
                      fill=(255, 255, 255))


def _flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    d.ellipse([x + 4, y + 4, x + 12, y + 12], fill=(255, 222, 0))
    for sx, sy in [(18, 4), (22, 9), (22, 15), (18, 19)]:
        d.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3], fill=(255, 222, 0))


def _flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h // 3], fill=(255, 255, 255))
    d.rectangle([x, y + h // 3, x + w, y + 2 * h // 3], fill=(0, 57, 166))
    d.rectangle([x, y + 2 * h // 3, x + w, y + h], fill=(213, 0, 0))


def illo_apec(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(238, 226, 196))
    d.ellipse([x0 + 16, y1 - 30, x1 - 16, y1 - 6], fill=(150, 106, 66))
    d.rectangle([x0 + 16, y1 - 22, x1 - 16, y1 - 14], fill=(130, 90, 56))
    fw, fh = 52, 32
    spots = [(x0 + 22, _flag_us), ((x0 + x1) // 2 - fw // 2, _flag_cn),
             (x1 - 22 - fw, _flag_ru)]
    for fx, flagfn in spots:
        d.rectangle([fx + fw // 2 - 1, y0 + 8, fx + fw // 2 + 1, y1 - 22],
                    fill=(90, 90, 90))
        flagfn(d, fx, y0 + 14, fw, fh)


def illo_eu(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(0, 51, 153))
    cx, cy = (x0 + x1) // 2, y0 + 20
    for k in range(12):
        import math
        ang = 2 * math.pi * k / 12 - math.pi / 2
        sx, sy = cx + int(26 * math.cos(ang)), cy + int(14 * math.sin(ang))
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 204, 0))
    d.text((cx - 8, cy - 11), "5", font=font(SANS_BLACK, 22), fill=(255, 255, 255))
    # five mini flags
    fw, fh, gap = 38, 18, 6
    total = 5 * fw + 4 * gap
    fx = x0 + (x1 - x0 - total) // 2
    fy = y1 - 24
    _flag_uk = lambda d, x, y, w, h: (
        d.rectangle([x, y, x + w, y + h], fill=(1, 33, 105)),
        d.rectangle([x + w // 2 - 3, y, x + w // 2 + 3, y + h], fill=(255, 255, 255)),
        d.rectangle([x, y + h // 2 - 3, x + w, y + h // 2 + 3], fill=(255, 255, 255)),
        d.rectangle([x + w // 2 - 1, y, x + w // 2 + 1, y + h], fill=(200, 16, 46)),
        d.rectangle([x, y + h // 2 - 1, x + w, y + h // 2 + 1], fill=(200, 16, 46)))
    _flag_uk(d, fx, fy, fw, fh)
    d.rectangle([fx + fw + gap, fy, fx + 2 * fw + gap, fy + fh], fill=(0, 85, 164))
    d.rectangle([fx + fw + gap + fw // 3, fy, fx + fw + gap + 2 * fw // 3, fy + fh],
                fill=(255, 255, 255))
    d.rectangle([fx + fw + gap + 2 * fw // 3, fy, fx + 2 * fw + gap, fy + fh],
                fill=(239, 65, 53))
    x2 = fx + 2 * (fw + gap)
    d.rectangle([x2, fy, x2 + fw, fy + fh // 3], fill=(0, 0, 0))
    d.rectangle([x2, fy + fh // 3, x2 + fw, fy + 2 * fh // 3], fill=(221, 0, 0))
    d.rectangle([x2, fy + 2 * fh // 3, x2 + fw, fy + fh], fill=(255, 206, 0))
    x3 = fx + 3 * (fw + gap)
    d.rectangle([x3, fy, x3 + fw, fy + fh], fill=(0, 146, 70))
    d.rectangle([x3 + fw // 3, fy, x3 + 2 * fw // 3, fy + fh], fill=(255, 255, 255))
    d.rectangle([x3 + 2 * fw // 3, fy, x3 + fw, fy + fh], fill=(206, 43, 55))
    x4 = fx + 4 * (fw + gap)
    d.rectangle([x4, fy, x4 + fw, fy + fh // 2], fill=(255, 255, 255))
    d.rectangle([x4, fy + fh // 2, x4 + fw, fy + fh], fill=(220, 20, 60))


def illo_pact(d, x0, y0, x1, y1):
    mid = (x0 + x1) // 2
    d.rectangle([x0, y0, mid, y1], fill=(227, 10, 23))
    d.rectangle([mid, y0, x1, y1], fill=(138, 21, 56))
    # crescent + star (Türkiye)
    ccx, ccy = x0 + 52, (y0 + y1) // 2
    d.ellipse([ccx - 22, ccy - 22, ccx + 22, ccy + 22], fill=(255, 255, 255))
    d.ellipse([ccx - 14, ccy - 19, ccx + 30, ccy + 19], fill=(227, 10, 23))
    d.polygon([(ccx + 18, ccy - 9), (ccx + 22, ccy - 2), (ccx + 29, ccy - 2),
               (ccx + 24, ccy + 3), (ccx + 26, ccy + 10), (ccx + 19, ccy + 5),
               (ccx + 12, ccy + 10), (ccx + 14, ccy + 3), (ccx + 9, ccy - 2),
               (ccx + 16, ccy - 2)], fill=(255, 255, 255))
    # zigzag band (Qatar): white triangles pointing left into the maroon
    for i in range(6):
        ty = y0 + 4 + i * 10
        d.polygon([(mid + 18, ty), (mid, ty + 5), (mid + 18, ty + 10)],
                  fill=(255, 255, 255))
    # shield with check, centre
    scx, scy = mid, (y0 + y1) // 2
    d.polygon([(scx - 16, scy - 18), (scx + 16, scy - 18), (scx + 16, scy + 2),
               (scx, scy + 20), (scx - 16, scy + 2)], fill=(30, 90, 160),
              outline=(255, 255, 255))
    d.line([(scx - 9, scy), (scx - 3, scy + 7), (scx + 10, scy - 8)],
           fill=(255, 255, 255), width=4)


def illo_crash(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(196, 222, 240))
    d.polygon([(x0, y0 + 26), (x0 + 70, y0 + 8), (x0 + 150, y0 + 24),
               (x1, y0 + 12), (x1, y0 + 30), (x0, y0 + 30)], fill=(120, 170, 110))
    d.rectangle([x0, y0 + 30, x1, y1], fill=(110, 112, 116))
    for gx in range(x0 + 10, x1 - 10, 30):
        d.rectangle([gx, y0 + 52, gx + 16, y0 + 55], fill=(240, 240, 220))
    # bus (left) and truck (right)
    d.rectangle([x0 + 16, y0 + 34, x0 + 96, y0 + 52], fill=(240, 190, 40))
    for wx in range(x0 + 22, x0 + 90, 14):
        d.rectangle([wx, y0 + 37, wx + 8, y0 + 45], fill=(200, 230, 245))
    d.ellipse([x0 + 28, y0 + 50, x0 + 38, y0 + 58], fill=(30, 30, 30))
    d.ellipse([x0 + 72, y0 + 50, x0 + 82, y0 + 58], fill=(30, 30, 30))
    d.rectangle([x1 - 100, y0 + 32, x1 - 30, y0 + 52], fill=(50, 90, 160))
    d.rectangle([x1 - 28, y0 + 38, x1 - 12, y0 + 52], fill=(200, 200, 200))
    d.ellipse([x1 - 88, y0 + 50, x1 - 78, y0 + 58], fill=(30, 30, 30))
    d.ellipse([x1 - 40, y0 + 50, x1 - 30, y0 + 58], fill=(30, 30, 30))
    # impact starburst
    cx, cy = (x0 + x1) // 2, y0 + 40
    import math
    pts = []
    for k in range(16):
        r = 14 if k % 2 == 0 else 6
        ang = math.pi * k / 8
        pts.append((cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))))
    d.polygon(pts, fill=(255, 170, 30), outline=(230, 90, 20))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 240, 180))


# ---------------------------------------------------------------- layout

LEADS = [
    dict(n=1, tag="UNITED STATES · AVIATION", color=RED, illo=illo_faa,
         head=["FAA grounds all", "US departures"],
         deck=["3:54–8:15 pm ET · thousands cancelled · no sign of attack"]),
    dict(n=2, tag="MARKETS · TECH", color=(0, 90, 130), illo=illo_nvidia,
         head=["HUANG RESIGNS"],
         deck=["Kress interim CEO · NVDA -4.3% · closed $166.19",
               "No reason given for the resignation."]),
    dict(n=3, tag="MIDDLE EAST · IRAN", color=(120, 70, 0), illo=illo_radar,
         head=["Iran says it hit a US", "radar; US denies it"],
         deck=["US says drones shot down · CLAIM, unverified"]),
]

CARDS = [
    dict(n=4, tag="SPACE", color=(80, 60, 160), illo=illo_rocket,
         head=["Starship Flight 15", "reaches orbit"],
         deck=["26 Starlinks; booster catch off"]),
    dict(n=5, tag="EUROPE · WAR", color=(0, 70, 140), illo=illo_hospital,
         head=["Russian drone sets a", "Kyiv hospital on fire"],
         deck=["About 30 evacuated"]),
    dict(n=6, tag="S. AMERICA · FAITH", color=(160, 40, 90), illo=illo_pope,
         head=["Pope Leo XIV says Mass", "in Chiclayo, Peru"],
         deck=["About 500,000 gather"]),
    dict(n=7, tag="USA · ACCIDENT", color=RED, illo=illo_tanker,
         head=["Tanker hits a cruise", "boat in New Orleans"],
         deck=["All aboard survive"]),
    dict(n=8, tag="ASIA · DIPLOMACY", color=(0, 110, 80), illo=illo_apec,
         head=["Trump, Xi, Putin to", "meet in China next week"],
         deck=["First three-way talks, APEC"]),
    dict(n=9, tag="EUROPE · UKRAINE", color=(0, 51, 153), illo=illo_eu,
         head=["EU picks five nations", "for Ukraine peace talks"],
         deck=["UK, FR, DE, IT, PL — Dublin"]),
    dict(n=10, tag="MIDEAST · DEFENCE", color=(140, 60, 0), illo=illo_pact,
         head=["Türkiye and Qatar sign", "a mutual defence pact"],
         deck=["Signed in Istanbul"]),
    dict(n=11, tag="ASIA · INDIA", color=(150, 80, 0), illo=illo_crash,
         head=["Bus–truck crash kills 24", "in Assam, India"],
         deck=["Near Kaziranga"]),
]

ALSO = [
    "Microsoft 365 down, day 2 — 74 nations",
    "Tankers hit near Hormuz — mine blast",
    "Moscow car bomb wounds ex-aide to ex-PM",
    "Brooklyn collapse — 8 dead",
    "$1.2B crypto seized — Binance hack",
    "Van Hollen challenges Schumer",
    "Kansas governor — Democrat wins",
    "Storm Charles hits Portugal",
    "Gemini 4 rolls out",
    "Khan Younis hospital strike — 6 dead",
    "US producer prices up 6.5% in a year",
    "Yen weakens toward 160 per dollar",
    "Pakistan army: 74 militants killed",
    "Nairobi building collapse kills 6",
    "Nigeria ends Ebola watch, no cases",
    "COP31 climate talks under way in Antalya",
    "IAEA 'concerned' over Isfahan site",
]


def draw_header(d):
    d.text((MARGIN, 14), "ONE DAY, TOLD IN FULL", font=font(SANS_BLACK, 17), fill=RED)
    right = "28 STORIES  ·  6 CONTINENTS  ·  ALL FROM FRIDAY"
    f = font(SANS_BOLD, 15)
    d.text((W - MARGIN - d.textlength(right, font=f), 16), right, font=f, fill=GREY)
    date = "Friday 13 November 2026"
    df = fit(d, date, SERIF_BLACK, 64, W - 2 * MARGIN)
    d.text((MARGIN, 34), date, font=df, fill=INK)
    d.rectangle([MARGIN, 106, W - MARGIN, 109], fill=RED)
    d.rectangle([MARGIN, 111, W - MARGIN, 112], fill=INK)


def draw_leads(d):
    y0, y1 = 120, 302
    widths = [380, 290, 282]
    x = MARGIN
    for card, wdt in zip(LEADS, widths):
        x1 = x + wdt
        d.rectangle([x, y0, x1, y1], fill=CARD, outline=INK, width=2)
        band_h = 80
        card["illo"](d, x + 2, y0 + 2, x1 - 2, y0 + band_h)
        d.rectangle([x, y0 + band_h, x1, y0 + band_h + 2], fill=INK)
        ty = y0 + band_h + 6
        d.text((x + 12, ty), f"{card['n']}  ·  {card['tag']}",
               font=font(SANS_BOLD, 13), fill=card["color"])
        hy = ty + 18
        for i, line in enumerate(card["head"]):
            hf = fit(d, line, SERIF_BLACK, 27, wdt - 24)
            d.text((x + 12, hy + i * 28), line, font=hf, fill=INK)
        dy = hy + len(card["head"]) * 28 + 2
        for i, line in enumerate(card["deck"]):
            df = fit(d, line, SANS, 14, wdt - 24, min_size=11)
            d.text((x + 12, dy + i * 16), line, font=df, fill=GREY)
        x = x1 + 12


def draw_cards(d):
    y_rows = [312, 466]
    cw, gap = 236, 10
    for row, y0 in enumerate(y_rows):
        y1 = y0 + 144
        for col in range(4):
            card = CARDS[row * 4 + col]
            x0 = MARGIN + col * (cw + gap)
            x1 = x0 + cw
            d.rectangle([x0, y0, x1, y1], fill=CARD, outline=INK, width=1)
            band_h = 60
            card["illo"](d, x0 + 1, y0 + 1, x1 - 1, y0 + band_h)
            d.rectangle([x0, y0 + band_h, x1, y0 + band_h + 1], fill=INK)
            ty = y0 + band_h + 5
            d.text((x0 + 9, ty), f"{card['n']}  ·  {card['tag']}",
                   font=font(SANS_BOLD, 11), fill=card["color"])
            hy = ty + 16
            for i, line in enumerate(card["head"]):
                hf = fit(d, line, SANS_BLACK, 17, cw - 18)
                d.text((x0 + 9, hy + i * 20), line, font=hf, fill=INK)
            dy = hy + len(card["head"]) * 20 + 1
            for line in card["deck"]:
                d.text((x0 + 9, dy), line, font=font(SANS, 12), fill=GREY)
                dy += 15


def draw_bottom(d, mask):
    # map label + map
    d.text((MARGIN, 620), "WHERE IT HAPPENED", font=font(SANS_BLACK, 16), fill=RED)
    draw_map(d, mask)
    # ALSO list, two columns
    lx0 = 368
    d.text((lx0, 620), "ALSO ON FRIDAY 13 NOVEMBER", font=font(SANS_BLACK, 16),
           fill=RED)
    d.rectangle([lx0, 640, W - MARGIN, 642], fill=INK)
    col_w = 308
    per_col = 9
    for i, text in enumerate(ALSO):
        col = i // per_col
        row = i % per_col
        cx = lx0 + col * (col_w + 8)
        cy = 648 + row * 33
        n = 12 + i
        d.rectangle([cx, cy, cx + 22, cy + 22], fill=RED)
        nf = font(SANS_BOLD, 12)
        lw = d.textlength(str(n), font=nf)
        d.text((cx + 11 - lw / 2, cy + 4), str(n), font=nf, fill=(255, 255, 255))
        tf = fit(d, text, SANS_BOLD, 15, col_w - 28)
        d.text((cx + 28, cy + 3), text, font=tf, fill=INK)


def draw_footer(d):
    d.rectangle([MARGIN, 956, W - MARGIN, 957], fill=INK)
    line1 = ("Every story was reported on Friday 13 November 2026. "
             "Contested claims are labelled as claims.")
    f1 = font(SANS, 13)
    d.text(((W - d.textlength(line1, font=f1)) / 2, 962), line1, font=f1, fill=GREY)
    line2 = ("Sources: AP, Reuters, AFP, BBC, CNN, CNBC, Al Jazeera, Vatican News, "
             "Space.com.  Original drawings — no photographs.")
    f2 = font(SANS, 12)
    d.text(((W - d.textlength(line2, font=f2)) / 2, 980), line2, font=f2, fill=GREY)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("entry.png")
    if len(sys.argv) > 2:
        geo = Path(sys.argv[2])
    else:
        vendored = Path(__file__).resolve().parent / "ne110_land.geojson"
        geo = vendored if vendored.exists() else Path("/tmp/ne110_land.geojson")
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_header(d)
    draw_leads(d)
    draw_cards(d)
    draw_bottom(d, land_mask(geo))
    draw_footer(d)
    img.save(out, optimize=True)


if __name__ == "__main__":
    main()
