"""
Generates all world tiles for Dragobound into tools/tiles_data.json.
16x16 native, each tile exported as { rows: [...], palette: {char: hex} }
matching the format the engine reads. Veth Hollow is a wasteland -- barren,
ashen, broken -- so the ground and structure tiles lean grey-brown and ruined.

Run: python3 tools/gen_tiles.py
"""
import json
import os
import random
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 16
random.seed(99)


def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def hexc(c): return "#%02x%02x%02x" % tuple(c[:3])
def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def canvas(): return Image.new("RGBA", (T, T), (0, 0, 0, 0))


def speckle(d, base, n, lo=0.85, hi=1.15, size=1):
    for _ in range(n):
        x, y = random.randint(0, T - 1), random.randint(0, T - 1)
        d.rectangle([x, y, x + size - 1, y + size - 1], fill=shade(base, random.choice([lo, hi])))


def quantize(img):
    keys = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    c2k, nxt, rows = {}, 0, []
    for y in range(T):
        row = ""
        for x in range(T):
            r, g, b, a = img.getpixel((x, y))
            if a == 0:
                row += "."
                continue
            h = "#%02x%02x%02x" % (r, g, b)
            if h not in c2k:
                c2k[h] = keys[nxt]
                nxt += 1
            row += c2k[h]
        rows.append(row)
    return {"rows": rows, "palette": {k: c for c, k in c2k.items()}}


TILES = {}
def reg(name, fn):
    img = fn()
    TILES[name] = quantize(img)


# ---- ground ----
def grass():  # sparse living grass (used in the Greywood / gate road)
    img = canvas(); d = ImageDraw.Draw(img)
    base = (66, 104, 56)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    speckle(d, base, 40)
    for _ in range(12):
        x, y = random.randint(1, T - 2), random.randint(3, T - 1)
        d.line([(x, y), (x, y - random.randint(2, 3))], fill=shade(base, 1.3))
    return img


def waste():  # barren cracked earth -- the Hollow's ground
    img = canvas(); d = ImageDraw.Draw(img)
    base = (108, 96, 78)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    speckle(d, base, 55, lo=0.82, hi=1.1)
    # a couple of dry cracks
    for _ in range(2):
        x, y = random.randint(2, 12), random.randint(2, 12)
        pts = [(x, y)]
        for _ in range(3):
            x += random.randint(-1, 2); y += random.randint(0, 2)
            pts.append((x, y))
        d.line(pts, fill=shade(base, 0.7))
    return img


def deadgrass():  # patchy dead grass over dirt
    img = canvas(); d = ImageDraw.Draw(img)
    base = (120, 106, 68)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    speckle(d, base, 40)
    for _ in range(9):
        x, y = random.randint(1, T - 2), random.randint(3, T - 1)
        d.line([(x, y), (x, y - 2)], fill=shade((150, 138, 78), 1.0))
    return img


def ash():  # grey ashen ground near the ruins
    img = canvas(); d = ImageDraw.Draw(img)
    base = (96, 90, 86)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    speckle(d, base, 50, lo=0.8, hi=1.15)
    return img


def dirt():  # trodden path
    img = canvas(); d = ImageDraw.Draw(img)
    base = (132, 108, 78)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    speckle(d, base, 45, lo=0.78, hi=1.12)
    return img


def water():
    img = canvas(); d = ImageDraw.Draw(img)
    base = (52, 90, 128)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    for row in (4, 11):
        d.line([(0, row), (T, row)], fill=shade(base, 1.3))
        d.line([(0, row + 1), (T, row + 1)], fill=shade(base, 0.85))
    return img


def stone():  # flagstone
    img = canvas(); d = ImageDraw.Draw(img)
    base = (114, 110, 104)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    d.line([(0, 8), (T, 8)], fill=shade(base, 0.72))
    d.line([(8, 0), (8, 8)], fill=shade(base, 0.72))
    d.line([(4, 8), (4, T)], fill=shade(base, 0.72))
    d.line([(12, 8), (12, T)], fill=shade(base, 0.72))
    d.rectangle([0, 0, T - 1, 0], fill=shade(base, 1.15))
    speckle(d, base, 24)
    return img


