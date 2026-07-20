"""
Generates original pixel-art sprite sheets and tiles for Dragobound.
Realistic human proportions (roughly 5.5 heads tall) at a higher native
resolution than a chibi/GBA-style sprite, with simple directional shading
for volume -- aiming at the SNES/PS1-era "realistic RPG sprite" register
(Chrono Trigger, Vagrant Story) rather than a cutesy handheld look.

Run: python3 tools/gen_sprites.py
Outputs PNGs into assets/sprites and assets/tiles.
"""
import os
import random
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR_DIR = os.path.join(ROOT, "assets", "sprites")
TILE_DIR = os.path.join(ROOT, "assets", "tiles")
os.makedirs(SPR_DIR, exist_ok=True)
os.makedirs(TILE_DIR, exist_ok=True)

SCALE = 3
FRAME_W, FRAME_H = 20, 40  # native pixels per character frame

random.seed(1234)


def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, factor):
    r, g, b = c[0], c[1], c[2]
    a = c[3] if len(c) > 3 else 255
    return (clamp(r * factor), clamp(g * factor), clamp(b * factor), a)


def new_frame(w=FRAME_W, h=FRAME_H):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def upscale(img, scale=SCALE):
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def shaded_rect(d, x0, y0, x1, y1, base, light=1.22, dark=0.76):
    """Flat fill plus a fixed 1px highlight column on the left and a 1px
    shadow column on the right -- a cheap way to imply a cylindrical form.
    Fixed-width bands (rather than proportional) keep narrow parts (a 6px
    head) from being swallowed by their own shading."""
    if x1 < x0 or y1 < y0:
        return
    d.rectangle([x0, y0, x1, y1], fill=base)
    if x1 - x0 + 1 >= 4:
        d.rectangle([x0, y0, x0, y1], fill=shade(base, light))
        d.rectangle([x1, y0, x1, y1], fill=shade(base, dark))


# ---------------------------------------------------------------------------
# Humanoid template -- parameterized so we can re-skin it for every NPC.
# ---------------------------------------------------------------------------
def draw_face(d, cx, top, skin, hair, eye_dark=(32, 26, 22, 255)):
    """cx: center column (float). top: row where hair crown starts.
    A 6px-wide head has no room for eyebrows *and* eyes *and* a nose
    without everything merging into a single dark smear -- keep it to
    what actually reads: hairline, two eyes with a gap, a jaw shadow."""
    hx0, hx1 = cx - 3, cx + 2  # head is 6 wide
    # hair crown + side tufts
    d.rectangle([hx0 - 1, top, hx1 + 1, top + 1], fill=hair)
    d.rectangle([hx0 - 2, top + 1, hx0 - 1, top + 2], fill=hair)
    d.rectangle([hx1 + 1, top + 1, hx1 + 2, top + 2], fill=hair)
    # face, flat except a shadowed jaw line
    d.rectangle([hx0, top + 2, hx1, top + 5], fill=skin)
    d.rectangle([hx0 + 1, top + 6, hx1 - 1, top + 6], fill=shade(skin, 0.86))
    # eyes -- one gap column between them so they read as two, not a bar
    d.point([(hx0 + 1, top + 4)], fill=eye_dark)
    d.point([(hx1 - 1, top + 4)], fill=eye_dark)
    # small mouth mark
    d.point([(cx - 0.5, top + 6)], fill=shade((150, 90, 80, 255), 0.75))


