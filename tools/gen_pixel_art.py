"""
Dragobound pixel-art generator (v5).

GBA-trainer chassis at 32x44: huge head, vertical bar eyes, no mouth/nose,
tiny akimbo body. Twelve unique character sheets -- nobody shares a sprite --
plus two dragons drawn in a clean quadruped side profile.

Veth Hollow is poor: every Hollow character gets wear -- dulled cloth colors,
patches, frayed hems, scuffed boots. The Solmeran soldier stays crisp on
purpose; the empire can afford it.

Fighters get a two-frame sword swing (windup + strike) per direction.

Run: python3 tools/gen_pixel_art.py            # writes src/data/sprites.js
     python3 tools/gen_pixel_art.py preview    # also writes /tmp/pixel_preview/*.png
"""
import json
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 32, 44
PREVIEW_DIR = "/tmp/pixel_preview"

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
ROLES = [
    "outline", "hair", "hairShadow", "skin", "skinShadow", "eye",
    "beard", "beardShadow", "torso", "torsoShadow", "accent", "accent2",
    "belt", "buckle", "pants", "pantsShadow", "boots", "bootsShadow",
    "metal", "metalShadow", "gold", "wood", "straw", "strawShadow", "orb",
    "body", "bodyShadow", "belly", "bellyShadow", "wing", "horn", "maw",
]
MARKER = {}
for i, role in enumerate(ROLES):
    v = 8 + i * 7
    MARKER[role] = (v, (v * 3) % 251, (v * 7) % 251, 255)
MARKER_TO_ROLE = {v[:3]: k for k, v in MARKER.items()}

ROLE_CHAR = {
    "outline": "K", "hair": "H", "hairShadow": "h", "skin": "S", "skinShadow": "s",
    "eye": "E", "beard": "D", "beardShadow": "d",
    "torso": "T", "torsoShadow": "t", "accent": "A", "accent2": "a",
    "belt": "Y", "buckle": "y", "pants": "P", "pantsShadow": "p",
    "boots": "O", "bootsShadow": "o", "metal": "M", "metalShadow": "m",
    "gold": "G", "wood": "W", "straw": "R", "strawShadow": "r", "orb": "Q",
    "body": "B", "bodyShadow": "b", "belly": "L", "bellyShadow": "l",
    "wing": "V", "horn": "N", "maw": "X",
}

GROUPS = {
    "hair": ({"hair", "hairShadow"}, "1", "h"),
    "skin": ({"skin", "skinShadow"}, "2", "s"),
    "torso": ({"torso", "torsoShadow"}, "3", "t"),
    "pants": ({"pants", "pantsShadow"}, "4", "p"),
    "boots": ({"boots", "bootsShadow"}, "5", "o"),
    "metal": ({"metal", "metalShadow"}, "7", "m"),
    "beard": ({"beard", "beardShadow"}, "8", "d"),
    "straw": ({"straw", "strawShadow"}, "9", "r"),
    "body": ({"body", "bodyShadow"}, "!", "b"),
    "belly": ({"belly", "bellyShadow"}, "@", "l"),
}
GROUND_CHAR = "0"
OCCLUDERS = {"belt", "buckle", "straw", "strawShadow"}

ROLE_TO_GROUP = {}
for g, (members, _, _) in GROUPS.items():
    for r in members:
        ROLE_TO_GROUP[r] = g


def m(role):
    return MARKER[role]


def role_at(img, x, y):
    if x < 0 or y < 0 or x >= img.width or y >= img.height:
        return None
    r, g, b, a = img.getpixel((x, y))
    if a == 0:
        return None
    return MARKER_TO_ROLE.get((r, g, b))


def add_outline(img):
    w, h = img.size
    alpha = [[img.getpixel((x, y))[3] > 0 for x in range(w)] for y in range(h)]
    outline = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = outline.load()
    for y in range(h):
        for x in range(w):
            if alpha[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and alpha[ny][nx]:
                    opx[(x, y)] = m("outline")
                    break
    return Image.alpha_composite(outline, img)


def to_grid(img):
    rows = []
    for y in range(img.height):
        row = ""
        for x in range(img.width):
            role = role_at(img, x, y)
            if role is None:
                row += "."
                continue
            ch = ROLE_CHAR[role]
            group = ROLE_TO_GROUP.get(role)
            if group and role == group:
                members, hl_ch, sh_ch = GROUPS[group]
                above = role_at(img, x, y - 1)
                right = role_at(img, x + 1, y)
                below = role_at(img, x, y + 1)
                above_group = ROLE_TO_GROUP.get(above) if above else None
                if role == "boots" and (below is None or below == "outline"):
                    ch = GROUND_CHAR
                elif above_group != group and above != "outline" and above not in OCCLUDERS:
                    ch = hl_ch
                elif sh_ch and (right is None or right == "outline"):
                    ch = sh_ch
                elif sh_ch and (below is None or below == "outline"):
                    ch = sh_ch
            row += ch
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------
WARM_LIGHT = (255, 244, 205)
COOL_DARK = (32, 26, 58)
WORN_GREY = (104, 96, 86)


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (1, 3, 5))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


CLOTH_ROLES = {"torso", "pants", "boots", "accent", "accent2", "belt", "straw"}


def make_palette(bases, worn=True):
    """worn: dull the cloth toward grey-brown -- these are poor people's
    clothes, washed a hundred times and mended more."""
    def base_of(role):
        c = rgb(bases[role])
        if worn and role in CLOTH_ROLES:
            c = mix(c, WORN_GREY, 0.16)
        return c

    pal = {"K": "#1a1424"}
    shadow_pairs = {
        "hair": ("H", "h"), "torso": ("T", "t"), "pants": ("P", "p"),
        "boots": ("O", "o"), "metal": ("M", "m"), "beard": ("D", "d"),
        "straw": ("R", "r"), "body": ("B", "b"), "belly": ("L", "l"),
    }
    plain = {
        "accent": "A", "accent2": "a", "belt": "Y", "wood": "W", "gold": "G",
        "orb": "Q", "wing": "V", "horn": "N",
    }
    for role, (bc, sc) in shadow_pairs.items():
        if role not in bases:
            continue
        base = base_of(role)
        pal[bc] = hexc(base)
        pal[sc] = hexc(mix(base, COOL_DARK, 0.34))
    for role, ch in plain.items():
        if role in bases:
            pal[ch] = hexc(base_of(role)) if role in CLOTH_ROLES else bases[role]
    if "skin" in bases:
        base = rgb(bases["skin"])
        pal["S"] = hexc(base)
        pal["s"] = hexc(mix(base, COOL_DARK, 0.20))
    if "belt" in bases:
        pal["y"] = hexc(mix(base_of("belt"), COOL_DARK, 0.35))
    pal["E"] = bases.get("eye", "#181418")
    pal["X"] = bases.get("maw", "#8e2c30")
    for group, (_members, hl_ch, _sc) in GROUPS.items():
        if group in bases:
            base = base_of(group) if group in CLOTH_ROLES else rgb(bases[group])
            t = 0.15 + 0.25 * (luminance(base) / 255.0)
            pal[hl_ch] = hexc(mix(base, WARM_LIGHT, t))
    return pal