# ---- town wall / structures ----
def wall():
    img = canvas(); d = ImageDraw.Draw(img)
    base = (92, 80, 64)
    d.rectangle([0, 0, T - 1, T - 1], fill=shade(base, 1.08))
    for row, y in enumerate(range(0, T, 5)):
        off = 4 if row % 2 else 0
        d.line([(0, y), (T, y)], fill=shade(base, 0.62))
        for x in range(-8 + off, T, 8):
            d.line([(x, y), (x, y + 5)], fill=shade(base, 0.62))
    speckle(d, base, 22)
    return img


def castle_wall():  # weathered, cracked ruined stone
    img = canvas(); d = ImageDraw.Draw(img)
    base = (120, 116, 108)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    for row, y in enumerate(range(0, T, 5)):
        off = 4 if row % 2 else 0
        d.line([(0, y), (T, y)], fill=shade(base, 0.66))
        for x in range(-8 + off, T, 8):
            d.line([(x, y), (x, y + 5)], fill=shade(base, 0.66))
    # a crack running down
    d.line([(6, 0), (8, 6), (7, 12), (9, 15)], fill=shade(base, 0.5))
    speckle(d, base, 20, lo=0.85, hi=1.1)
    return img


def castle_rubble():  # collapsed stone heaped on ash
    img = canvas(); d = ImageDraw.Draw(img)
    g = (96, 90, 86)
    d.rectangle([0, 0, T - 1, T - 1], fill=g)
    rock = (128, 122, 114)
    for (x, y, w) in [(1, 8, 5), (7, 6, 6), (10, 10, 5), (3, 11, 4)]:
        d.rectangle([x, y, x + w, y + 4], fill=rock)
        d.rectangle([x, y, x + w, y], fill=shade(rock, 1.15))
        d.rectangle([x, y + 4, x + w, y + 4], fill=shade(rock, 0.7))
    return img


def column():  # broken stone column base
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(96, 90, 86))  # ash ground
    stone_c = (150, 144, 134)
    d.rectangle([4, 2, 11, 15], fill=stone_c)
    d.rectangle([4, 2, 5, 15], fill=shade(stone_c, 1.15))
    d.rectangle([10, 2, 11, 15], fill=shade(stone_c, 0.7))
    d.rectangle([3, 12, 12, 15], fill=shade(stone_c, 0.85))  # wider base
    d.line([(4, 6), (11, 6)], fill=shade(stone_c, 0.7))       # crack
    d.polygon([(4, 2), (7, 4), (11, 2)], fill=(96, 90, 86))   # broken top
    return img


def gate():  # heavy timber-and-iron town gate
    img = canvas(); d = ImageDraw.Draw(img)
    frame = (58, 44, 30)
    plank = (104, 74, 44)
    d.rectangle([0, 0, T - 1, T - 1], fill=frame)
    d.rectangle([1, 1, T - 2, T - 2], fill=plank)
    for x in range(3, T - 2, 4):
        d.line([(x, 1), (x, T - 2)], fill=shade(plank, 0.72))
    for y in (4, 11):  # iron bands
        d.rectangle([1, y, T - 2, y + 1], fill=(64, 60, 58))
        for x in range(2, T - 2, 4):
            d.point([(x, y)], fill=(150, 146, 140))  # rivets
    return img


def fence():  # broken wooden fence
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(108, 96, 78))  # waste ground
    w = (96, 70, 44)
    for x in (2, 8, 13):
        h = 15 if x != 8 else 10  # middle post broken short
        d.rectangle([x, 16 - h, x + 1, 15], fill=w)
        d.rectangle([x, 16 - h, x, 15], fill=shade(w, 1.15))
    d.rectangle([2, 5, 13, 6], fill=w)  # rail (broken past middle)
    return img


# ---- objects ----
def potato():  # withered potato plant row
    img = canvas(); d = ImageDraw.Draw(img)
    soil = (94, 70, 48)
    d.rectangle([0, 0, T - 1, T - 1], fill=soil)
    d.rectangle([0, 6, T - 1, 9], fill=shade(soil, 1.12))  # mounded row
    speckle(d, soil, 20, lo=0.8, hi=1.1)
    leaf = (108, 116, 66)
    for cx in (4, 11):
        d.line([(cx, 8), (cx - 2, 4)], fill=shade(leaf, 0.8))
        d.line([(cx, 8), (cx + 2, 4)], fill=leaf)
        d.line([(cx, 8), (cx, 3)], fill=shade(leaf, 0.9))
        d.point([(cx - 2, 4), (cx + 2, 4)], fill=shade((150, 130, 60), 1.0))  # wilting tips
    return img


