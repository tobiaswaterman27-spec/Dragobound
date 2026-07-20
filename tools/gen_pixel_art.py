"""
Dragobound pixel-art generator (v3).

Produces every character and enemy as role-keyed pixel grids + per-character
palettes, written straight into src/data/sprites.js. Characters are drawn at
24x36 native with a parameterized humanoid builder: shared skeleton, but each
character gets its own authored components (hairstyle, headgear, beard,
garment type, props, missing-arm variant, child proportions) -- real designs,
not palette swaps.

Passes applied to every frame:
 - 1px outline around the silhouette (near-black with a cool cast)
 - auto top-edge highlight (light from above), hue-shifted warm
 - auto shadows are hue-shifted cool
 - boots get a darker grounding row where they meet the ground

Run: python3 tools/gen_pixel_art.py            # writes src/data/sprites.js
     python3 tools/gen_pixel_art.py preview    # also writes /tmp/pixel_preview/*.png
"""
import json
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 24, 36
PREVIEW_DIR = "/tmp/pixel_preview"

# ---------------------------------------------------------------------------
# Roles. Every drawable material gets a marker color (for the PIL stage) and a
# single character (for the exported grid).
# ---------------------------------------------------------------------------
ROLES = [
    "outline", "hair", "hairShadow", "skin", "skinShadow", "eye", "mouth",
    "beard", "torso", "torsoShadow", "accent", "cape", "capeShadow",
    "belt", "buckle", "pants", "pantsShadow", "boots", "bootsShadow",
    "metal", "metalShadow", "gold", "wood", "straw", "orb",
    # dragon-only roles
    "body", "bodyShadow", "belly", "wing", "horn", "maw",
]
MARKER = {}
for i, role in enumerate(ROLES):
    v = 8 + i * 7
    MARKER[role] = (v, (v * 3) % 251, (v * 7) % 251, 255)
MARKER_TO_ROLE = {v[:3]: k for k, v in MARKER.items()}

ROLE_CHAR = {
    "outline": "K", "hair": "H", "hairShadow": "h", "skin": "S", "skinShadow": "s",
    "eye": "E", "mouth": "U", "beard": "D", "torso": "T", "torsoShadow": "t",
    "accent": "A", "cape": "C", "capeShadow": "c", "belt": "Y", "buckle": "y",
    "pants": "P", "pantsShadow": "p", "boots": "O", "bootsShadow": "o",
    "metal": "M", "metalShadow": "m", "gold": "G", "wood": "W", "straw": "R",
    "orb": "Q",
    "body": "B", "bodyShadow": "b", "belly": "L", "wing": "V", "horn": "N",
    "maw": "X",
}

# groups for the auto-highlight pass: base role -> (siblings, highlight char)
HIGHLIGHT_GROUPS = {
    "hair": ({"hair", "hairShadow"}, "1"),
    "skin": ({"skin", "skinShadow"}, "2"),
    "torso": ({"torso", "torsoShadow"}, "3"),
    "pants": ({"pants", "pantsShadow"}, "4"),
    "boots": ({"boots", "bootsShadow"}, "5"),
    "cape": ({"cape", "capeShadow"}, "6"),
    "metal": ({"metal", "metalShadow"}, "7"),
    "beard": ({"beard"}, "8"),
    "body": ({"body", "bodyShadow"}, "!"),
    "belly": ({"belly"}, "@"),
}
GROUND_CHAR = "0"  # extra-dark bottom edge of boots
OCCLUDERS = {"belt", "buckle", "straw"}  # things below these get no top-light