def draw_humanoid(direction, step, palette):
    img = new_frame()
    d = ImageDraw.Draw(img)
    hair = palette["hair"]
    skin = palette["skin"]
    cape = palette["cape"]
    tunic = palette["tunic"]
    accent = palette["accent"]
    pants = palette["pants"]
    boots = palette["boots"]

    cx = FRAME_W / 2  # 10.0
    leg_off = 0 if step == 0 else (2 if step == 1 else -2)
    arm_off = -leg_off // 2

    if direction == "up":
        # back of the head/hair, cape covering most of the back
        shaded_rect(d, cx - 4, 1, cx + 3, 8, hair)
        shaded_rect(d, cx - 3, 9, cx + 2, 9, shade(skin, 0.85))  # nape
        shaded_rect(d, cx - 7, 10, cx + 6, 21, cape)
        shaded_rect(d, cx - 5, 11, cx + 4, 20, shade(tunic, 0.9))
        d.line([(cx - 1, 11), (cx - 1, 19)], fill=shade(tunic, 0.7))
        # arms
        shaded_rect(d, cx - 8, 12 + arm_off, cx - 7, 19 + arm_off, tunic)
        shaded_rect(d, cx + 7, 12 - arm_off, cx + 8, 19 - arm_off, tunic)
    elif direction == "side":
        facex = cx + 2
        shaded_rect(d, facex - 2, 1, facex + 4, 2, hair)
        d.rectangle([facex + 3, 2, facex + 5, 4], fill=hair)  # brow-ward spike
        shaded_rect(d, facex - 2, 3, facex + 3, 8, skin)
        shaded_rect(d, facex - 2, 9, facex + 3, 9, shade(skin, 0.9))
        d.point([(facex + 2, 5)], fill=(32, 26, 22, 255))  # eye
        d.point([(facex + 3, 6)], fill=shade(skin, 0.8))  # nose tip
        d.line([(facex - 1, 7), (facex + 1, 7)], fill=shade((150, 90, 80, 255), 0.8))
        # torso (slightly forward-leaning silhouette)
        shaded_rect(d, cx - 6, 10, cx + 5, 21, tunic)
        d.rectangle([cx - 1, 10, cx + 1, 20], fill=accent)
        shaded_rect(d, cx - 7, 10, cx - 6, 20, cape)
        # trailing / leading arm
        shaded_rect(d, cx + 2, 12 + arm_off, cx + 4, 19 + arm_off, tunic)
        d.rectangle([cx + 2, 18 + arm_off, cx + 4, 19 + arm_off], fill=shade(skin, 1.05))
    else:  # down
        draw_face(d, cx, 1, skin, hair)
        shaded_rect(d, cx - 7, 10, cx + 6, 21, cape)  # cape peeking past shoulders
        shaded_rect(d, cx - 6, 10, cx + 5, 21, tunic)  # torso, tapers via shading only
        d.rectangle([cx - 1, 11, cx + 0, 20], fill=accent)  # center placket
        shaded_rect(d, cx - 6, 10, cx + 5, 10, shade(accent, 1.1))  # collar
        # arms + hands
        shaded_rect(d, cx - 9, 12 + arm_off, cx - 7, 19 + arm_off, tunic)
        d.rectangle([cx - 9, 18 + arm_off, cx - 7, 19 + arm_off], fill=shade(skin, 1.05))
        shaded_rect(d, cx + 7, 12 - arm_off, cx + 9, 19 - arm_off, tunic)
        d.rectangle([cx + 7, 18 - arm_off, cx + 9, 19 - arm_off], fill=shade(skin, 1.05))

    # belt
    shaded_rect(d, cx - 6, 22, cx + 5, 22, shade(boots, 1.15))
    d.rectangle([cx - 1, 22, cx + 0, 22], fill=(180, 150, 70, 255))  # buckle

    # hips / thighs -- a real gap between the legs so they read as two, not one slab
    if direction == "side":
        shaded_rect(d, cx - 5, 23, cx - 1, 29, pants)
        shaded_rect(d, cx - 1, 23, cx + 4, 29, shade(pants, 0.85))
    else:
        shaded_rect(d, cx - 6, 23, cx - 2, 29, pants)
        shaded_rect(d, cx + 2, 23, cx + 6, 29, pants)

    # shins + boots, offset for the walk cycle
    if direction == "side":
        back_off = leg_off
        front_off = -leg_off
        shaded_rect(d, cx - 5, 30 + back_off, cx - 1, 36 + back_off, shade(pants, 0.8))
        shaded_rect(d, cx - 5, 37 + back_off, cx - 1, 39 + back_off, boots)
        shaded_rect(d, cx - 1, 30 + front_off, cx + 4, 36 + front_off, pants)
        shaded_rect(d, cx - 1, 37 + front_off, cx + 4, 39 + front_off, shade(boots, 1.1))
    else:
        lo = max(leg_off, 0)
        ro = max(-leg_off, 0)
        shaded_rect(d, cx - 6, 30 + lo, cx - 2, 36 + lo, pants)
        shaded_rect(d, cx - 6, 37 + lo, cx - 2, 39 + lo, boots)
        shaded_rect(d, cx + 2, 30 + ro, cx + 6, 36 + ro, pants)
        shaded_rect(d, cx + 2, 37 + ro, cx + 6, 39 + ro, boots)

    return img