def wagon():  # empty wooden cart bed
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(132, 108, 78))  # dirt under
    w = (110, 80, 46)
    d.rectangle([1, 3, 14, 12], fill=w)                     # bed
    d.rectangle([1, 3, 14, 4], fill=shade(w, 1.15))
    d.rectangle([1, 11, 14, 12], fill=shade(w, 0.7))
    for x in range(3, 14, 3):
        d.line([(x, 4), (x, 11)], fill=shade(w, 0.8))       # planks
    d.ellipse([1, 11, 5, 15], fill=(60, 46, 30))            # wheel
    d.ellipse([2, 12, 4, 14], fill=(120, 110, 100))
    d.ellipse([10, 11, 14, 15], fill=(60, 46, 30))
    d.ellipse([11, 12, 13, 14], fill=(120, 110, 100))
    return img


def logs():  # stack of cut logs (sits on the wagon)
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(110, 80, 46))  # wagon bed showing
    bark = (92, 66, 40)
    end = (156, 122, 78)
    for (y) in (3, 8):
        for x in (2, 7, 12):
            d.ellipse([x, y, x + 4, y + 4], fill=bark)
            d.ellipse([x + 1, y + 1, x + 3, y + 3], fill=end)
            d.point([(x + 2, y + 2)], fill=shade(end, 0.7))  # rings
    return img


def deadtree():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(108, 96, 78))  # waste
    bark = (74, 56, 40)
    d.rectangle([7, 6, 9, 15], fill=bark)
    d.rectangle([7, 6, 7, 15], fill=shade(bark, 1.2))
    d.line([(8, 7), (4, 3)], fill=bark, width=1)
    d.line([(8, 6), (12, 2)], fill=bark, width=1)
    d.line([(8, 9), (13, 8)], fill=bark, width=1)
    d.line([(4, 3), (3, 1)], fill=bark)
    d.line([(12, 2), (13, 0)], fill=bark)
    return img


def bush():  # dry dead shrub
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(108, 96, 78))  # ground beneath
    base = (96, 82, 52)
    d.ellipse([1, 6, T - 2, T - 2], fill=shade(base, 0.85))
    d.ellipse([2, 3, T - 5, 11], fill=base)
    d.ellipse([7, 2, T - 2, 10], fill=shade(base, 1.15))
    for _ in range(10):
        x, y = random.randint(2, 13), random.randint(3, 13)
        d.point([(x, y)], fill=shade(base, 0.7))
    return img


def rubble():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(108, 96, 78))
    rock = (128, 122, 114)
    d.polygon([(2, 15), (6, 5), (10, 15)], fill=rock)
    d.polygon([(6, 15), (6, 5), (10, 15)], fill=shade(rock, 0.75))
    d.polygon([(8, 15), (12, 7), (15, 15)], fill=shade(rock, 0.9))
    return img


def well():  # stone well
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(108, 96, 78))
    s = (128, 122, 114)
    d.ellipse([2, 6, 13, 15], fill=s)
    d.ellipse([4, 8, 11, 14], fill=(30, 34, 44))       # dark water hole
    d.rectangle([2, 3, 3, 8], fill=(90, 66, 40))       # posts
    d.rectangle([12, 3, 13, 8], fill=(90, 66, 40))
    d.rectangle([2, 2, 13, 3], fill=(74, 54, 34))      # roof beam
    return img


# ---- interior detail ----
def wood_floor():
    img = canvas(); d = ImageDraw.Draw(img)
    base = (150, 112, 70)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    for y in (0, 5, 10, 15):
        d.line([(0, y), (T, y)], fill=shade(base, 0.74))
    for (x, y) in [(6, 2), (11, 7), (4, 12)]:
        d.line([(x, y), (x, y + 3)], fill=shade(base, 0.86))
    return img