ROLE_OF_GROUP_MEMBER = {}
for g, (members, _) in HIGHLIGHT_GROUPS.items():
    for r in members:
        ROLE_OF_GROUP_MEMBER[r] = g


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
    """Marker image -> role-char grid, applying auto highlight + grounding."""
    rows = []
    for y in range(img.height):
        row = ""
        for x in range(img.width):
            role = role_at(img, x, y)
            if role is None:
                row += "."
                continue
            ch = ROLE_CHAR[role]
            group = ROLE_OF_GROUP_MEMBER.get(role)
            if group and role == group:  # base tones only, not authored shadows
                above = role_at(img, x, y - 1)
                above_group = ROLE_OF_GROUP_MEMBER.get(above) if above else None
                if above_group != group and above != "outline" and above not in OCCLUDERS:
                    ch = HIGHLIGHT_GROUPS[group][1]
            if role == "boots":
                below = role_at(img, x, y + 1)
                if below is None or below == "outline":
                    ch = GROUND_CHAR
            row += ch
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Palette generation: hue-shifted ramps from per-character base colors.
# ---------------------------------------------------------------------------
WARM_LIGHT = (255, 244, 205)
COOL_DARK = (32, 26, 58)


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (1, 3, 5))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def make_palette(bases):
    """bases: subset of {hair, skin, torso, accent, cape, belt, pants, boots,
    metal, beard, wood, gold, straw, orb, eye, body, belly, wing, horn} -> hex."""
    pal = {"K": "#1a1424"}
    shadow_pairs = {
        "hair": ("H", "h"), "torso": ("T", "t"), "cape": ("C", "c"),
        "pants": ("P", "p"), "boots": ("O", "o"), "metal": ("M", "m"),
        "body": ("B", "b"),
    }
    plain = {
        "accent": "A", "belt": "Y", "beard": "D", "wood": "W", "gold": "G",
        "straw": "R", "orb": "Q", "belly": "L", "wing": "V", "horn": "N",
    }
    for role, (bc, sc) in shadow_pairs.items():
        if role not in bases:
            continue
        base = rgb(bases[role])
        pal[bc] = hexc(base)
        pal[sc] = hexc(mix(base, COOL_DARK, 0.38))
    for role, ch in plain.items():
        if role in bases:
            pal[ch] = bases[role]
    if "skin" in bases:
        base = rgb(bases["skin"])
        pal["S"] = hexc(base)
        pal["s"] = hexc(mix(base, COOL_DARK, 0.22))
    if "belt" in bases:
        pal["y"] = hexc(mix(rgb(bases["belt"]), COOL_DARK, 0.35))
    pal["E"] = bases.get("eye", "#181418")
    # mouth: a subtle darkening of that character's skin, not a red slash
    if "skin" in bases:
        pal["U"] = hexc(mix(rgb(bases["skin"]), (96, 40, 36), 0.45))
    else:
        pal["U"] = "#7a3c34"
    pal["X"] = bases.get("maw", "#8e2c30")
    for group, (_members, hl_ch) in HIGHLIGHT_GROUPS.items():
        src = {"body": "body", "belly": "belly"}.get(group, group)
        if src in bases:
            base = rgb(bases[src])
            t = 0.16 + 0.24 * (luminance(base) / 255.0)
            pal[hl_ch] = hexc(mix(base, WARM_LIGHT, t))
    return pal