PALETTES = {
    "player": dict(hair=(64, 46, 32, 255), skin=(196, 156, 122, 255),
                   cape=(96, 28, 26, 255), tunic=(68, 72, 76, 255),
                   accent=(122, 34, 30, 255), pants=(42, 38, 36, 255),
                   boots=(30, 25, 21, 255)),
    "player_azure": dict(hair=(72, 66, 60, 255), skin=(206, 168, 134, 255),
                         cape=(40, 60, 88, 255), tunic=(56, 66, 80, 255),
                         accent=(150, 128, 70, 255), pants=(36, 40, 48, 255),
                         boots=(38, 36, 44, 255)),
    "player_ember": dict(hair=(46, 34, 28, 255), skin=(190, 144, 108, 255),
                         cape=(122, 58, 26, 255), tunic=(82, 48, 32, 255),
                         accent=(150, 92, 32, 255), pants=(48, 36, 28, 255),
                         boots=(48, 34, 24, 255)),
    "player_shade": dict(hair=(54, 52, 58, 255), skin=(202, 166, 148, 255),
                         cape=(50, 42, 66, 255), tunic=(56, 52, 66, 255),
                         accent=(96, 78, 116, 255), pants=(32, 30, 38, 255),
                         boots=(36, 33, 42, 255)),
    "joran": dict(hair=(58, 42, 28, 255), skin=(202, 160, 126, 255),
                  cape=(56, 58, 64, 255), tunic=(74, 72, 68, 255),
                  accent=(108, 42, 38, 255), pants=(44, 42, 40, 255),
                  boots=(34, 28, 22, 255)),
    "marrow": dict(hair=(208, 206, 200, 255), skin=(196, 164, 138, 255),
                   cape=(58, 46, 76, 255), tunic=(66, 54, 82, 255),
                   accent=(122, 106, 52, 255), pants=(42, 36, 52, 255),
                   boots=(32, 28, 26, 255)),
    "king": dict(hair=(196, 188, 178, 255), skin=(200, 164, 132, 255),
                 cape=(96, 28, 32, 255), tunic=(124, 104, 54, 255),
                 accent=(96, 28, 32, 255), pants=(50, 42, 32, 255),
                 boots=(32, 26, 20, 255)),
    "villager_f": dict(hair=(82, 56, 32, 255), skin=(206, 168, 134, 255),
                       cape=(112, 84, 56, 255), tunic=(140, 104, 66, 255),
                       accent=(86, 58, 40, 255), pants=(104, 76, 52, 255),
                       boots=(66, 48, 34, 255)),
    "villager_m": dict(hair=(42, 32, 22, 255), skin=(196, 154, 120, 255),
                       cape=(86, 68, 48, 255), tunic=(112, 90, 58, 255),
                       accent=(68, 54, 36, 255), pants=(76, 66, 52, 255),
                       boots=(52, 42, 30, 255)),
    "child": dict(hair=(184, 146, 60, 255), skin=(212, 174, 140, 255),
                  cape=(140, 138, 84, 255), tunic=(168, 158, 86, 255),
                  accent=(130, 102, 40, 255), pants=(94, 84, 58, 255),
                  boots=(64, 52, 34, 255)),
    "soldier": dict(hair=(28, 26, 24, 255), skin=(196, 154, 120, 255),
                    cape=(58, 30, 30, 255), tunic=(66, 70, 74, 255),
                    accent=(140, 120, 60, 255), pants=(48, 50, 54, 255),
                    boots=(26, 24, 22, 255)),
}

# Ensure pants read as distinct from boots even after per-character tuning --
# a leg that's one flat shade top to bottom looks like a single fused slab.
for _pal in PALETTES.values():
    if sum(_pal["pants"][:3]) - sum(_pal["boots"][:3]) < 35:
        _pal["pants"] = shade(_pal["pants"], 1.4)


def build_character_sheet(name, palette):
    """3x3 grid: rows = down/up/side, cols = idle/step1/step2. Side faces right."""
    sheet = Image.new("RGBA", (FRAME_W * 3, FRAME_H * 3), (0, 0, 0, 0))
    for row, direction in enumerate(["down", "up", "side"]):
        for col, step in enumerate([0, 1, 2]):
            frame = draw_humanoid(direction, step, palette)
            sheet.paste(frame, (col * FRAME_W, row * FRAME_H), frame)
    sheet = upscale(sheet)
    sheet.save(os.path.join(SPR_DIR, f"{name}.png"))
    print("wrote", name)


