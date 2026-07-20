"""
Generates original pixel-art sprite sheets and tiles for Dragobound.
Everything here is hand-authored at a low native resolution (drawn with
simple flat-shaded primitives) and then scaled up with NEAREST filtering
to keep hard pixel edges -- classic GBA-era top-down RPG look.

Run: python3 tools/gen_sprites.py
Outputs PNGs into assets/sprites and assets/tiles.
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR_DIR = os.path.join(ROOT, "assets", "sprites")
TILE_DIR = os.path.join(ROOT, "assets", "tiles")
os.makedirs(SPR_DIR, exist_ok=True)
os.makedirs(TILE_DIR, exist_ok=True)

SCALE = 4
FRAME_W, FRAME_H = 16, 24  # native pixels per frame


def new_frame():
    return Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))


def upscale(img, scale=SCALE):
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


# ---------------------------------------------------------------------------
# Humanoid template -- parameterized so we can re-skin it for every NPC.
# ---------------------------------------------------------------------------
def draw_humanoid(direction, step, palette):
    """
    direction: 'down' | 'up' | 'side'
    step: 0 (idle/contact), 1 (mid-stride left leg fwd), 2 (mid-stride right leg fwd)
    palette: dict with keys hair, skin, cape, tunic, accent, pants, boots, mark
    """
    img = new_frame()
    d = ImageDraw.Draw(img)
    hair = palette["hair"]
    skin = palette["skin"]
    cape = palette["cape"]
    tunic = palette["tunic"]
    accent = palette["accent"]
    pants = palette["pants"]
    boots = palette["boots"]
    mark = palette.get("mark")

    leg_off = 0 if step == 0 else (1 if step == 1 else -1)
    arm_off = -leg_off

    # cape (drawn first, sits behind everything)
    d.rectangle([2, 10, 3, 19], fill=cape)
    d.rectangle([12, 10, 13, 19], fill=cape)
    d.rectangle([3, 18, 12, 20], fill=cape)

    if direction == "up":
        # back of head, no face
        d.rectangle([4, 1, 11, 8], fill=hair)
        d.rectangle([3, 4, 4, 7], fill=hair)
        d.rectangle([11, 4, 12, 7], fill=hair)
        # torso (mostly cape covering back)
        d.rectangle([4, 10, 11, 17], fill=cape)
        d.rectangle([6, 10, 9, 12], fill=accent)
    elif direction == "side":
        # profile silhouette (facing right; flip for left)
        d.rectangle([5, 1, 11, 3], fill=hair)  # top of head
        d.rectangle([9, 3, 12, 4], fill=hair)  # spike toward back
        d.rectangle([6, 3, 11, 8], fill=skin)  # face
        d.ellipse([9, 5, 10, 6], fill=(20, 20, 24, 255))  # eye
        if mark:
            d.point([(8, 6)], fill=mark)
        d.rectangle([6, 2, 11, 3], fill=(214, 224, 232, 255))  # headband
        # torso
        d.rectangle([5, 10, 11, 17], fill=tunic)
        d.rectangle([7, 10, 9, 12], fill=accent)
        # far arm (behind torso, skin mitt)
        d.rectangle([9, 12 + arm_off, 10, 15 + arm_off], fill=skin)
    else:  # down
        d.rectangle([4, 1, 11, 4], fill=hair)
        d.rectangle([3, 2, 4, 6], fill=hair)
        d.rectangle([11, 2, 12, 6], fill=hair)
        d.rectangle([4, 4, 11, 8], fill=skin)  # face
        d.rectangle([4, 3, 11, 4], fill=(214, 224, 232, 255))  # headband
        d.ellipse([5, 6, 6, 7], fill=(20, 20, 24, 255))  # left eye
        d.ellipse([9, 6, 10, 7], fill=(20, 20, 24, 255))  # right eye
        if mark:
            d.point([(5, 7), (10, 7)], fill=mark)
        # neck
        d.rectangle([6, 9, 9, 9], fill=skin)
        # torso
        d.rectangle([4, 10, 11, 17], fill=tunic)
        d.rectangle([7, 10, 8, 15], fill=accent)
        d.rectangle([4, 10, 11, 10], fill=(214, 190, 90, 255))  # collar trim
        # arms / hands
        d.rectangle([2, 11 + arm_off, 3, 15 + arm_off], fill=skin)
        d.rectangle([12, 11 - arm_off, 13, 15 - arm_off], fill=skin)

    # belt
    d.rectangle([4, 17, 11, 18], fill=(40, 32, 28, 255))
    # legs (both directions share this block; side view narrows it)
    if direction == "side":
        d.rectangle([6, 18, 8, 20 + leg_off], fill=pants)
        d.rectangle([8, 18, 10, 20 - leg_off], fill=pants)
        d.rectangle([6, 20 + leg_off, 8, 23 + leg_off], fill=boots)
        d.rectangle([8, 20 - leg_off, 10, 23 - leg_off], fill=boots)
    else:
        d.rectangle([5, 18, 7, 20 + max(leg_off, 0)], fill=pants)
        d.rectangle([9, 18, 11, 20 + max(-leg_off, 0)], fill=pants)
        d.rectangle([5, 20 + max(leg_off, 0), 7, 23 + max(leg_off, 0)], fill=boots)
        d.rectangle([9, 20 + max(-leg_off, 0), 11, 23 + max(-leg_off, 0)], fill=boots)

    return img


PALETTES = {
    "player": dict(hair=(238, 240, 245, 255), skin=(235, 190, 150, 255),
                   cape=(168, 36, 40, 255), tunic=(52, 120, 130, 255),
                   accent=(180, 40, 44, 255), pants=(38, 46, 74, 255),
                   boots=(48, 110, 60, 255), mark=(70, 150, 90, 255)),
    "player_azure": dict(hair=(230, 220, 200, 255), skin=(230, 185, 145, 255),
                         cape=(40, 70, 150, 255), tunic=(60, 90, 140, 255),
                         accent=(210, 180, 60, 255), pants=(40, 44, 60, 255),
                         boots=(70, 70, 90, 255), mark=(60, 130, 200, 255)),
    "player_ember": dict(hair=(60, 44, 40, 255), skin=(200, 150, 110, 255),
                         cape=(190, 90, 30, 255), tunic=(120, 50, 34, 255),
                         accent=(230, 160, 40, 255), pants=(50, 36, 30, 255),
                         boots=(70, 46, 30, 255), mark=(220, 120, 40, 255)),
    "player_shade": dict(hair=(70, 70, 80, 255), skin=(210, 170, 150, 255),
                         cape=(60, 40, 90, 255), tunic=(70, 60, 90, 255),
                         accent=(150, 120, 200, 255), pants=(30, 28, 40, 255),
                         boots=(50, 44, 60, 255), mark=(140, 100, 190, 255)),
    "joran": dict(hair=(90, 64, 46, 255), skin=(224, 178, 140, 255),
                  cape=(70, 78, 92, 255), tunic=(96, 100, 110, 255),
                  accent=(150, 40, 40, 255), pants=(50, 50, 56, 255),
                  boots=(60, 50, 40, 255), mark=None),
    "marrow": dict(hair=(225, 225, 225, 255), skin=(215, 180, 150, 255),
                   cape=(70, 40, 100, 255), tunic=(84, 56, 120, 255),
                   accent=(150, 130, 40, 255), pants=(50, 40, 60, 255),
                   boots=(40, 32, 30, 255), mark=None),
    "king": dict(hair=(210, 200, 190, 255), skin=(220, 180, 145, 255),
                 cape=(120, 20, 30, 255), tunic=(160, 140, 40, 255),
                 accent=(120, 20, 30, 255), pants=(60, 50, 40, 255),
                 boots=(40, 30, 20, 255), mark=None),
    "villager_f": dict(hair=(80, 54, 30, 255), skin=(226, 182, 145, 255),
                       cape=(120, 90, 60, 255), tunic=(150, 110, 70, 255),
                       accent=(90, 60, 40, 255), pants=(110, 80, 55, 255),
                       boots=(70, 50, 35, 255), mark=None),
    "villager_m": dict(hair=(40, 30, 20, 255), skin=(210, 165, 130, 255),
                       cape=(90, 70, 50, 255), tunic=(120, 95, 60, 255),
                       accent=(70, 55, 35, 255), pants=(80, 70, 55, 255),
                       boots=(55, 45, 30, 255), mark=None),
    "child": dict(hair=(200, 160, 60, 255), skin=(230, 190, 150, 255),
                  cape=(150, 150, 90, 255), tunic=(180, 170, 90, 255),
                  accent=(140, 110, 40, 255), pants=(100, 90, 60, 255),
                  boots=(70, 55, 35, 255), mark=None),
    "soldier": dict(hair=(30, 30, 30, 255), skin=(210, 165, 130, 255),
                    cape=(60, 30, 30, 255), tunic=(70, 74, 80, 255),
                    accent=(150, 130, 40, 255), pants=(50, 52, 56, 255),
                    boots=(30, 28, 26, 255), mark=None),
}


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
# Wyrmling (small enemy dragon) -- 2-frame idle + a lunge/attack frame.
# ---------------------------------------------------------------------------
def draw_wyrmling(frame_kind, palette):
    img = new_frame()
    d = ImageDraw.Draw(img)
    body = palette["body"]
    belly = palette["belly"]
    wing = palette["wing"]
    eye = (255, 220, 60, 255)

    bob = 0 if frame_kind == "idle1" else (1 if frame_kind == "idle2" else -1)
    lunge = 2 if frame_kind == "attack" else 0

    # tail
    d.line([(3, 20 - bob), (1, 17 - bob)], fill=body, width=2)
    # hind legs
    d.rectangle([4, 19 - bob, 6, 21 - bob], fill=body)
    d.rectangle([9, 19 - bob, 11, 21 - bob], fill=body)
    # body
    d.ellipse([3 + lunge, 11 - bob, 12 + lunge, 20 - bob], fill=body)
    d.ellipse([5 + lunge, 14 - bob, 10 + lunge, 19 - bob], fill=belly)
    # wings
    d.polygon([(3, 10 - bob), (0, 6 - bob), (5, 11 - bob)], fill=wing)
    d.polygon([(12, 10 - bob), (15, 6 - bob), (10, 11 - bob)], fill=wing)
    # neck + head
    d.ellipse([4 + lunge * 2, 4 - bob, 11 + lunge * 2, 12 - bob], fill=body)
    d.ellipse([5 + lunge * 2, 2 - bob, 10 + lunge * 2, 6 - bob], fill=body)
    d.ellipse([6 + lunge * 2, 3 - bob, 7 + lunge * 2, 4 - bob], fill=eye)
    # small horns
    d.line([(6, 2 - bob), (5, 0 - bob)], fill=(230, 230, 230, 255), width=1)
    d.line([(9, 2 - bob), (10, 0 - bob)], fill=(230, 230, 230, 255), width=1)
    # front legs / claws
    d.rectangle([3 + lunge * 2, 12 - bob, 5 + lunge * 2, 15 - bob], fill=body)
    d.rectangle([10 + lunge * 2, 12 - bob, 12 + lunge * 2, 15 - bob], fill=body)
    return img


WYRMLING_PAL = dict(body=(74, 130, 70, 255), belly=(200, 210, 140, 255), wing=(50, 96, 52, 255))
SKITTER_PAL = dict(body=(120, 96, 70, 255), belly=(200, 180, 140, 255), wing=(90, 70, 50, 255))

for name, pal in [("wyrmling", WYRMLING_PAL), ("skitterdrake", SKITTER_PAL)]:
    sheet = Image.new("RGBA", (FRAME_W * 3, FRAME_H), (0, 0, 0, 0))
    for col, kind in enumerate(["idle1", "idle2", "attack"]):
        frame = draw_wyrmling(kind, pal)
        sheet.paste(frame, (col * FRAME_W, 0), frame)
    sheet = upscale(sheet)
    sheet.save(os.path.join(SPR_DIR, f"{name}.png"))
    print("wrote", name)


# ---------------------------------------------------------------------------
# Tiles -- 16x16 native, upscaled to 64x64 to match the character scale.
# ---------------------------------------------------------------------------
TILE = 16


def tile_canvas():
    return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))


def save_tile(name, img):
    upscale(img).save(os.path.join(TILE_DIR, f"{name}.png"))
    print("wrote tile", name)


def grass():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(74, 128, 64, 255))
    for x, y in [(2, 2), (9, 4), (5, 9), (12, 11), (3, 13)]:
        d.point([(x, y), (x + 1, y)], fill=(94, 150, 80, 255))
    return img


def dirt_path():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(150, 118, 82, 255))
    for x, y in [(2, 3), (10, 2), (6, 8), (12, 12), (3, 11)]:
        d.point([(x, y)], fill=(130, 100, 68, 255))
    return img


def stone_ruins():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(120, 118, 116, 255))
    d.line([(0, 8), (15, 8)], fill=(96, 94, 92, 255))
    d.line([(8, 0), (8, 15)], fill=(96, 94, 92, 255))
    return img


def water():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(56, 96, 150, 255))
    d.line([(0, 5), (15, 5)], fill=(80, 130, 180, 255))
    d.line([(0, 11), (15, 11)], fill=(80, 130, 180, 255))
    return img


def wood_floor():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(140, 100, 62, 255))
    for y in range(0, 16, 4):
        d.line([(0, y), (15, y)], fill=(120, 84, 50, 255))
    return img


def wall():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(90, 66, 50, 255))
    d.rectangle([1, 1, 14, 14], fill=(108, 80, 60, 255))
    return img


def house_wall_bg():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(150, 110, 70, 255))
    for y in range(0, 16, 4):
        d.line([(0, y), (15, y)], fill=(120, 84, 50, 255))
    return img


def house_roof():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(96, 40, 36, 255))
    for y in range(0, 16, 3):
        d.line([(0, y), (15, y)], fill=(76, 30, 28, 255))
    return img


def door():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(60, 40, 26, 255))
    d.rectangle([2, 2, 13, 15], fill=(90, 60, 36, 255))
    d.ellipse([10, 8, 12, 10], fill=(210, 190, 90, 255))
    return img


def bush():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([1, 4, 14, 15], fill=(48, 100, 48, 255))
    d.ellipse([3, 2, 12, 10], fill=(60, 118, 58, 255))
    return img


def rubble():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=(74, 128, 64, 255))
    d.polygon([(2, 14), (6, 4), (10, 14)], fill=(110, 108, 104, 255))
    d.polygon([(7, 14), (11, 6), (14, 14)], fill=(96, 94, 90, 255))
    return img


def chest():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([2, 6, 13, 14], fill=(110, 74, 40, 255))
    d.rectangle([2, 4, 13, 7], fill=(140, 96, 50, 255))
    d.rectangle([6, 8, 9, 10], fill=(210, 190, 90, 255))
    return img


def bed():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([1, 2, 14, 14], fill=(150, 40, 40, 255))
    d.rectangle([1, 2, 14, 5], fill=(230, 230, 230, 255))
    return img


def table():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([1, 5, 14, 11], fill=(120, 84, 50, 255))
    d.rectangle([2, 11, 4, 15], fill=(90, 62, 36, 255))
    d.rectangle([11, 11, 13, 15], fill=(90, 62, 36, 255))
    return img


def diary():
    img = tile_canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 12, 13], fill=(90, 40, 40, 255))
    d.rectangle([4, 4, 11, 12], fill=(150, 60, 55, 255))
    d.line([(7, 4), (7, 12)], fill=(70, 30, 30, 255))
    return img


TILES = {
    "grass": grass, "dirt": dirt_path(), "stone": stone_ruins(), "water": water(),
    "wood_floor": wood_floor(), "wall": wall(), "house_wall": house_wall_bg(),
    "house_roof": house_roof(), "door": door(), "bush": bush(), "rubble": rubble(),
    "chest": chest(), "bed": bed(), "table": table(), "diary": diary(),
}

for name, maker in TILES.items():
    img = maker() if callable(maker) else maker
    save_tile(name, img)

print("done")