# ---------------------------------------------------------------------------
# Humanoid builder. Coordinates assume 24x36; child specs shift + shrink.
# ---------------------------------------------------------------------------
def build_humanoid(spec, direction, step):
    """spec: dict of component options. direction: down|up|side. step: 0|1|-1."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    child = spec.get("child", False)
    dy = 8 if child else 0           # children: head sits lower (whole figure shorter)
    arm_off = -step                  # arms swing opposite to legs

    garment = spec.get("garment", "tunic")
    robe_like = garment in ("robe", "dress")

    # segment layout: children get a short torso and stubby legs that still
    # fit the frame, adults use the full 36 rows
    if child:
        t_top, t_bot, t_l, t_r = 22, 29, 7, 16
        l_top, l_bot, b_top, b_bot = 30, 32, 33, 35
        ll, rl = (8, 10), (13, 15)
        a_slv, a_hand = (23, 26), (27, 28)
        arm_l, arm_r = (5, 6), (17, 18)
        side_arm = (12, 15)
    else:
        t_top, t_bot, t_l, t_r = 14, 24, 6, 17
        l_top, l_bot, b_top, b_bot = 26, 31, 32, 35
        ll, rl = (7, 10), (13, 16)
        a_slv, a_hand = (15, 20), (21, 23)
        arm_l, arm_r = (4, 5), (18, 19)
        side_arm = (13, 16)

    # ---- cape, seen from the front/side (drawn first, behind everything).
    # The back view gets a full cape overlay later, on top of the garment. ----
    if spec.get("cape") and direction == "down":
        d.rectangle([5, 14, 6, 26], fill=m("capeShadow"))
        d.rectangle([17, 14, 18, 26], fill=m("capeShadow"))
    elif spec.get("cape") and direction == "side":
        # trailing behind only (character faces right)
        d.rectangle([4, 14, 7, 27], fill=m("cape"))
        d.rectangle([4, 14, 4, 27], fill=m("capeShadow"))
        d.rectangle([4, 25, 7, 27], fill=m("capeShadow"))

    # ---- legs & footwear ----
    lo = max(step, 0)
    ro = max(-step, 0)
    if robe_like:
        pass  # skirt covers the legs; small boots added after the garment
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

    # ---- torso / garment ----
    if robe_like:
        # long garment: torso block widening into a skirt that sways as you walk
        d.rectangle([6, 14 + dy, 17, 23 + dy], fill=m("torso"))
        d.polygon([(6, 24 + dy), (17, 24 + dy), (19, 33 + dy), (4, 33 + dy)], fill=m("torso"))
        d.rectangle([6, 14 + dy, 6, 23 + dy], fill=m("torsoShadow"))
        d.rectangle([17, 14 + dy, 17, 23 + dy], fill=m("torsoShadow"))
        sway = step
        d.rectangle([4, 33 + dy, 19, 33 + dy], fill=m("torsoShadow"))
        if direction != "up":
            d.rectangle([8, 14 + dy, 8, 33 + dy], fill=m("accent"))
            d.rectangle([15, 14 + dy, 15, 33 + dy], fill=m("accent"))
        # feet peeking out
        d.rectangle([8 + sway, 34 + dy, 10 + sway, 35 + dy], fill=m("boots"))
        d.rectangle([13 + sway, 34 + dy, 15 + sway, 35 + dy], fill=m("boots"))
    elif garment == "overalls":
        d.rectangle([6, 14 + dy, 17, 17 + dy], fill=m("torso"))       # shirt
        d.rectangle([6, 18 + dy, 17, 25 + dy], fill=m("pants"))       # overall body
        d.rectangle([8, 14 + dy, 9, 17 + dy], fill=m("pants"))        # straps
        d.rectangle([14, 14 + dy, 15, 17 + dy], fill=m("pants"))
        d.rectangle([10, 19 + dy, 13, 22 + dy], fill=m("pantsShadow"))  # bib pocket
    elif garment == "armor":
        d.rectangle([6, 14 + dy, 17, 24 + dy], fill=m("metal"))
        d.rectangle([6, 14 + dy, 7, 24 + dy], fill=m("metalShadow"))
        d.rectangle([16, 14 + dy, 17, 24 + dy], fill=m("metalShadow"))
        d.rectangle([9, 18 + dy, 14, 27 + dy], fill=m("accent"))      # tabard
        d.rectangle([11, 18 + dy, 12, 27 + dy], fill=m("gold"))       # tabard stripe
        # pauldrons
        d.rectangle([4, 14 + dy, 6, 16 + dy], fill=m("metal"))
        d.rectangle([17, 14 + dy, 19, 16 + dy], fill=m("metal"))
    else:  # tunic
        d.rectangle([t_l, t_top, t_r, t_bot], fill=m("torso"))
        d.rectangle([t_l, t_top, t_l, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r, t_top, t_r, t_bot], fill=m("torsoShadow"))
        if spec.get("strap") and direction == "down":
            # leather strap across the chest
            for i in range(10):
                x = t_l + 1 + i
                y = t_top + 1 + i * 0.9
                d.rectangle([x, int(y), x, int(y) + 1], fill=m("accent"))
        if spec.get("strap") and direction == "up":
            for i in range(10):
                x = t_r - 1 - i
                y = t_top + 1 + i * 0.9
                d.rectangle([x, int(y), x, int(y) + 1], fill=m("accent"))

    # belt (not for robes/overalls; children go without)
    if garment in ("tunic", "armor") and not child:
        d.rectangle([6, 24, 17, 25], fill=m("belt"))
        if direction == "down":
            d.rectangle([11, 24, 12, 25], fill=m("buckle"))

    # ---- arms ----
    sleeve = m("metal") if garment == "armor" else m("torso")
    if direction == "side":
        d.rectangle([side_arm[0], a_slv[0] + 1 + arm_off, side_arm[1], a_slv[1] + 1 + arm_off], fill=sleeve)
        # shadowed left edge so the arm reads as a separate limb over the torso
        d.rectangle([side_arm[0], a_slv[0] + 1 + arm_off, side_arm[0], a_slv[1] + 1 + arm_off],
                    fill=m("metalShadow") if garment == "armor" else m("torsoShadow"))
        d.rectangle([side_arm[0], a_hand[0] + 1 + arm_off, side_arm[1], a_hand[1] + arm_off], fill=m("skin"))
        if spec.get("staff"):
            d.rectangle([17, 6, 18, 33], fill=m("wood"))
            d.ellipse([16, 3, 19, 6], fill=m("orb"))
    else:
        left_arm = not (spec.get("one_arm") and direction == "down")
        right_arm = not (spec.get("one_arm") and direction == "up")
        if left_arm:
            d.rectangle([arm_l[0], a_slv[0] + arm_off, arm_l[1], a_slv[1] + arm_off], fill=sleeve)
            d.rectangle([arm_l[0], a_hand[0] + arm_off, arm_l[1], a_hand[1] + arm_off], fill=m("skin"))
            if spec.get("bracers"):
                d.rectangle([arm_l[0], a_slv[1] + arm_off, arm_l[1], a_hand[0] + arm_off], fill=m("belt"))
        else:
            # pinned empty sleeve, folded at the elbow
            d.rectangle([arm_l[0], a_slv[0], arm_l[1], a_slv[1] - 1], fill=sleeve)
            d.rectangle([arm_l[0], a_slv[1] - 1, arm_l[1], a_slv[1]], fill=m("torsoShadow"))
        if right_arm:
            d.rectangle([arm_r[0], a_slv[0] - arm_off, arm_r[1], a_slv[1] - arm_off], fill=sleeve)
            d.rectangle([arm_r[0], a_hand[0] - arm_off, arm_r[1], a_hand[1] - arm_off], fill=m("skin"))
            if spec.get("bracers"):
                d.rectangle([arm_r[0], a_slv[1] - arm_off, arm_r[1], a_hand[0] - arm_off], fill=m("belt"))
        else:
            d.rectangle([arm_r[0], a_slv[0], arm_r[1], a_slv[1] - 1], fill=sleeve)
            d.rectangle([arm_r[0], a_slv[1] - 1, arm_r[1], a_slv[1]], fill=m("torsoShadow"))
        if spec.get("staff") and direction == "down":
            d.rectangle([19, 6, 20, 33], fill=m("wood"))
            d.ellipse([18, 3, 21, 6], fill=m("orb"))

    # ---- full cape overlay for the back view: covers garment and arms ----
    if spec.get("cape") and direction == "up":
        d.rectangle([5, 14, 18, 28], fill=m("cape"))
        d.rectangle([5, 14, 5, 28], fill=m("capeShadow"))
        d.rectangle([18, 14, 18, 28], fill=m("capeShadow"))
        d.rectangle([5, 26, 18, 28], fill=m("capeShadow"))

    # ---- head ----
    hair = spec.get("hair", "short")
    headgear = spec.get("headgear")
    if direction == "down":
        d.ellipse([7, 4 + dy, 16, 13 + dy], fill=m("skin"))
        # eyes with brows
        d.rectangle([9, 9 + dy, 10, 10 + dy], fill=m("eye"))
        d.rectangle([13, 9 + dy, 14, 10 + dy], fill=m("eye"))
        d.point([(9, 9 + dy), (13, 9 + dy)], fill=(255, 255, 255, 255))
        d.point([(11, 11 + dy), (12, 11 + dy)], fill=m("skinShadow"))  # nose
        if spec.get("beard"):
            d.rectangle([8, 12 + dy, 15, 15 + dy], fill=m("beard"))
            d.rectangle([10, 12 + dy, 13, 12 + dy], fill=m("beard"))   # mustache
            d.rectangle([11, 13 + dy, 12, 13 + dy], fill=m("mouth"))
        else:
            d.rectangle([11, 12 + dy, 12, 12 + dy], fill=m("mouth"))
    elif direction == "up":
        d.ellipse([7, 4 + dy, 16, 13 + dy], fill=m("skinShadow"))  # mostly covered by hair
    else:  # side (faces right)
        d.ellipse([8, 4 + dy, 17, 13 + dy], fill=m("skin"))
        d.rectangle([14, 9 + dy, 15, 10 + dy], fill=m("eye"))
        d.point([(14, 9 + dy)], fill=(255, 255, 255, 255))
        d.point([(17, 10 + dy)], fill=m("skinShadow"))  # nose bump
        if spec.get("beard"):
            d.rectangle([11, 12 + dy, 16, 15 + dy], fill=m("beard"))
        else:
            d.point([(15, 12 + dy)], fill=m("mouth"))

    # hair / headgear on top
    def hair_down_up(front):
        if headgear == "helm":
            d.ellipse([6, 1 + dy, 17, 9 + dy], fill=m("metal"))
            d.rectangle([6, 6 + dy, 7, 12 + dy], fill=m("metal"))    # cheek guards
            d.rectangle([16, 6 + dy, 17, 12 + dy], fill=m("metal"))
            d.rectangle([6, 5 + dy, 6, 8 + dy], fill=m("metalShadow"))
            if front:
                d.rectangle([11, 5 + dy, 12, 8 + dy], fill=m("metalShadow"))  # nose guard
            return
        if headgear == "straw_hat":
            d.ellipse([3, 5 + dy, 20, 8 + dy], fill=m("straw"))       # brim
            d.ellipse([7, 1 + dy, 16, 7 + dy], fill=m("straw"))       # dome
            d.rectangle([7, 5 + dy, 16, 5 + dy], fill=m("belt"))      # hat band
            return
        if hair == "spiky":
            d.ellipse([6, 2 + dy, 17, 8 + dy], fill=m("hair"))
            for sx in (7, 10, 13):
                d.polygon([(sx, 3 + dy), (sx + 1, 0 + dy), (sx + 3, 3 + dy)], fill=m("hair"))
        elif hair == "bun":
            d.ellipse([6, 2 + dy, 17, 8 + dy], fill=m("hair"))
            d.ellipse([14, 1 + dy, 18, 4 + dy], fill=m("hairShadow" if front else "hair"))
        elif hair == "long":
            d.ellipse([6, 2 + dy, 17, 8 + dy], fill=m("hair"))
            d.rectangle([5, 6 + dy, 6, 15 + dy], fill=m("hair"))
            d.rectangle([17, 6 + dy, 18, 15 + dy], fill=m("hair"))
        elif hair == "bald_fringe":
            d.rectangle([6, 6 + dy, 7, 9 + dy], fill=m("hair"))
            d.rectangle([16, 6 + dy, 17, 9 + dy], fill=m("hair"))
        else:  # short
            d.ellipse([6, 2 + dy, 17, 8 + dy], fill=m("hair"))
        if not front:
            # back of head: hair falls lower
            if hair != "bald_fringe":
                d.ellipse([6, 2 + dy, 17, 11 + dy], fill=m("hair"))
                d.rectangle([6, 8 + dy, 8, 10 + dy], fill=m("hairShadow"))
            if hair == "bun":
                d.ellipse([10, 1 + dy, 15, 6 + dy], fill=m("hair"))
                d.ellipse([11, 2 + dy, 14, 5 + dy], fill=m("hairShadow"))
        else:
            # fringe notches over the forehead
            if hair in ("short", "spiky", "long"):
                d.rectangle([7, 5 + dy, 8, 6 + dy], fill=m("hair"))
                d.rectangle([10, 5 + dy, 11, 6 + dy], fill=m("hair"))
                d.rectangle([14, 5 + dy, 16, 6 + dy], fill=m("hair"))
        if headgear == "circlet":
            d.rectangle([6, 4 + dy, 17, 4 + dy], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([6, 3 + dy, 17, 4 + dy], fill=m("gold"))
            for sx in (7, 11, 15):
                d.point([(sx, 2 + dy)], fill=m("gold"))

    if direction in ("down", "up"):
        hair_down_up(front=(direction == "down"))
    else:  # side profile hair
        if headgear == "helm":
            d.ellipse([7, 1 + dy, 18, 9 + dy], fill=m("metal"))
            d.rectangle([7, 6 + dy, 9, 12 + dy], fill=m("metalShadow"))
        elif headgear == "straw_hat":
            d.ellipse([4, 5 + dy, 21, 8 + dy], fill=m("straw"))
            d.ellipse([8, 1 + dy, 17, 7 + dy], fill=m("straw"))
        else:
            d.ellipse([7, 1 + dy, 17, 7 + dy], fill=m("hair"))
            d.rectangle([7, 5 + dy, 9, 12 + dy], fill=m("hair"))     # hair back mass
            d.rectangle([7, 8 + dy, 7, 11 + dy], fill=m("hairShadow"))
            if hair == "spiky":
                d.polygon([(8, 2 + dy), (6, 0 + dy), (9, 1 + dy)], fill=m("hair"))
            if hair == "bun":
                d.ellipse([5, 3 + dy, 9, 7 + dy], fill=m("hair"))
                d.ellipse([6, 4 + dy, 8, 6 + dy], fill=m("hairShadow"))
            if hair == "long":
                d.rectangle([7, 6 + dy, 9, 16 + dy], fill=m("hair"))
            if headgear == "circlet":
                d.rectangle([8, 4 + dy, 17, 4 + dy], fill=m("gold"))
            if headgear == "crown":
                d.rectangle([8, 3 + dy, 17, 4 + dy], fill=m("gold"))

    # ---- sword on the back (visible from behind; hilt peeks over the shoulder) ----
    if spec.get("sword"):
        if direction == "up":
            d.line([(15, 15 + dy), (9, 27 + dy)], fill=m("bootsShadow"), width=2)
            d.rectangle([15, 12 + dy, 16, 14 + dy], fill=m("wood"))
            d.rectangle([14, 14 + dy, 17, 14 + dy], fill=m("gold"))
        elif direction == "down":
            d.rectangle([17, 11 + dy, 18, 12 + dy], fill=m("wood"))
            d.rectangle([16, 13 + dy, 19, 13 + dy], fill=m("gold"))

    return img


# ---------------------------------------------------------------------------
# Character specs + base colors: this is where each design lives.
# ---------------------------------------------------------------------------
CHARACTERS = {
    "player": dict(
        spec=dict(hair="short", cape=True, strap=True, sword=True),
        bases=dict(hair="#4a3524", skin="#eec39a", torso="#4f6d80", accent="#6d4a30",
                   cape="#a02c30", belt="#8a6d42", pants="#33384c", boots="#5d4630",
                   wood="#7a5a38", gold="#d8b04a", eye="#181418"),
    ),
    "joran": dict(
        spec=dict(hair="short", strap=True, bracers=True),
        bases=dict(hair="#8a6b40", skin="#e0b088", torso="#5d6653", accent="#54402b",
                   belt="#6d5638", pants="#3d3c38", boots="#4a3826",
                   gold="#d8b04a", wood="#7a5a38", eye="#181418"),
    ),
    "king": dict(
        spec=dict(hair="short", beard=True, headgear="circlet", garment="robe"),
        bases=dict(hair="#b8b2a8", skin="#dcb28c", torso="#7c2830", accent="#c9a44a",
                   beard="#c6c0b6", belt="#8a6d42", pants="#463824", boots="#2e2620",
                   gold="#e0bc54", eye="#181418"),
    ),
    "marrow": dict(
        spec=dict(hair="bald_fringe", beard=True, garment="robe", staff=True),
        bases=dict(hair="#cac4bc", skin="#c8a684", torso="#4e3c6a", accent="#8d7a3a",
                   beard="#d4cec6", belt="#8a6d42", pants="#3a3050", boots="#2a2422",
                   wood="#6d5334", orb="#5ac8b4", gold="#d8b04a", eye="#181418"),
    ),
    "villager_f": dict(  # Sela Vane -- one-armed, shawl-and-dress
        spec=dict(hair="bun", garment="dress", one_arm=True),
        bases=dict(hair="#6d5335", skin="#e2ba92", torso="#7a5a48", accent="#a89070",
                   belt="#54402b", pants="#5d4838", boots="#463424", eye="#181418"),
    ),
    "villager_m": dict(  # Tobin / Garrick -- farmer
        spec=dict(hair="short", headgear="straw_hat", garment="overalls"),
        bases=dict(hair="#3d2e1e", skin="#d8a878", torso="#a08858", accent="#54402b",
                   belt="#6d5638", pants="#4e5c74", boots="#4a3826",
                   straw="#cbb26a", eye="#181418"),
    ),
    "child": dict(  # Wren / Pell
        spec=dict(hair="spiky", child=True),
        bases=dict(hair="#b08c3c", skin="#eec4a2", torso="#8c8a52", accent="#6d5a30",
                   belt="#6d5638", pants="#5d5240", boots="#54402b", eye="#181418"),
    ),
    "soldier": dict(
        spec=dict(headgear="helm", garment="armor"),
        bases=dict(hair="#242220", skin="#d8a878", torso="#3d4148", accent="#5d2c2c",
                   metal="#8a8e96", belt="#3a3430", pants="#3a3e46", boots="#26221e",
                   gold="#c9a44a", eye="#181418"),
    ),
}


# ---------------------------------------------------------------------------
# Dragons: two distinct species, three frames each (idle1, idle2, attack).
# ---------------------------------------------------------------------------
def build_wyrmling(frame):
    """Compact juvenile with folded wings. Faces right."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 3 if frame == "attack" else 0
    y = 0 if frame != "attack" else 0

    # tail (curls up behind)
    d.line([(4, 28 - bob), (0, 20 - bob)], fill=m("body"), width=3)
    d.polygon([(0, 21 - bob), (0, 17 - bob), (3, 20 - bob)], fill=m("horn"))
    # hind leg
    d.rectangle([5, 29 - bob, 8, 34], fill=m("bodyShadow"))
    d.rectangle([4, 34, 8, 35], fill=m("bodyShadow"))
    # body
    d.ellipse([3, 16 - bob, 17, 31 - bob], fill=m("body"))
    d.ellipse([6, 21 - bob, 15, 30 - bob], fill=m("belly"))
    # folded wing over the back
    d.polygon([(4, 18 - bob), (2, 10 - bob), (12, 16 - bob)], fill=m("wing"))
    d.line([(3, 11 - bob), (11, 16 - bob)], fill=m("bodyShadow"))
    # spine spikes
    for sx in (8, 11, 14):
        d.polygon([(sx, 16 - bob), (sx + 1, 13 - bob), (sx + 2, 16 - bob)], fill=m("bodyShadow"))
    # front leg (raises on attack)
    d.rectangle([12 + lunge, 27 - bob - lunge, 15 + lunge, 34 - lunge], fill=m("body"))
    d.rectangle([12 + lunge, 34 - lunge, 16 + lunge, 35 - lunge], fill=m("bodyShadow"))
    d.point([(16 + lunge, 35 - lunge)], fill=m("horn"))
    # neck + head
    hx = 11 + lunge
    d.ellipse([hx, 6 - bob, hx + 11, 17 - bob], fill=m("body"))
    d.ellipse([hx + 6, 10 - bob, hx + 12, 15 - bob], fill=m("body"))  # snout
    if frame == "attack":
        d.polygon([(hx + 6, 15 - bob), (hx + 12, 15 - bob), (hx + 9, 19 - bob)], fill=m("maw"))
        d.point([(hx + 7, 15 - bob), (hx + 11, 15 - bob)], fill=m("horn"))  # fangs
    else:
        d.line([(hx + 6, 14 - bob), (hx + 11, 14 - bob)], fill=m("bodyShadow"))
    d.rectangle([hx + 3, 9 - bob, hx + 4, 10 - bob], fill=m("eye"))
    d.point([(hx + 10, 11 - bob)], fill=m("bodyShadow"))  # nostril
    # horns
    d.line([(hx + 3, 6 - bob), (hx + 1, 2 - bob)], fill=m("horn"), width=1)
    d.line([(hx + 6, 6 - bob), (hx + 7, 2 - bob)], fill=m("horn"), width=1)
    return img