for name, pal in PALETTES.items():
    build_character_sheet(name, pal)


# ---------------------------------------------------------------------------
# Dragons -- low, wingless ground reptiles (both the wyrmling and the
# skitterdrake are small ground-hunters per the bestiary), scale texture,
# spine ridge. A single lunge offset drives the whole front half so nothing
# visually detaches on the attack frame. 3-frame sheet: idle1, idle2, attack.
# ---------------------------------------------------------------------------
def draw_dragon(frame_kind, palette):
    img = new_frame()
    d = ImageDraw.Draw(img)
    body = palette["body"]
    belly = palette["belly"]
    spine = shade(body, 0.62)
    scale_dark = shade(body, 0.8)
    horn = (214, 208, 198, 255)
    eye = (230, 200, 60, 255)

    bob = 0 if frame_kind == "idle1" else (1 if frame_kind == "idle2" else -1)
    lunge = 2 if frame_kind == "attack" else 0
    y = 24  # ground line the creature's feet rest on

    # tail, tapering back and slightly up
    d.line([(3, y + 3 - bob), (0, y - 4 - bob)], fill=body, width=2)
    d.line([(1, y - 2 - bob), (0, y - 5 - bob)], fill=spine, width=1)

    # hind legs, clawed
    shaded_rect(d, 3, y - 3 - bob, 5, y + 1 - bob, body)
    d.line([(3, y + 1 - bob), (2, y + 2 - bob)], fill=scale_dark)
    shaded_rect(d, 9, y - 3 - bob, 11, y + 1 - bob, body)
    d.line([(11, y + 1 - bob), (12, y + 2 - bob)], fill=scale_dark)

    # body barrel + belly -- front edge stretches slightly with the lunge so
    # the neck attaches to it at every frame, never floating free
    barrel_x1 = 12 + lunge // 2
    shaded_rect(d, 3, y - 12 - bob, barrel_x1, y - 3 - bob, body)
    shaded_rect(d, 5, y - 9 - bob, barrel_x1 - 2, y - 4 - bob, belly)

    # spine ridge spikes
    for x in range(4, 12, 2):
        d.polygon([(x, y - 12 - bob), (x + 1, y - 14 - bob), (x + 2, y - 12 - bob)], fill=spine)
    # scale texture flecks
    for (sx, sy) in [(6, y - 8), (9, y - 6), (7, y - 5)]:
        d.point([(sx, sy - bob)], fill=scale_dark)

    # front legs, extend forward on the lunge
    shaded_rect(d, 8 + lunge, y - 6 - bob, 10 + lunge, y - 1 - bob, body)
    d.line([(8 + lunge, y - 1 - bob), (7 + lunge, y - bob)], fill=scale_dark)

    # neck + head, attaches to the barrel's (already-extended) front edge
    nx = 10 + lunge
    shaded_rect(d, nx, y - 17 - bob, nx + 5, y - 10 - bob, body)
    shaded_rect(d, nx + 1, y - 20 - bob, nx + 6, y - 15 - bob, body)  # snout
    d.point([(nx + 5, y - 18 - bob)], fill=(28, 20, 16, 255))  # nostril
    d.ellipse([nx + 1, y - 19 - bob, nx + 2, y - 18 - bob], fill=eye)
    d.line([(nx + 1, y - 15 - bob), (nx + 6, y - 15 - bob)], fill=scale_dark)  # jaw line
    d.line([(nx + 1, y - 20 - bob), (nx, y - 23 - bob)], fill=horn)
    d.line([(nx + 4, y - 20 - bob), (nx + 5, y - 23 - bob)], fill=horn)
    return img


WYRMLING_PAL = dict(body=(64, 96, 58, 255), belly=(168, 176, 122, 255))
SKITTER_PAL = dict(body=(110, 88, 64, 255), belly=(178, 160, 124, 255))

for name, pal in [("wyrmling", WYRMLING_PAL), ("skitterdrake", SKITTER_PAL)]:
    sheet = Image.new("RGBA", (FRAME_W * 3, FRAME_H), (0, 0, 0, 0))
    for col, kind in enumerate(["idle1", "idle2", "attack"]):
        frame = draw_dragon(kind, pal)
        sheet.paste(frame, (col * FRAME_W, 0), frame)
    sheet = upscale(sheet)
    sheet.save(os.path.join(SPR_DIR, f"{name}.png"))
    print("wrote", name)