def house_wall():
    img = canvas(); d = ImageDraw.Draw(img)
    base = (150, 112, 70)
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    for y in (0, 4, 8, 12):
        d.line([(0, y), (T, y)], fill=shade(base, 0.72))
        d.line([(0, y + 1), (T, y + 1)], fill=shade(base, 1.16))
    return img


def house_roof():
    img = canvas(); d = ImageDraw.Draw(img)
    base = (120, 62, 46)  # weathered, faded thatch-red
    d.rectangle([0, 0, T - 1, T - 1], fill=base)
    for row, y in enumerate(range(0, T, 4)):
        off = 4 if row % 2 else 0
        d.line([(0, y), (T, y)], fill=shade(base, 0.7))
        for x in range(off, T, 8):
            d.line([(x, y), (x, y + 4)], fill=shade(base, 0.82))
    return img


def door():
    img = canvas(); d = ImageDraw.Draw(img)
    frame = (58, 42, 28)
    plank = (112, 78, 46)
    d.rectangle([0, 0, T - 1, T - 1], fill=frame)
    d.rectangle([2, 1, 13, 15], fill=plank)
    for x in (5, 9):
        d.line([(x, 1), (x, 15)], fill=shade(plank, 0.74))
    d.rectangle([2, 7, 13, 8], fill=shade(frame, 1.3))
    d.ellipse([10, 8, 12, 10], fill=(210, 184, 96))  # handle
    return img


def rug():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))  # floor beneath
    base = (120, 68, 60)
    d.rectangle([1, 2, 14, 13], fill=base)
    d.rectangle([1, 2, 14, 13], outline=shade(base, 1.25))
    d.rectangle([4, 5, 11, 10], fill=shade(base, 0.78))
    d.rectangle([6, 6, 9, 9], fill=(150, 130, 80))
    return img


def hearth():  # fireplace with embers
    img = canvas(); d = ImageDraw.Draw(img)
    s = (110, 104, 96)
    d.rectangle([0, 0, T - 1, T - 1], fill=s)
    for y in (0, 5, 10):
        d.line([(0, y), (T, y)], fill=shade(s, 0.7))
    d.rectangle([3, 7, 12, 15], fill=(26, 22, 20))       # opening
    d.rectangle([4, 12, 11, 14], fill=(60, 30, 18))      # log bed
    for x in (5, 8, 10):
        d.point([(x, 13)], fill=(230, 140, 40))          # embers
    d.point([(6, 12), (9, 12)], fill=(240, 190, 70))
    return img


def shelf():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))  # on wall
    w = (96, 68, 40)
    d.rectangle([1, 4, 14, 5], fill=w)
    d.rectangle([1, 10, 14, 11], fill=w)
    d.rectangle([3, 1, 5, 4], fill=(140, 120, 80))          # jar
    d.rectangle([8, 1, 9, 4], fill=(120, 60, 50))           # bottle
    d.rectangle([11, 2, 13, 4], fill=(90, 110, 70))         # pot
    d.rectangle([4, 6, 7, 10], fill=(120, 90, 50))          # book/box
    return img


def window():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    d.rectangle([2, 2, 13, 13], fill=(74, 54, 34))          # frame
    d.rectangle([3, 3, 12, 12], fill=(120, 140, 150))       # dull daylight
    d.line([(8, 3), (8, 12)], fill=(74, 54, 34))
    d.line([(3, 7), (12, 7)], fill=(74, 54, 34))
    return img


def bed():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))  # floor beneath
    frame = (98, 68, 40)
    d.rectangle([1, 2, 14, 15], fill=frame)
    blanket = (120, 74, 58)  # faded, worn
    d.rectangle([2, 7, 13, 15], fill=blanket)
    d.line([(2, 11), (13, 11)], fill=shade(blanket, 0.74))
    d.rectangle([2, 2, 13, 6], fill=(206, 196, 176))        # pillow, greyed
    return img


def table():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))  # floor beneath
    top = (134, 96, 56)
    d.rectangle([1, 5, 14, 10], fill=top)
    d.rectangle([1, 5, 14, 6], fill=shade(top, 1.2))
    d.rectangle([1, 9, 14, 10], fill=shade(top, 0.72))
    leg = (94, 64, 36)
    d.rectangle([3, 10, 5, 15], fill=leg)
    d.rectangle([10, 10, 12, 15], fill=leg)
    return img