def build_skitterdrake(frame):
    """Long, low, wingless scavenger with a back frill. Faces right."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 3 if frame == "attack" else 0

    # long tail low behind
    d.line([(5, 28 - bob), (0, 24 - bob)], fill=m("body"), width=2)
    d.line([(2, 25 - bob), (0, 22 - bob)], fill=m("bodyShadow"), width=1)
    # legs (four, splayed)
    for lx in (4, 9):
        d.rectangle([lx, 30 - bob, lx + 2, 35], fill=m("bodyShadow"))
    for lx in (13 + lunge, 18 + lunge):
        d.rectangle([lx, 30 - bob, lx + 2, 35], fill=m("body"))
    # long low body
    d.ellipse([2, 20 - bob, 20, 31 - bob], fill=m("body"))
    d.ellipse([5, 24 - bob, 17, 30 - bob], fill=m("belly"))
    # back frill spikes
    for sx in (5, 8, 11, 14):
        d.polygon([(sx, 21 - bob), (sx + 1, 17 - bob), (sx + 3, 21 - bob)], fill=m("horn"))
    # narrow head on a low neck, long snout
    hx = 14 + lunge
    d.ellipse([hx, 13 - bob, hx + 9, 22 - bob], fill=m("body"))
    d.rectangle([hx + 6, 16 - bob, hx + 9, 20 - bob], fill=m("body"))
    if frame == "attack":
        d.polygon([(hx + 5, 19 - bob), (hx + 9, 18 - bob), (hx + 8, 22 - bob)], fill=m("maw"))
    else:
        d.line([(hx + 4, 19 - bob), (hx + 9, 19 - bob)], fill=m("bodyShadow"))
    d.rectangle([hx + 3, 15 - bob, hx + 4, 16 - bob], fill=m("eye"))
    d.point([(hx + 8, 17 - bob)], fill=m("bodyShadow"))
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
# Build everything and write src/data/sprites.js
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
        characters_out[name] = {"shapes": shapes, "palette": make_palette(cfg["bases"])}

    dragons_out = {}
    for name, cfg in DRAGONS.items():
        shapes = {}
        for frame_name in ("idle1", "idle2", "attack"):
            img = add_outline(cfg["build"](frame_name))
            shapes[frame_name] = to_grid(img)
        dragons_out[name] = {"shapes": shapes, "palette": make_palette(cfg["bases"])}

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles_data.json")) as f:
        tiles = json.load(f)

    out = []
    out.append("// Hand-authored pixel-matrix art -- no external image files.")
    out.append("// Generated by tools/gen_pixel_art.py; edit that, not this.")
    out.append("// Each character has its own authored shape set (24x36) + palette.")
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
        def render(rows, palette, scale=10):
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

        # contact sheet: all characters down-idle + both dragons idle1
        cells = []
        for name, data in characters_out.items():
            cells.append(render(data["shapes"]["down"]["idle"], data["palette"]))
        for name, data in dragons_out.items():
            cells.append(render(data["shapes"]["idle1"], data["palette"]))
        cw = max(c.width for c in cells)
        ch = max(c.height for c in cells)
        sheet = Image.new("RGBA", ((cw + 8) * len(cells) + 8, ch + 16), (222, 226, 230, 255))
        for i, c in enumerate(cells):
            sheet.paste(c, (8 + i * (cw + 8), 8), c)
        sheet.save(os.path.join(PREVIEW_DIR, "cast.png"))

        # player, all directions/frames
        pdata = characters_out["player"]
        cells = []
        for direction in ("down", "up", "side"):
            for frame in ("idle", "step1", "step2"):
                cells.append(render(pdata["shapes"][direction][frame], pdata["palette"]))
        sheet = Image.new("RGBA", ((cw + 8) * len(cells) + 8, ch + 16), (222, 226, 230, 255))
        for i, c in enumerate(cells):
            sheet.paste(c, (8 + i * (cw + 8), 8), c)
        sheet.save(os.path.join(PREVIEW_DIR, "player_dirs.png"))
        print("previews in", PREVIEW_DIR)


if __name__ == "__main__":
    main()