# ---------------------------------------------------------------------------
# Size tiers
# ---------------------------------------------------------------------------
SIZES = {
    "adult": dict(cap=(4, 2, 27, 14), face=(5, 8, 26, 26),
                  eyes=((10, 11), (20, 21)), ey=17, eh=4,
                  t=(27, 37, 9, 22), legs=(38, 39, 40, 43),
                  ll=(10, 14), rl=(17, 21), side_arm=(16, 21), flare=5),
    "teen": dict(cap=(6, 6, 25, 17), face=(7, 11, 24, 28),
                 eyes=((11, 12), (19, 20)), ey=20, eh=3,
                 t=(30, 38, 10, 21), legs=(39, 40, 41, 43),
                 ll=(11, 14), rl=(17, 20), side_arm=(16, 20), flare=4),
    "child": dict(cap=(8, 12, 23, 21), face=(9, 15, 22, 30),
                  eyes=((12, 13), (18, 19)), ey=23, eh=3,
                  t=(33, 39, 10, 21), legs=(40, 40, 41, 43),
                  ll=(11, 14), rl=(17, 20), side_arm=(16, 20), flare=0),
}


# ---------------------------------------------------------------------------
# Humanoid builder
# ---------------------------------------------------------------------------
def build_humanoid(spec, direction, step, attack=0):
    """attack: 0 = none, 1 = windup, 2 = strike."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    size = SIZES[spec.get("size", "adult")]
    arm_off = -step
    garment = spec.get("garment", "tunic")
    robe_like = garment in ("robe", "dress")

    cap = size["cap"]
    face = size["face"]
    eye_cols, ey, eh = size["eyes"], size["ey"], size["eh"]
    t_top, t_bot, t_l, t_r = size["t"]
    l_top, l_bot, b_top, b_bot = size["legs"]
    ll, rl = size["ll"], size["rl"]
    side_arm = size["side_arm"]
    flare = size["flare"]
    seed = spec.get("seed", 0)

    # ---------------- legs & feet ----------------
    lo = max(step, 0)
    ro = max(-step, 0)
    if robe_like:
        pass
    elif direction == "side":
        back, front = step, -step
        d.rectangle([ll[0] + 1, l_top + back, ll[1] + 1, l_bot + back], fill=m("pantsShadow"))
        d.rectangle([ll[0] + 1, b_top + back, ll[1] + 1, b_bot + back], fill=m("bootsShadow"))
        d.rectangle([rl[0] - 1, l_top + front, rl[1] - 1, l_bot + front], fill=m("pants"))
        d.rectangle([rl[0] - 1, b_top + front, rl[1] - 1, b_bot + front], fill=m("boots"))
    else:
        d.rectangle([ll[0], l_top + lo, ll[1], l_bot + lo], fill=m("pants"))
        d.rectangle([ll[0], l_top + lo, ll[0], l_bot + lo], fill=m("pantsShadow"))
        d.rectangle([rl[0], l_top + ro, rl[1], l_bot + ro], fill=m("pants"))
        d.rectangle([rl[1], l_top + ro, rl[1], l_bot + ro], fill=m("pantsShadow"))
        d.rectangle([ll[0], b_top + lo, ll[1], b_bot + lo], fill=m("boots"))
        d.rectangle([ll[0], b_top + lo, ll[0], b_bot + lo], fill=m("bootsShadow"))
        d.rectangle([rl[0], b_top + ro, rl[1], b_bot + ro], fill=m("boots"))
        d.rectangle([rl[1], b_top + ro, rl[1], b_bot + ro], fill=m("bootsShadow"))
        d.rectangle([ll[0] + 1, b_top + 1 + lo, ll[1] - 1, b_top + 1 + lo], fill=m("accent2"))
        d.rectangle([rl[0] + 1, b_top + 1 + ro, rl[1] - 1, b_top + 1 + ro], fill=m("accent2"))

    # ---------------- torso / garment ----------------
    if robe_like:
        d.rectangle([t_l - 1, t_top, t_r + 1, t_bot], fill=m("torso"))
        sway = step
        d.polygon([(t_l - 1, t_bot), (t_r + 1, t_bot), (t_r + 2, 41), (t_l - 2, 41)], fill=m("torso"))
        d.rectangle([t_l - 1, t_top, t_l - 1, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r + 1, t_top, t_r + 1, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_l - 2, 40, t_r + 2, 41], fill=m("torsoShadow"))
        if direction != "up":
            d.rectangle([t_l + 1, t_top, t_l + 2, 41], fill=m("accent"))
            d.rectangle([t_r - 2, t_top, t_r - 1, 41], fill=m("accent"))
        if spec.get("sash"):
            d.rectangle([t_l - 1, t_top + 4, t_r + 1, t_top + 5], fill=m("accent2"))
        if spec.get("apron") and direction == "down":
            d.rectangle([12, t_top + 2, 19, 40], fill=m("accent2"))
            d.rectangle([12, t_top + 2, 12, 40], fill=m("torsoShadow"))
            d.rectangle([19, t_top + 2, 19, 40], fill=m("torsoShadow"))
        d.rectangle([11 + sway, 42, 14 + sway, 43], fill=m("boots"))
        d.rectangle([17 + sway, 42, 20 + sway, 43], fill=m("boots"))
    elif garment == "overalls":
        d.rectangle([t_l, t_top, t_r, t_top + 3], fill=m("torso"))
        d.rectangle([t_l, t_top + 4, t_r, t_bot], fill=m("pants"))
        d.rectangle([11, t_top, 12, t_top + 3], fill=m("pants"))
        d.rectangle([19, t_top, 20, t_top + 3], fill=m("pants"))
        d.point([(11, t_top + 4), (20, t_top + 4)], fill=m("buckle"))
        d.rectangle([13, t_top + 6, 18, t_top + 8], fill=m("pantsShadow"))
        d.rectangle([t_l, t_top, t_l, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r, t_top, t_r, t_bot], fill=m("torsoShadow"))
    elif garment == "armor":
        d.rectangle([t_l, t_top, t_r, t_bot], fill=m("metal"))
        d.rectangle([t_l, t_top, t_l + 1, t_bot], fill=m("metalShadow"))
        d.rectangle([t_r - 1, t_top, t_r, t_bot], fill=m("metalShadow"))
        d.line([(t_l + 2, t_top + 5), (t_r - 2, t_top + 5)], fill=m("metalShadow"))
        d.rectangle([13, t_top + 3, 18, t_bot + 1], fill=m("accent"))
        d.rectangle([15, t_top + 3, 16, t_bot + 1], fill=m("gold"))
    else:  # tunic
        d.rectangle([t_l, t_top, t_r, t_bot], fill=m("torso"))
        d.rectangle([t_l, t_top, t_l, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r, t_top, t_r, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_l, t_bot, t_r, t_bot], fill=m("torsoShadow"))
        d.line([(13, t_top), (15, t_top + 2)], fill=m("accent2"))
        d.line([(18, t_top), (16, t_top + 2)], fill=m("accent2"))
        if spec.get("strap") and direction == "down":
            for i in range(7):
                x = t_l + 1 + i * 1.6
                y = t_top + 1 + i
                d.rectangle([int(x), y, int(x) + 1, y], fill=m("accent"))
        if spec.get("strap") and direction == "up":
            for i in range(7):
                x = t_r - 1 - i * 1.6
                y = t_top + 1 + i
                d.rectangle([int(x) - 1, y, int(x), y], fill=m("accent"))

    if garment in ("tunic", "armor") and spec.get("size", "adult") == "adult":
        d.rectangle([t_l, t_bot - 2, t_r, t_bot - 1], fill=m("belt"))
        if direction == "down":
            d.rectangle([15, t_bot - 2, 16, t_bot - 1], fill=m("buckle"))

    # ---------------- arms ----------------
    sleeve = m("metal") if garment == "armor" else m("torso")
    sleeve_sh = m("metalShadow") if garment == "armor" else m("torsoShadow")
    sh_y = t_top + 1

    def akimbo_left(off):
        d.polygon([(t_l, sh_y + off), (t_l - flare, sh_y + 2 + off), (t_l - flare, sh_y + 5 + off),
                   (t_l - 1, sh_y + 4 + off)], fill=sleeve)
        d.rectangle([t_l - flare, sh_y + 5 + off, t_l - flare + 2, sh_y + 7 + off], fill=m("skin"))
        if spec.get("bracers"):
            d.rectangle([t_l - flare, sh_y + 4 + off, t_l - flare + 2, sh_y + 5 + off], fill=m("belt"))

    def akimbo_right(off):
        d.polygon([(t_r, sh_y + off), (t_r + flare, sh_y + 2 + off), (t_r + flare, sh_y + 5 + off),
                   (t_r + 1, sh_y + 4 + off)], fill=sleeve)
        d.rectangle([t_r + flare - 2, sh_y + 5 + off, t_r + flare, sh_y + 7 + off], fill=m("skin"))
        if spec.get("bracers"):
            d.rectangle([t_r + flare - 2, sh_y + 4 + off, t_r + flare, sh_y + 5 + off], fill=m("belt"))

    def vblade(x, y0, y1):
        """Vertical blade with a stepped tip at y0; never touches the frame edge."""
        d.rectangle([x, y0 + 2, x + 1, y1], fill=m("metal"))
        d.rectangle([x, y0, x, y0 + 1], fill=m("metal"))

    def hblade(x0, x1, y):
        """Horizontal blade pointing right with a stepped tip at x1."""
        d.rectangle([x0, y, x1 - 2, y + 1], fill=m("metal"))
        d.rectangle([x1 - 1, y, x1, y], fill=m("metal"))

    if attack:
        pass  # attack arm + blade drawn after the head so the raised sword isn't hidden
    elif False:
        if direction == "side":
            if attack == 1:  # windup: blade raised vertical
                d.rectangle([side_arm[0] + 2, sh_y - 2, side_arm[1], sh_y + 1], fill=sleeve)
                d.rectangle([side_arm[1] - 1, sh_y - 4, side_arm[1] + 1, sh_y - 2], fill=m("skin"))
                d.rectangle([side_arm[1] - 2, sh_y - 5, side_arm[1] + 2, sh_y - 5], fill=m("gold"))
                vblade(side_arm[1] - 1, 6, sh_y - 6)
            else:  # strike: thrust forward
                d.rectangle([side_arm[1] - 3, sh_y + 1, side_arm[1] + 1, sh_y + 3], fill=sleeve)
                d.rectangle([side_arm[1] + 2, sh_y + 1, side_arm[1] + 3, sh_y + 3], fill=m("skin"))
                d.rectangle([side_arm[1] + 4, sh_y, side_arm[1] + 4, sh_y + 4], fill=m("gold"))
                hblade(side_arm[1] + 5, 30, sh_y + 1)
        elif direction == "down":
            akimbo_left(0)
            if attack == 1:  # windup: blade high over the right shoulder
                d.rectangle([t_r, sh_y - 2, t_r + 2, sh_y], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 4, t_r + 5, sh_y - 2], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y - 5, t_r + 6, sh_y - 5], fill=m("gold"))
                vblade(t_r + 4, 8, sh_y - 6)
            else:  # strike: blade swung down beside the leg
                d.rectangle([t_r, sh_y, t_r + 2, sh_y + 2], fill=sleeve)
                d.rectangle([t_r + 3, sh_y + 3, t_r + 5, sh_y + 5], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y + 6, t_r + 6, sh_y + 6], fill=m("gold"))
                d.rectangle([t_r + 4, sh_y + 7, t_r + 5, 40], fill=m("metal"))
                d.rectangle([t_r + 4, 41, t_r + 4, 42], fill=m("metal"))  # tip
        else:  # up
            akimbo_left(0)
            if attack == 1:  # windup: blade out to the side
                d.rectangle([t_r, sh_y - 1, t_r + 2, sh_y + 1], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 1, t_r + 4, sh_y + 1], fill=m("skin"))
                d.rectangle([t_r + 5, sh_y - 2, t_r + 5, sh_y + 2], fill=m("gold"))
                hblade(t_r + 6, 30, sh_y - 1)
            else:  # strike: blade raised high
                d.rectangle([t_r, sh_y - 1, t_r + 3, sh_y + 1], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 3, t_r + 5, sh_y - 1], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y - 4, t_r + 6, sh_y - 4], fill=m("gold"))
                vblade(t_r + 3, 4, sh_y - 5)
    elif direction == "side":
        d.polygon([(side_arm[0] + 1, sh_y + arm_off), (side_arm[1] + 3, sh_y + 2 + arm_off),
                   (side_arm[1] + 3, sh_y + 5 + arm_off), (side_arm[0] + 2, sh_y + 4 + arm_off)], fill=sleeve)
        d.rectangle([side_arm[1], sh_y + 5 + arm_off, side_arm[1] + 2, sh_y + 7 + arm_off], fill=m("skin"))
        if spec.get("staff"):
            d.rectangle([27, 8, 28, 41], fill=m("wood"))
            d.rectangle([27, 8, 27, 41], fill=m("bootsShadow"))
            d.ellipse([25, 3, 30, 8], fill=m("orb"))
    else:
        left_arm = not (spec.get("one_arm") and direction == "down")
        right_arm = not (spec.get("one_arm") and direction == "up")
        if flare == 0:
            for present, (ax0, ax1), off in ((left_arm, (t_l - 2, t_l - 1), arm_off),
                                             (right_arm, (t_r + 1, t_r + 2), -arm_off)):
                d.rectangle([ax0, t_top + 1 + off, ax1, t_top + 4 + off], fill=sleeve)
                d.rectangle([ax0, t_top + 5 + off, ax1, t_top + 6 + off], fill=m("skin"))
        else:
            if left_arm:
                akimbo_left(arm_off)
            else:
                d.rectangle([t_l - 3, sh_y, t_l - 1, sh_y + 3], fill=sleeve)
                d.rectangle([t_l - 3, sh_y + 3, t_l - 1, sh_y + 4], fill=sleeve_sh)
            if right_arm:
                akimbo_right(-arm_off)
            else:
                d.rectangle([t_r + 1, sh_y, t_r + 3, sh_y + 3], fill=sleeve)
                d.rectangle([t_r + 1, sh_y + 3, t_r + 3, sh_y + 4], fill=sleeve_sh)
        if spec.get("staff") and direction == "down":
            d.rectangle([28, 8, 29, 41], fill=m("wood"))
            d.ellipse([26, 3, 31, 8], fill=m("orb"))

    # ---------------- wear & tear (skip for crisp Solmeran gear) ----------------
    if spec.get("worn", True):
        px = img.load()
        if garment == "tunic" or robe_like:
            patch_x = t_l + 3 + (seed % 5)
            patch_y = t_top + 3 + (seed % 3)
            d.rectangle([patch_x, patch_y, patch_x + 2, patch_y + 1], fill=m("torsoShadow"))
        if garment == "overalls":
            d.rectangle([t_l + 2 + (seed % 3), t_top + 5, t_l + 3 + (seed % 3), t_top + 6], fill=m("pantsShadow"))
        # frayed hem: nick pixels out so the outline pass makes it ragged
        hem_y = 41 if robe_like else t_bot
        for fx in range(t_l + 1 + (seed % 3), t_r, 4):
            if 0 <= fx < W and img.getpixel((fx, hem_y))[3] > 0:
                px[(fx, hem_y)] = (0, 0, 0, 0)
        # scuffed boots
        if not robe_like:
            d.point([(ll[0] + 1 + (seed % 3), b_top + 2), (rl[0] + 1 + ((seed + 1) % 3), b_top + 3)],
                    fill=m("bootsShadow"))

    # ---------------- head ----------------
    hair = spec.get("hair", "short")
    headgear = spec.get("headgear")

    if direction == "down":
        d.ellipse(list(face), fill=m("skin"))
        for ex0, ex1 in eye_cols:
            d.rectangle([ex0, ey, ex1, ey + eh], fill=m("eye"))
        if spec.get("beard"):
            d.ellipse([face[0] + 3, ey + eh + 1, face[2] - 3, face[3] + 4], fill=m("beard"))
    elif direction == "up":
        d.ellipse(list(face), fill=m("skinShadow"))
    else:
        d.ellipse([face[0] + 4, face[1], face[2] + 2, face[3]], fill=m("skin"))
        ex = face[2] - 5
        d.rectangle([ex, ey, ex + 1, ey + eh], fill=m("eye"))
        if spec.get("beard"):
            d.rectangle([face[0] + 8, ey + eh + 1, face[2] + 1, face[3] + 3], fill=m("beard"))

    def front_hair():
        if headgear == "helm":
            d.ellipse([cap[0], cap[1], cap[2], cap[3]], fill=m("metal"))
            d.rectangle([cap[0], cap[3] + 1, cap[0] + 2, cap[3] + 9], fill=m("metal"))
            d.rectangle([cap[2] - 2, cap[3] + 1, cap[2], cap[3] + 9], fill=m("metalShadow"))
            d.rectangle([15, cap[3] - 2, 16, ey + eh], fill=m("metalShadow"))
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] - 3, cap[3] - 3, cap[2] + 3, cap[3] + 2], fill=m("straw"))
            d.ellipse([cap[0] + 2, cap[1] + 1, cap[2] - 2, cap[3] - 1], fill=m("straw"))
            d.rectangle([cap[0] + 2, cap[3] - 3, cap[2] - 2, cap[3] - 2], fill=m("belt"))
            return
        if headgear == "kerchief":
            d.ellipse([cap[0] + 1, cap[1] + 1, cap[2] - 1, cap[3] + 1], fill=m("accent"))
            d.rectangle([cap[0] + 1, cap[3] - 1, cap[2] - 1, cap[3]], fill=m("belt"))
            d.polygon([(cap[0] + 2, cap[3]), (cap[0], cap[3] + 5), (cap[0] + 4, cap[3] + 2)], fill=m("accent"))
            return
        d.ellipse(list(cap), fill=m("hair"))
        d.rectangle([cap[0], cap[3] - 3, cap[2], cap[3]], fill=m("hair"))
        # short side tufts framing the face, plain hair color only
        d.rectangle([cap[0], cap[3], cap[0] + 1, cap[3] + 4], fill=m("hair"))
        d.rectangle([cap[2] - 1, cap[3], cap[2], cap[3] + 4], fill=m("hair"))
        if hair == "spiky":
            for sx in (cap[0] + 4, 14, cap[2] - 7):
                d.polygon([(sx, cap[1] + 2), (sx + 2, cap[1] - 2), (sx + 4, cap[1] + 2)], fill=m("hair"))
        if hair == "long":
            d.rectangle([cap[0] - 1, cap[3], cap[0], t_top + 3], fill=m("hair"))
            d.rectangle([cap[2], cap[3], cap[2] + 1, t_top + 3], fill=m("hair"))
        if hair == "bun":
            d.ellipse([cap[2] - 5, cap[1] - 2, cap[2], cap[1] + 3], fill=m("hair"))
            d.ellipse([cap[2] - 4, cap[1] - 1, cap[2] - 1, cap[1] + 2], fill=m("hairShadow"))
        if hair == "pigtails":
            d.ellipse([cap[0] - 3, cap[3] - 2, cap[0] + 1, cap[3] + 4], fill=m("hair"))
            d.ellipse([cap[2] - 1, cap[3] - 2, cap[2] + 3, cap[3] + 4], fill=m("hair"))
        if hair == "bald_fringe":
            d.ellipse([cap[0] + 2, cap[1] + 2, cap[2] - 2, cap[3] + 1], fill=m("skin"))
            d.rectangle([cap[0], cap[3] - 2, cap[0] + 2, cap[3] + 4], fill=m("hair"))
            d.rectangle([cap[2] - 2, cap[3] - 2, cap[2], cap[3] + 4], fill=m("hair"))
        if headgear == "circlet":
            d.rectangle([cap[0] + 1, cap[3] - 2, cap[2] - 1, cap[3] - 1], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 2, cap[1] + 2, cap[2] - 2, cap[1] + 4], fill=m("gold"))
            for sx in (cap[0] + 4, 15, cap[2] - 5):
                d.rectangle([sx, cap[1], sx + 1, cap[1] + 2], fill=m("gold"))

    def back_hair():
        if headgear == "helm":
            d.ellipse([cap[0], cap[1], cap[2], cap[3] + 2], fill=m("metal"))
            d.rectangle([cap[0] + 4, cap[3] + 2, cap[2] - 4, face[3] - 1], fill=m("metalShadow"))
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] + 4, cap[3] - 1, cap[2] - 4, face[3]], fill=m("hair"))
            d.ellipse([cap[0] - 3, cap[3] - 3, cap[2] + 3, cap[3] + 2], fill=m("straw"))
            d.ellipse([cap[0] + 2, cap[1] + 1, cap[2] - 2, cap[3] - 1], fill=m("straw"))
            return
        if headgear == "kerchief":
            d.ellipse([cap[0] + 1, cap[1] + 1, cap[2] - 1, face[3] - 2], fill=m("accent"))
            d.polygon([(14, face[3] - 3), (17, face[3] - 3), (16, face[3] + 2), (15, face[3] + 2)],
                      fill=m("belt"))
            return
        # one clean rounded mass down to the chin line, thin shadow at the bottom
        d.ellipse([cap[0], cap[1], cap[2], face[3]], fill=m("hair"))
        d.ellipse([cap[0] + 4, face[3] - 3, cap[2] - 4, face[3]], fill=m("hairShadow"))
        if hair == "long":
            d.rectangle([cap[0] + 1, face[3] - 4, cap[2] - 1, t_top + 4], fill=m("hair"))
            d.rectangle([cap[0] + 1, t_top + 3, cap[2] - 1, t_top + 4], fill=m("hairShadow"))
        if hair == "bun":
            d.ellipse([13, cap[1] - 2, 20, cap[1] + 5], fill=m("hair"))
            d.ellipse([14, cap[1] - 1, 19, cap[1] + 4], fill=m("hairShadow"))
        if hair == "pigtails":
            d.ellipse([cap[0] - 3, cap[3] - 2, cap[0] + 1, cap[3] + 4], fill=m("hair"))
            d.ellipse([cap[2] - 1, cap[3] - 2, cap[2] + 3, cap[3] + 4], fill=m("hair"))
        if hair == "bald_fringe":
            d.ellipse([cap[0] + 3, cap[1] + 2, cap[2] - 3, cap[3]], fill=m("skin"))
            d.rectangle([cap[0] + 1, cap[3] - 1, cap[2] - 1, cap[3] + 5], fill=m("hair"))
            d.rectangle([cap[0] + 5, cap[3] + 6, cap[2] - 5, face[3] - 1], fill=m("skinShadow"))
        if headgear == "circlet":
            d.rectangle([cap[0] + 1, cap[3] - 2, cap[2] - 1, cap[3] - 1], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 2, cap[1] + 2, cap[2] - 2, cap[1] + 4], fill=m("gold"))

    def side_hair():
        if headgear == "helm":
            d.ellipse([cap[0] + 1, cap[1], cap[2] + 1, cap[3]], fill=m("metal"))
            d.rectangle([cap[2] - 4, cap[3] + 1, cap[2], cap[3] + 8], fill=m("metalShadow"))
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] - 2, cap[3] - 3, cap[2] + 4, cap[3] + 2], fill=m("straw"))
            d.ellipse([cap[0] + 3, cap[1] + 1, cap[2] - 1, cap[3] - 1], fill=m("straw"))
            return
        if headgear == "kerchief":
            d.ellipse([cap[0] + 2, cap[1] + 1, cap[2], face[3] - 4], fill=m("accent"))
            d.polygon([(cap[0] + 3, face[3] - 5), (cap[0] + 1, face[3]), (cap[0] + 6, face[3] - 3)],
                      fill=m("belt"))
            return
        # rounded cap + rounded back mass, no square blocks
        d.ellipse([cap[0] + 1, cap[1], cap[2] + 1, cap[3]], fill=m("hair"))
        d.ellipse([cap[0], cap[1] + 4, cap[0] + 9, face[3] - 2], fill=m("hair"))
        if hair == "spiky":
            d.polygon([(cap[0] + 4, cap[1] + 2), (cap[0] + 1, cap[1] - 1), (cap[0] + 6, cap[1] + 1)], fill=m("hair"))
        if hair == "long":
            d.rectangle([cap[0] + 1, cap[3], cap[0] + 5, t_top + 3], fill=m("hair"))
        if hair == "bun":
            d.ellipse([cap[0] - 1, cap[1] + 3, cap[0] + 4, cap[1] + 9], fill=m("hair"))
            d.ellipse([cap[0], cap[1] + 4, cap[0] + 3, cap[1] + 8], fill=m("hairShadow"))
        if hair == "pigtails":
            d.ellipse([cap[0] - 2, cap[3] - 2, cap[0] + 2, cap[3] + 4], fill=m("hair"))
        if hair == "bald_fringe":
            d.ellipse([cap[0] + 3, cap[1] + 2, cap[2], cap[3]], fill=m("skin"))
            d.rectangle([cap[0] + 1, cap[3] - 3, cap[0] + 5, cap[3] + 5], fill=m("hair"))
        if headgear == "circlet":
            d.rectangle([cap[0] + 2, cap[3] - 2, cap[2], cap[3] - 1], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 2, cap[1] + 2, cap[2], cap[1] + 4], fill=m("gold"))

    if direction == "down":
        front_hair()
    elif direction == "up":
        back_hair()
    else:
        side_hair()

    # ---------------- attack arm + blade (drawn over everything) ----------------
    if attack:
        if direction == "side":
            if attack == 1:  # windup: blade raised vertical in front of the face
                d.rectangle([side_arm[0] + 2, sh_y - 2, side_arm[1], sh_y + 1], fill=sleeve)
                d.rectangle([side_arm[1] - 1, sh_y - 4, side_arm[1] + 1, sh_y - 2], fill=m("skin"))
                d.rectangle([side_arm[1] - 2, sh_y - 5, side_arm[1] + 2, sh_y - 5], fill=m("gold"))
                vblade(side_arm[1] - 1, 6, sh_y - 6)
            else:  # strike: thrust forward
                d.rectangle([side_arm[1] - 3, sh_y + 1, side_arm[1] + 1, sh_y + 3], fill=sleeve)
                d.rectangle([side_arm[1] + 2, sh_y + 1, side_arm[1] + 3, sh_y + 3], fill=m("skin"))
                d.rectangle([side_arm[1] + 4, sh_y, side_arm[1] + 4, sh_y + 4], fill=m("gold"))
                hblade(side_arm[1] + 5, 30, sh_y + 1)
        elif direction == "down":
            akimbo_left(0)
            if attack == 1:  # windup: blade high over the right shoulder
                d.rectangle([t_r, sh_y - 2, t_r + 2, sh_y], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 4, t_r + 5, sh_y - 2], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y - 5, t_r + 6, sh_y - 5], fill=m("gold"))
                vblade(t_r + 4, 8, sh_y - 6)
            else:  # strike: blade swung down beside the leg
                d.rectangle([t_r, sh_y, t_r + 2, sh_y + 2], fill=sleeve)
                d.rectangle([t_r + 3, sh_y + 3, t_r + 5, sh_y + 5], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y + 6, t_r + 6, sh_y + 6], fill=m("gold"))
                d.rectangle([t_r + 4, sh_y + 7, t_r + 5, 40], fill=m("metal"))
                d.rectangle([t_r + 4, 41, t_r + 4, 42], fill=m("metal"))  # tip
        else:  # up
            akimbo_left(0)
            if attack == 1:  # windup: blade out to the side
                d.rectangle([t_r, sh_y - 1, t_r + 2, sh_y + 1], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 1, t_r + 4, sh_y + 1], fill=m("skin"))
                d.rectangle([t_r + 5, sh_y - 2, t_r + 5, sh_y + 2], fill=m("gold"))
                hblade(t_r + 6, 30, sh_y - 1)
            else:  # strike: blade raised high
                d.rectangle([t_r, sh_y - 1, t_r + 3, sh_y + 1], fill=sleeve)
                d.rectangle([t_r + 3, sh_y - 3, t_r + 5, sh_y - 1], fill=m("skin"))
                d.rectangle([t_r + 2, sh_y - 4, t_r + 6, sh_y - 4], fill=m("gold"))
                vblade(t_r + 3, 4, sh_y - 5)

    # ---------------- weapon on the back ----------------
    if spec.get("sword") and not attack:
        if direction == "up":
            d.line([(20, t_top + 2), (12, t_bot + 2)], fill=m("bootsShadow"), width=2)
            d.rectangle([20, t_top - 3, 21, t_top + 1], fill=m("wood"))
            d.rectangle([19, t_top + 1, 22, t_top + 1], fill=m("gold"))
        elif direction == "down":
            d.rectangle([25, t_top - 4, 26, t_top - 1], fill=m("wood"))
            d.rectangle([24, t_top - 1, 27, t_top - 1], fill=m("gold"))
    if spec.get("axe") and not attack:
        if direction == "up":
            d.line([(12, t_top + 1), (19, t_bot + 2)], fill=m("wood"), width=2)
            d.rectangle([9, t_top - 1, 13, t_top + 2], fill=m("metal"))
            d.rectangle([9, t_top + 2, 13, t_top + 2], fill=m("metalShadow"))
        elif direction == "down":
            d.rectangle([5, t_top - 4, 6, t_top - 1], fill=m("wood"))

    return img


# ---------------------------------------------------------------------------
# Character specs -- twelve unique sheets, no reuse.
# ---------------------------------------------------------------------------
CHARACTERS = {
    "player": dict(  # Dain Thorne
        spec=dict(hair="short", strap=True, sword=True, fighter=True, seed=3),
        bases=dict(hair="#4a3524", skin="#f0c9a2", torso="#4f6d80", accent="#6d4a30",
                   accent2="#65899c", belt="#8a6d42", pants="#33384c", boots="#5d4630",
                   wood="#7a5a38", gold="#d8b04a", metal="#b8bcc4", eye="#26303a"),
    ),
    "joran": dict(
        spec=dict(hair="spiky", strap=True, bracers=True, fighter=True, seed=7),
        bases=dict(hair="#8a6b40", skin="#e0b088", torso="#5d6653", accent="#54402b",
                   accent2="#6f7a63", belt="#6d5638", pants="#3d3c38", boots="#4a3826",
                   gold="#d8b04a", wood="#7a5a38", metal="#b8bcc4", eye="#2e2a22"),
    ),
    "king": dict(  # Alden -- royal, but a poor king of a poor land
        spec=dict(hair="short", beard=True, headgear="circlet", garment="robe", sash=True, seed=11),
        bases=dict(hair="#b8b2a8", skin="#dcb28c", torso="#7c2830", accent="#c9a44a",
                   accent2="#dcb054", beard="#c6c0b6", belt="#8a6d42", pants="#463824",
                   boots="#2e2620", gold="#e0bc54", eye="#2e2a26"),
    ),
    "marrow": dict(
        spec=dict(hair="bald_fringe", beard=True, garment="robe", staff=True, seed=13),
        bases=dict(hair="#cac4bc", skin="#c8a684", torso="#4e3c6a", accent="#8d7a3a",
                   accent2="#6a5690", beard="#d4cec6", belt="#8a6d42", pants="#3a3050",
                   boots="#2a2422", wood="#6d5334", orb="#5ac8b4", gold="#d8b04a",
                   eye="#2a2632"),
    ),
    "sela": dict(  # Sela Vane -- one-armed
        spec=dict(hair="bun", garment="dress", one_arm=True, seed=17),
        bases=dict(hair="#6d5335", skin="#e2ba92", torso="#7a5a48", accent="#a89070",
                   accent2="#8d6d58", belt="#54402b", pants="#5d4838", boots="#463424",
                   eye="#322a22"),
    ),
    "tobin": dict(  # farmer
        spec=dict(hair="short", headgear="straw_hat", garment="overalls", seed=19),
        bases=dict(hair="#3d2e1e", skin="#d8a878", torso="#a08858", accent="#54402b",
                   accent2="#b09868", belt="#6d5638", pants="#4e5c74", boots="#4a3826",
                   straw="#cbb26a", eye="#2a241c"),
    ),
    "yssa": dict(  # Tobin's wife -- greying bun, apron over her dress
        spec=dict(hair="bun", garment="dress", apron=True, seed=23),
        bases=dict(hair="#8a7a62", skin="#dcb090", torso="#6d5a45", accent="#8d7a62",
                   accent2="#b0a184", belt="#54452e", pants="#5d4f3d", boots="#463a28",
                   eye="#2e2820"),
    ),
    "garrick": dict(  # lumberjack -- bearded, axe on his back
        spec=dict(hair="short", beard=True, axe=True, seed=29),
        bases=dict(hair="#4a3a2a", skin="#d0a075", torso="#5d5038", accent="#3d3424",
                   accent2="#6d5e44", beard="#54422e", belt="#3a2f1e", pants="#44392b",
                   boots="#38291a", wood="#6d5334", metal="#9aa0a8", eye="#261f16"),
    ),
    "mira": dict(  # Garrick's wife -- kerchief
        spec=dict(headgear="kerchief", garment="dress", seed=31),
        bases=dict(hair="#5d452e", skin="#e0b490", torso="#75604c", accent="#8a5248",
                   accent2="#9a8266", belt="#54382e", pants="#5d4c3a", boots="#443626",
                   eye="#302620"),
    ),
    "wren": dict(  # Joran's little sister
        spec=dict(hair="pigtails", size="child", seed=37),
        bases=dict(hair="#7a5a34", skin="#f0c9a4", torso="#907a56", accent="#6d5a40",
                   accent2="#a08c64", belt="#6d5638", pants="#5d5240", boots="#54402b",
                   eye="#32301e"),
    ),
    "pell": dict(  # the Ashwoods' boy, nearly grown
        spec=dict(hair="spiky", size="teen", seed=41),
        bases=dict(hair="#3a2d1e", skin="#e2b48c", torso="#7a6a4a", accent="#54452c",
                   accent2="#8d7c58", belt="#5d4c30", pants="#4c4234", boots="#443322",
                   eye="#2a231a"),
    ),
    "soldier": dict(  # Solmeran regular -- crisp, well-kept gear
        spec=dict(headgear="helm", garment="armor", worn=False, seed=43),
        bases=dict(hair="#242220", skin="#d8a878", torso="#3d4148", accent="#5d2c2c",
                   accent2="#6d3434", metal="#8a8e96", belt="#3a3430", pants="#3a3e46",
                   boots="#26221e", gold="#c9a44a", eye="#26241e"),
    ),
}


# ---------------------------------------------------------------------------
# Dragons -- clean quadruped side profile, facing right.
# ---------------------------------------------------------------------------
def build_wyrmling(frame):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 2 if frame == "attack" else 0

    # tail: thick at the hip, curling up-left with a spade tip
    d.line([(5, 31 - bob), (1, 24 - bob)], fill=m("body"), width=3)
    d.polygon([(0, 25 - bob), (0, 20 - bob), (4, 23 - bob)], fill=m("horn"))
    # hind leg
    d.rectangle([6, 33 - bob, 10, 41], fill=m("bodyShadow"))
    d.rectangle([5, 40, 10, 42], fill=m("bodyShadow"))
    d.point([(5, 43), (8, 43)], fill=m("horn"))
    # horizontal body barrel
    d.ellipse([3, 22 - bob, 23, 37 - bob], fill=m("body"))
    d.ellipse([7, 28 - bob, 20, 36 - bob], fill=m("belly"))
    # folded wing lying along the back
    d.polygon([(7, 24 - bob), (13, 15 - bob), (20, 25 - bob)], fill=m("wing"))
    d.line([(12, 17 - bob), (18, 24 - bob)], fill=m("bodyShadow"))
    # spine spikes along the back
    for sx in (6, 10):
        d.polygon([(sx, 23 - bob), (sx + 1, 19 - bob), (sx + 3, 23 - bob)], fill=m("horn"))
    # foreleg (steps forward on lunge)
    d.rectangle([16 + lunge, 33 - bob, 20 + lunge, 41], fill=m("body"))
    d.rectangle([15 + lunge, 40, 20 + lunge, 42], fill=m("body"))
    d.point([(15 + lunge, 43), (18 + lunge, 43)], fill=m("horn"))
    # neck rising to a head at the upper right
    d.polygon([(17, 25 - bob), (19, 14 - bob), (26, 16 - bob), (23, 27 - bob)], fill=m("body"))
    hx = lunge
    d.ellipse([18 + hx, 6 - bob, 29 + hx, 17 - bob], fill=m("body"))
    d.ellipse([25 + hx, 10 - bob, 31 + hx, 15 - bob], fill=m("body"))  # snout
    d.point([(29 + hx, 11 - bob)], fill=m("bodyShadow"))
    if frame == "attack":
        d.polygon([(25 + hx, 14 - bob), (31 + hx, 12 - bob), (28 + hx, 18 - bob)], fill=m("maw"))
        d.point([(26 + hx, 14 - bob), (29 + hx, 13 - bob)], fill=m("horn"))
    else:
        d.line([(25 + hx, 14 - bob), (30 + hx, 13 - bob)], fill=m("bodyShadow"))
    # slit eye + brow
    d.rectangle([21 + hx, 10 - bob, 23 + hx, 11 - bob], fill=m("eye"))
    d.point([(22 + hx, 10 - bob)], fill=m("outline"))
    d.line([(20 + hx, 8 - bob), (24 + hx, 8 - bob)], fill=m("bodyShadow"))
    # swept-back horns
    d.polygon([(19 + hx, 7 - bob), (14 + hx, 3 - bob), (20 + hx, 4 - bob)], fill=m("horn"))
    d.polygon([(23 + hx, 6 - bob), (19 + hx, 1 - bob), (25 + hx, 3 - bob)], fill=m("horn"))
    return img


def build_skitterdrake(frame):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 1 if frame == "attack" else 0

    # long whip tail
    d.line([(5, 32 - bob), (0, 25 - bob)], fill=m("body"), width=2)
    # low, long body
    d.ellipse([2, 27 - bob, 24, 39 - bob], fill=m("body"))
    d.ellipse([6, 31 - bob, 21, 38 - bob], fill=m("belly"))
    # jagged back frill
    for fx in (5, 9, 13, 17):
        d.polygon([(fx, 28 - bob), (fx + 2, 23 - bob), (fx + 4, 28 - bob)], fill=m("horn"))
    # four short legs
    d.rectangle([5, 38 - bob, 8, 42], fill=m("bodyShadow"))
    d.rectangle([11, 38 - bob, 14, 42], fill=m("bodyShadow"))
    d.rectangle([17 + lunge, 38 - bob, 20 + lunge, 42], fill=m("body"))
    d.rectangle([23 + lunge, 38 - bob, 26 + lunge, 42], fill=m("body"))
    d.point([(6, 43), (12, 43), (18 + lunge, 43), (24 + lunge, 43)], fill=m("horn"))
    # head held low and forward, long flat snout
    hx = lunge
    d.ellipse([17 + hx, 16 - bob, 28 + hx, 27 - bob], fill=m("body"))
    d.rectangle([24 + hx, 20 - bob, 30 + hx, 25 - bob], fill=m("body"))
    d.point([(29 + hx, 21 - bob)], fill=m("bodyShadow"))
    if frame == "attack":
        d.polygon([(23 + hx, 24 - bob), (30 + hx, 22 - bob), (26 + hx, 28 - bob)], fill=m("maw"))
        d.point([(24 + hx, 24 - bob), (28 + hx, 23 - bob)], fill=m("horn"))
    else:
        d.line([(24 + hx, 24 - bob), (29 + hx, 23 - bob)], fill=m("bodyShadow"))
    # slit eye + brow
    d.rectangle([20 + hx, 19 - bob, 22 + hx, 20 - bob], fill=m("eye"))
    d.point([(21 + hx, 19 - bob)], fill=m("outline"))
    d.line([(19 + hx, 17 - bob), (23 + hx, 17 - bob)], fill=m("bodyShadow"))
    return img


DRAGONS = {
    "wyrmling": dict(
        build=build_wyrmling,
        bases=dict(body="#5f8e4e", belly="#c2cc8a", wing="#3d6238", horn="#ded6c2",
                   eye="#f0d23c", maw="#8e2c30"),
    ),
    "skitterdrake": dict(
        build=build_skitterdrake,
        bases=dict(body="#8a6d4e", belly="#cdbb95", wing="#6a5238", horn="#c2b088",
                   eye="#f0d23c", maw="#8e2c30"),
    ),
}


# ---------------------------------------------------------------------------
# Build + export
# ---------------------------------------------------------------------------
def main():
    preview = "preview" in sys.argv
    if preview:
        os.makedirs(PREVIEW_DIR, exist_ok=True)

    characters_out = {}
    for name, cfg in CHARACTERS.items():
        shapes = {}
        for direction in ("down", "up", "side"):
            shapes[direction] = {}
            for frame_name, step in (("idle", 0), ("step1", 1), ("step2", -1)):
                img = add_outline(build_humanoid(cfg["spec"], direction, step))
                shapes[direction][frame_name] = to_grid(img)
            if cfg["spec"].get("fighter"):
                for phase in (1, 2):
                    img = add_outline(build_humanoid(cfg["spec"], direction, 0, attack=phase))
                    shapes[direction][f"attack{phase}"] = to_grid(img)
        characters_out[name] = {"shapes": shapes,
                                "palette": make_palette(cfg["bases"], cfg["spec"].get("worn", True))}

    dragons_out = {}
    for name, cfg in DRAGONS.items():
        shapes = {}
        for frame_name in ("idle1", "idle2", "attack"):
            img = add_outline(cfg["build"](frame_name))
            shapes[frame_name] = to_grid(img)
        dragons_out[name] = {"shapes": shapes, "palette": make_palette(cfg["bases"], worn=False)}

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles_data.json")) as f:
        tiles = json.load(f)

    out = []
    out.append("// Hand-authored pixel-matrix art -- no external image files.")
    out.append("// Generated by tools/gen_pixel_art.py; edit that, not this.")
    out.append("// Twelve unique character sheets; nobody shares a sprite.")
    out.append("")
    out.append(f"export const CHARACTERS = {json.dumps(characters_out)};")
    out.append("")
    out.append(f"export const DRAGONS = {json.dumps(dragons_out)};")
    out.append("")
    out.append(f"export const TILES = {json.dumps(tiles)};")
    out.append("")
    with open(os.path.join(ROOT, "src", "data", "sprites.js"), "w") as f:
        f.write("\n".join(out))
    print("wrote src/data/sprites.js")

    if preview:
        def render(rows, palette, scale=8):
            h = len(rows)
            w = len(rows[0])
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            px = img.load()
            for yy, row in enumerate(rows):
                for xx, key in enumerate(row):
                    if key == ".":
                        continue
                    hexcol = palette.get(key)
                    if not hexcol:
                        continue
                    px[(xx, yy)] = rgb(hexcol) + (255,)
            return img.resize((w * scale, h * scale), Image.NEAREST)

        def sheet_of(cells):
            cw = max(c.width for c in cells)
            ch = max(c.height for c in cells)
            sheet = Image.new("RGBA", ((cw + 8) * len(cells) + 8, ch + 16), (222, 226, 230, 255))
            for i, c in enumerate(cells):
                sheet.paste(c, (8 + i * (cw + 8), 8), c)
            return sheet

        cells = [render(data["shapes"]["down"]["idle"], data["palette"]) for data in characters_out.values()]
        cells += [render(data["shapes"]["idle1"], data["palette"]) for data in dragons_out.values()]
        sheet_of(cells).save(os.path.join(PREVIEW_DIR, "cast.png"))

        cells = [render(data["shapes"]["up"]["idle"], data["palette"]) for data in characters_out.values()]
        sheet_of(cells).save(os.path.join(PREVIEW_DIR, "backs.png"))

        pdata = characters_out["player"]
        cells = []
        for direction in ("down", "up", "side"):
            for frame in ("idle", "attack1", "attack2"):
                cells.append(render(pdata["shapes"][direction][frame], pdata["palette"]))
        cells += [render(dragons_out[n]["shapes"]["attack"], dragons_out[n]["palette"])
                  for n in dragons_out]
        sheet_of(cells).save(os.path.join(PREVIEW_DIR, "attacks.png"))
        print("previews in", PREVIEW_DIR)


if __name__ == "__main__":
    main()