# ---------------------------------------------------------------------------
# Tiles -- 32x32 native, upscaled 2x to the 64px world grid. More texture/
# noise/shading than flat cartoon fills.
# ---------------------------------------------------------------------------
TILE = 32
TILE_SCALE = 2


def tile_canvas():
    return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))


def tile_upscale(img):
    return img.resize((img.width * TILE_SCALE, img.height * TILE_SCALE), Image.NEAREST)


def save_tile(name, img):
    tile_upscale(img).save(os.path.join(TILE_DIR, f"{name}.png"))
    print("wrote tile", name)


def noise_speckle(d, base, count, dark=0.85, light=1.15, size=1):
    for _ in range(count):
        x = random.randint(0, TILE - 1)
        y = random.randint(0, TILE - 1)
        c = shade(base, random.choice([dark, light]))
        d.rectangle([x, y, x + size - 1, y + size - 1], fill=c)


def grass():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (58, 92, 50, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    noise_speckle(d, base, 90)
    for _ in range(14):
        x = random.randint(1, TILE - 2)
        y = random.randint(4, TILE - 1)
        blade = shade(base, random.uniform(1.1, 1.35))
        d.line([(x, y), (x, y - random.randint(2, 4))], fill=blade)
    return img


def dirt_path():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (118, 92, 64, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    noise_speckle(d, base, 70)
    for _ in range(5):
        x, y = random.randint(2, TILE - 4), random.randint(2, TILE - 4)
        d.ellipse([x, y, x + 2, y + 1], fill=shade(base, 0.75))
    return img


def stone_ruins():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (108, 106, 102, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    for row in range(0, TILE, 8):
        offset = 8 if (row // 8) % 2 else 0
        d.line([(0, row), (TILE, row)], fill=shade(base, 0.7))
        for col in range(-offset, TILE, 16):
            d.line([(col, row), (col, row + 8)], fill=shade(base, 0.7))
    noise_speckle(d, base, 60)
    return img


def water():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (48, 84, 132, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    for row in range(2, TILE, 6):
        d.line([(0, row), (TILE, row - 2)], fill=shade(base, 1.25), width=1)
    noise_speckle(d, base, 30, dark=0.9, light=1.3)
    return img


def wood_floor():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (128, 92, 58, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    for y in range(0, TILE, 8):
        d.line([(0, y), (TILE, y)], fill=shade(base, 0.78))
    for _ in range(10):
        x = random.randint(0, TILE - 6)
        y = random.randint(0, TILE - 1)
        d.line([(x, y), (x + random.randint(3, 6), y)], fill=shade(base, 0.9))
    return img


def wall():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (86, 64, 48, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=shade(base, 1.1))
    for row in range(0, TILE, 8):
        offset = 8 if (row // 8) % 2 else 0
        d.line([(0, row), (TILE, row)], fill=shade(base, 0.65), width=1)
        for col in range(-offset, TILE, 16):
            d.line([(col, row), (col, row + 8)], fill=shade(base, 0.65), width=1)
    noise_speckle(d, base, 40)
    return img


def house_wall_bg():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (146, 106, 66, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    for y in range(0, TILE, 7):
        d.line([(0, y), (TILE, y)], fill=shade(base, 0.72))
        d.line([(0, y + 1), (TILE, y + 1)], fill=shade(base, 1.15))
    for _ in range(6):
        x = random.randint(0, TILE - 1)
        y = random.randint(0, TILE - 1)
        d.point([(x, y)], fill=shade(base, 0.6))
    return img


def house_roof():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (94, 38, 34, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    for y in range(0, TILE, 5):
        d.line([(0, y), (TILE, y)], fill=shade(base, 0.7))
    for y in range(0, TILE, 5):
        for x in range((y // 5) % 2 * 4, TILE, 8):
            d.line([(x, y), (x, y + 5)], fill=shade(base, 0.8))
    noise_speckle(d, base, 30, dark=0.75, light=1.1)
    return img


def door():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    frame = (52, 36, 24, 255)
    plank = (98, 66, 40, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=frame)
    d.rectangle([3, 2, TILE - 4, TILE - 2], fill=plank)
    for x in range(5, TILE - 4, 6):
        d.line([(x, 2), (x, TILE - 2)], fill=shade(plank, 0.75))
    d.rectangle([3, TILE // 2 - 1, TILE - 4, TILE // 2], fill=(58, 46, 30, 255))  # iron band
    d.ellipse([TILE - 10, TILE // 2 - 2, TILE - 7, TILE // 2 + 1], fill=(196, 172, 90, 255))  # handle
    return img


def bush():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (46, 92, 44, 255)
    d.ellipse([2, 10, TILE - 3, TILE - 2], fill=shade(base, 0.85))
    d.ellipse([4, 5, TILE - 8, 20], fill=base)
    d.ellipse([10, 3, TILE - 3, 18], fill=shade(base, 1.15))
    noise_speckle(d, base, 40)
    return img


def rubble():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (58, 92, 50, 255)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=base)
    noise_speckle(d, base, 40)
    rock = (100, 98, 94, 255)
    d.polygon([(4, TILE - 2), (12, 6), (20, TILE - 2)], fill=rock)
    d.polygon([(12, TILE - 2), (12, 6), (20, TILE - 2)], fill=shade(rock, 0.8))
    d.polygon([(14, TILE - 2), (22, 10), (30, TILE - 2)], fill=shade(rock, 0.9))
    d.polygon([(22, TILE - 2), (22, 10), (30, TILE - 2)], fill=shade(rock, 0.7))
    return img


def chest():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    base = (0, 0, 0, 0)
    wood = (112, 74, 40, 255)
    d.rectangle([4, 12, TILE - 5, TILE - 3], fill=wood)
    d.rectangle([4, 12, TILE - 5, 15], fill=shade(wood, 0.75))
    d.rectangle([4, 6, TILE - 5, 13], fill=shade(wood, 1.15))
    d.rectangle([4, 6, TILE - 5, 8], fill=shade(wood, 0.9))
    for x in (7, TILE - 9):
        d.rectangle([x, 6, x + 2, TILE - 3], fill=(70, 70, 74, 255))
    d.rectangle([12, 15, 19, 19], fill=(198, 172, 90, 255))
    return img


def bed():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    frame = (92, 62, 36, 255)
    d.rectangle([1, 3, TILE - 2, TILE - 2], fill=frame)
    blanket = (128, 42, 40, 255)
    d.rectangle([2, 8, TILE - 3, TILE - 3], fill=blanket)
    for y in range(9, TILE - 3, 5):
        d.line([(2, y), (TILE - 3, y)], fill=shade(blanket, 0.75))
    d.rectangle([2, 3, TILE - 3, 8], fill=(224, 222, 214, 255))
    d.rectangle([2, 3, TILE - 3, 4], fill=shade((224, 222, 214, 255), 0.85))
    return img


def table():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    top = (126, 88, 52, 255)
    d.rectangle([1, 9, TILE - 2, 19], fill=top)
    d.rectangle([1, 9, TILE - 2, 11], fill=shade(top, 1.2))
    d.rectangle([1, 17, TILE - 2, 19], fill=shade(top, 0.75))
    leg = (86, 58, 34, 255)
    d.rectangle([4, 19, 7, TILE - 2], fill=leg)
    d.rectangle([TILE - 8, 19, TILE - 5, TILE - 2], fill=leg)
    return img


def diary():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    cover = (92, 42, 40, 255)
    d.rectangle([5, 4, TILE - 6, TILE - 5], fill=cover)
    d.rectangle([5, 4, TILE - 6, 6], fill=shade(cover, 1.2))
    pages = (206, 190, 150, 255)
    d.rectangle([7, 7, TILE - 8, TILE - 8], fill=pages)
    for y in range(9, TILE - 9, 3):
        d.line([(8, y), (TILE - 9, y)], fill=shade(pages, 0.8))
    d.line([(TILE // 2, 4), (TILE // 2, TILE - 5)], fill=shade(cover, 0.6), width=1)
    d.rectangle([TILE // 2 - 1, TILE // 2 - 3, TILE // 2 + 1, TILE // 2 + 3], fill=(180, 150, 70, 255))  # clasp
    return img


TILES = {
    "grass": grass, "dirt": dirt_path, "stone": stone_ruins, "water": water,
    "wood_floor": wood_floor, "wall": wall, "house_wall": house_wall_bg,
    "house_roof": house_roof, "door": door, "bush": bush, "rubble": rubble,
    "chest": chest, "bed": bed, "table": table, "diary": diary,
}

for name, maker in TILES.items():
    save_tile(name, maker())

print("done")