def chair():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))  # floor beneath
    w = (110, 78, 46)
    d.rectangle([4, 2, 11, 8], fill=w)                      # back
    d.rectangle([4, 8, 11, 10], fill=shade(w, 0.85))       # seat
    d.rectangle([4, 10, 5, 15], fill=shade(w, 0.8))
    d.rectangle([10, 10, 11, 15], fill=shade(w, 0.8))
    return img


def pot():  # cooking pot on the floor
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    m = (72, 70, 74)
    d.ellipse([3, 6, 12, 14], fill=m)
    d.ellipse([4, 5, 11, 9], fill=shade(m, 1.2))           # rim
    d.ellipse([5, 6, 10, 8], fill=(40, 36, 34))            # inside
    return img


def barrel():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    w = (120, 84, 48)
    d.ellipse([3, 2, 12, 15], fill=w)
    d.rectangle([3, 4, 12, 13], fill=w)
    d.rectangle([3, 5, 12, 6], fill=(70, 52, 34))          # hoops
    d.rectangle([3, 11, 12, 12], fill=(70, 52, 34))
    d.rectangle([4, 4, 5, 13], fill=shade(w, 1.15))
    d.ellipse([4, 2, 11, 6], fill=shade(w, 1.1))           # top
    return img


def crate():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    w = (128, 96, 56)
    d.rectangle([2, 3, 13, 14], fill=w)
    d.rectangle([2, 3, 13, 14], outline=shade(w, 0.7))
    d.line([(2, 3), (13, 14)], fill=shade(w, 0.7))
    d.line([(13, 3), (2, 14)], fill=shade(w, 0.7))
    return img


def straw():  # straw bedding pile
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    s = (176, 150, 82)
    d.ellipse([1, 6, 14, 14], fill=s)
    for _ in range(16):
        x, y = random.randint(2, 13), random.randint(7, 13)
        d.line([(x, y), (x + random.randint(-1, 1), y - 2)], fill=shade(s, random.choice([0.8, 1.15])))
    return img


def chest():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    w = (118, 82, 46)
    d.rectangle([2, 7, 13, 14], fill=w)
    d.rectangle([2, 7, 13, 8], fill=shade(w, 0.72))
    d.rectangle([2, 4, 13, 8], fill=shade(w, 1.14))
    for x in (4, 11):
        d.rectangle([x, 4, x + 1, 14], fill=(70, 66, 70))
    d.rectangle([7, 8, 9, 10], fill=(206, 178, 92))
    return img


def diary():
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, T - 1, T - 1], fill=(150, 112, 70))
    cover = (108, 52, 46)
    d.rectangle([4, 2, 12, 14], fill=cover)
    d.rectangle([4, 2, 12, 3], fill=shade(cover, 1.25))
    pages = (206, 190, 152)
    d.rectangle([5, 4, 11, 13], fill=pages)
    d.line([(8, 2), (8, 14)], fill=shade(cover, 0.6))
    for y in (6, 8, 10):
        d.line([(6, y), (10, y)], fill=shade(pages, 0.8))
    return img


for name, fn in {
    "grass": grass, "waste": waste, "deadgrass": deadgrass, "ash": ash, "dirt": dirt,
    "water": water, "stone": stone, "wall": wall, "castle_wall": castle_wall,
    "castle_rubble": castle_rubble, "column": column, "gate": gate, "fence": fence,
    "potato": potato, "wagon": wagon, "logs": logs, "deadtree": deadtree, "bush": bush,
    "rubble": rubble, "well": well, "wood_floor": wood_floor, "house_wall": house_wall,
    "house_roof": house_roof, "door": door, "rug": rug, "hearth": hearth, "shelf": shelf,
    "window": window, "bed": bed, "table": table, "chair": chair, "pot": pot,
    "barrel": barrel, "crate": crate, "straw": straw, "chest": chest, "diary": diary,
}.items():
    reg(name, fn)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles_data.json"), "w") as f:
    json.dump(TILES, f)
print("wrote tiles_data.json with", len(TILES), "tiles")
