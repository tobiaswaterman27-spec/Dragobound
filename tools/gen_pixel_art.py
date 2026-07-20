"""
Dragobound pixel-art generator (v4).

32x44 native chibi proportions (head is ~half the figure, like GBA-era
Pokemon overworld sprites) with per-character authored designs: hairstyles,
headgear, beards, garments, props, a one-armed variant, child proportions.
No capes.

Automatic finishing passes on every frame:
 - 1px silhouette outline (near-black, cool cast)
 - top-edge warm highlight (light from above)
 - right/bottom-edge cool shadow at the silhouette (cylindrical form)
 - boots darken where they meet the ground

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
    "outline", "hair", "hairShadow", "skin", "skinShadow", "eye", "mouth",
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
    "eye": "E", "mouth": "U", "beard": "D", "beardShadow": "d",
    "torso": "T", "torsoShadow": "t", "accent": "A", "accent2": "a",
    "belt": "Y", "buckle": "y", "pants": "P", "pantsShadow": "p",
    "boots": "O", "bootsShadow": "o", "metal": "M", "metalShadow": "m",
    "gold": "G", "wood": "W", "straw": "R", "strawShadow": "r", "orb": "Q",
    "body": "B", "bodyShadow": "b", "belly": "L", "bellyShadow": "l",
    "wing": "V", "horn": "N", "maw": "X",
}

# groups: base role -> (member roles, highlight char, shadow char or None)
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
    """Marker image -> role-char grid with the finishing light/shadow passes."""
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
            if group and role == group:  # base tones only
                members, hl_ch, sh_ch = GROUPS[group]
                above = role_at(img, x, y - 1)
                right = role_at(img, x + 1, y)
                below = role_at(img, x, y + 1)
                above_group = ROLE_TO_GROUP.get(above) if above else None
                # priority: grounding > top-light > edge shadow
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


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (1, 3, 5))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def make_palette(bases):
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
        base = rgb(bases[role])
        pal[bc] = hexc(base)
        pal[sc] = hexc(mix(base, COOL_DARK, 0.34))
    for role, ch in plain.items():
        if role in bases:
            pal[ch] = bases[role]
    if "skin" in bases:
        base = rgb(bases["skin"])
        pal["S"] = hexc(base)
        pal["s"] = hexc(mix(base, COOL_DARK, 0.20))
        pal["U"] = hexc(mix(base, (96, 40, 36), 0.45))
    else:
        pal["U"] = "#7a3c34"
    if "belt" in bases:
        pal["y"] = hexc(mix(rgb(bases["belt"]), COOL_DARK, 0.35))
    pal["E"] = bases.get("eye", "#181418")
    pal["X"] = bases.get("maw", "#8e2c30")
    for group, (_members, hl_ch, _sc) in GROUPS.items():
        if group in bases:
            base = rgb(bases[group])
            t = 0.15 + 0.25 * (luminance(base) / 255.0)
            pal[hl_ch] = hexc(mix(base, WARM_LIGHT, t))
    return pal


# ---------------------------------------------------------------------------
# Humanoid builder -- chibi proportions, 32x44.
# ---------------------------------------------------------------------------
def build_humanoid(spec, direction, step, attack=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    child = spec.get("child", False)
    arm_off = -step
    garment = spec.get("garment", "tunic")
    robe_like = garment in ("robe", "dress")

    # ---------------- layout ----------------
    if child:
        hd = dict(cap=(9, 12, 22, 21), face=(10, 15, 21, 30), eye_y=24,
                  eyes=((12, 14), (18, 20)), nose=(15, 27), mouth=(15, 29))
        t_top, t_bot, t_l, t_r = 31, 37, 10, 21
        l_top, l_bot, b_top, b_bot = 38, 40, 41, 43
        ll, rl = (11, 14), (17, 20)
        a_slv, a_hand = (32, 35), (36, 37)
        arm_l, arm_r = (7, 9), (22, 24)
        side_arm = (16, 20)
    else:
        # GBA-Pokemon proportions: the head is well over half the figure, the
        # body a short block with stubby legs
        hd = dict(cap=(7, 4, 24, 15), face=(8, 8, 23, 25), eye_y=18,
                  eyes=((11, 13), (19, 21)), nose=(15, 22), mouth=(15, 24))
        t_top, t_bot, t_l, t_r = 26, 35, 9, 22
        l_top, l_bot, b_top, b_bot = 36, 39, 40, 43
        ll, rl = (10, 14), (17, 21)
        a_slv, a_hand = (27, 31), (32, 34)
        arm_l, arm_r = (6, 8), (23, 25)
        side_arm = (16, 21)

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
        # boot cuffs
        d.rectangle([ll[0], b_top + lo, ll[1], b_top + lo], fill=m("bootsShadow"))
        d.rectangle([rl[0], b_top + ro, rl[1], b_top + ro], fill=m("bootsShadow"))

    # ---------------- torso / garment ----------------
    if robe_like:
        d.rectangle([t_l - 1, t_top, t_r + 1, t_bot], fill=m("torso"))
        sway = step
        d.polygon([(t_l - 1, t_bot), (t_r + 1, t_bot), (t_r + 2, 41), (t_l - 2, 41)], fill=m("torso"))
        d.rectangle([t_l - 1, t_top, t_l - 1, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r + 1, t_top, t_r + 1, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_l - 2, 40, t_r + 2, 41], fill=m("torsoShadow"))  # hem shadow
        if direction != "up":
            d.rectangle([t_l + 1, t_top, t_l + 2, 41], fill=m("accent"))
            d.rectangle([t_r - 2, t_top, t_r - 1, 41], fill=m("accent"))
        if spec.get("sash"):
            d.rectangle([t_l - 1, 30, t_r + 1, 31], fill=m("accent2"))
        # center fold lines on the skirt
        d.line([(15, t_bot + 1), (14, 40)], fill=m("torsoShadow"))
        d.line([(17, t_bot + 1), (18, 40)], fill=m("torsoShadow"))
        # feet peeking
        d.rectangle([11 + sway, 42, 14 + sway, 43], fill=m("boots"))
        d.rectangle([17 + sway, 42, 20 + sway, 43], fill=m("boots"))
    elif garment == "overalls":
        d.rectangle([t_l, t_top, t_r, 29], fill=m("torso"))              # shirt
        d.rectangle([t_l, 30, t_r, t_bot], fill=m("pants"))              # overall body
        d.rectangle([11, t_top, 12, 29], fill=m("pants"))                # straps
        d.rectangle([19, t_top, 20, 29], fill=m("pants"))
        d.point([(11, 30), (20, 30)], fill=m("buckle"))                  # strap buttons
        d.rectangle([13, 32, 18, 34], fill=m("pantsShadow"))             # bib pocket
        d.rectangle([t_l, t_top, t_l, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r, t_top, t_r, t_bot], fill=m("torsoShadow"))
    elif garment == "armor":
        d.rectangle([t_l, t_top, t_r, t_bot], fill=m("metal"))
        d.rectangle([t_l, t_top, t_l + 1, t_bot], fill=m("metalShadow"))
        d.rectangle([t_r - 1, t_top, t_r, t_bot], fill=m("metalShadow"))
        d.line([(t_l + 2, 30), (t_r - 2, 30)], fill=m("metalShadow"))    # breastplate seam
        d.rectangle([13, 29, 18, 38], fill=m("accent"))                  # tabard
        d.rectangle([15, 29, 16, 38], fill=m("gold"))                    # tabard stripe
        d.rectangle([4, t_top, t_l - 1, t_top + 2], fill=m("metal"))     # pauldrons
        d.rectangle([t_r + 1, t_top, 27, t_top + 2], fill=m("metal"))
        d.rectangle([4, t_top + 2, t_l - 1, t_top + 2], fill=m("metalShadow"))
        d.rectangle([t_r + 1, t_top + 2, 27, t_top + 2], fill=m("metalShadow"))
    else:  # tunic
        d.rectangle([t_l, t_top, t_r, t_bot], fill=m("torso"))
        d.rectangle([t_l, t_top, t_l, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_r, t_top, t_r, t_bot], fill=m("torsoShadow"))
        d.rectangle([t_l, t_bot, t_r, t_bot], fill=m("torsoShadow"))     # hem
        d.rectangle([t_l + 1, t_top, t_r - 1, t_top], fill=m("accent2")) # collar
        if not child:
            d.line([(16, t_top + 2), (16, t_bot - 3)], fill=m("torsoShadow"))  # center fold
        if spec.get("strap") and direction == "down":
            for i in range(9):
                x = t_l + 1 + i * 1.4
                y = t_top + 1 + i
                d.rectangle([int(x), y, int(x) + 1, y], fill=m("accent"))
        if spec.get("strap") and direction == "up":
            for i in range(9):
                x = t_r - 1 - i * 1.4
                y = t_top + 1 + i
                d.rectangle([int(x) - 1, y, int(x), y], fill=m("accent"))

    # belt
    if garment in ("tunic", "armor") and not child:
        d.rectangle([t_l, 33, t_r, 34], fill=m("belt"))
        if direction == "down":
            d.rectangle([15, 33, 16, 34], fill=m("buckle"))

    # ---------------- arms ----------------
    sleeve = m("metal") if garment == "armor" else m("torso")
    sleeve_sh = m("metalShadow") if garment == "armor" else m("torsoShadow")
    if attack:
        blade = m("metal")
        if direction == "side":
            # thrust: arm extended forward, blade out in front
            d.rectangle([side_arm[1] - 3, a_slv[0] + 1, side_arm[1] + 1, a_slv[0] + 3], fill=sleeve)
            d.rectangle([side_arm[1] + 2, a_slv[0] + 1, side_arm[1] + 3, a_slv[0] + 3], fill=m("skin"))
            d.rectangle([side_arm[1] + 4, a_slv[0], side_arm[1] + 4, a_slv[0] + 4], fill=m("gold"))
            d.rectangle([side_arm[1] + 5, a_slv[0] + 1, 31, a_slv[0] + 2], fill=blade)
        elif direction == "down":
            d.rectangle([arm_l[0], a_slv[0], arm_l[1], a_slv[1]], fill=sleeve)
            d.rectangle([arm_l[0], a_hand[0], arm_l[1], a_hand[1]], fill=m("skin"))
            # sword arm swings low, blade pointing down beside the leg
            d.rectangle([arm_r[0], a_slv[0], arm_r[1], a_slv[0] + 2], fill=sleeve)
            d.rectangle([arm_r[0] + 1, a_slv[0] + 3, arm_r[1] + 1, a_slv[0] + 5], fill=m("skin"))
            d.rectangle([arm_r[0], a_slv[0] + 6, arm_r[1] + 2, a_slv[0] + 6], fill=m("gold"))
            d.rectangle([arm_r[0] + 2, a_slv[0] + 7, arm_r[0] + 3, 42], fill=blade)
        else:  # up: blade raised high beside the head
            d.rectangle([arm_l[0], a_slv[0], arm_l[1], a_slv[1]], fill=sleeve)
            d.rectangle([arm_l[0], a_hand[0], arm_l[1], a_hand[1]], fill=m("skin"))
            d.rectangle([arm_r[0], t_top - 1, arm_r[1] + 2, t_top + 1], fill=sleeve)
            d.rectangle([26, t_top - 4, 28, t_top - 2], fill=m("skin"))
            d.rectangle([25, t_top - 5, 29, t_top - 5], fill=m("gold"))
            d.rectangle([26, 4, 27, t_top - 6], fill=blade)
    elif direction == "side":
        d.rectangle([side_arm[0], a_slv[0] + arm_off, side_arm[1], a_slv[1] + arm_off], fill=sleeve)
        d.rectangle([side_arm[0], a_slv[0] + arm_off, side_arm[0], a_slv[1] + arm_off], fill=sleeve_sh)
        d.rectangle([side_arm[0], a_slv[1] + arm_off, side_arm[1], a_slv[1] + arm_off], fill=sleeve_sh)  # cuff
        d.rectangle([side_arm[0] + 1, a_hand[0] + arm_off, side_arm[1] - 1, a_hand[1] + arm_off], fill=m("skin"))
        if spec.get("staff"):
            d.rectangle([24, 8, 25, 41], fill=m("wood"))
            d.rectangle([24, 8, 24, 41], fill=m("bootsShadow"))
            d.ellipse([22, 3, 27, 8], fill=m("orb"))
    else:
        left_arm = not (spec.get("one_arm") and direction == "down")
        right_arm = not (spec.get("one_arm") and direction == "up")
        for present, (ax0, ax1), off in ((left_arm, arm_l, arm_off), (right_arm, arm_r, -arm_off)):
            if present:
                d.rectangle([ax0, a_slv[0] + off, ax1, a_slv[1] + off], fill=sleeve)
                d.rectangle([ax0, a_slv[1] + off, ax1, a_slv[1] + off], fill=sleeve_sh)  # cuff
                if spec.get("bracers"):
                    d.rectangle([ax0, a_slv[1] - 1 + off, ax1, a_slv[1] + off], fill=m("belt"))
                d.rectangle([ax0, a_hand[0] + off, ax1, a_hand[1] + off], fill=m("skin"))
            else:
                d.rectangle([ax0, a_slv[0], ax1, a_slv[0] + 3], fill=sleeve)
                d.rectangle([ax0, a_slv[0] + 3, ax1, a_slv[0] + 4], fill=sleeve_sh)  # pinned fold
        if spec.get("staff") and direction == "down":
            d.rectangle([26, 8, 27, 41], fill=m("wood"))
            d.ellipse([24, 3, 29, 8], fill=m("orb"))

    # ---------------- head ----------------
    hair = spec.get("hair", "short")
    headgear = spec.get("headgear")
    cap = hd["cap"]
    face = hd["face"]
    ey = hd["eye_y"]

    if direction == "down":
        d.ellipse(list(face), fill=m("skin"))
        # Pokemon-style line eyes: simple horizontal dashes
        for ex0, ex1 in hd["eyes"]:
            d.rectangle([ex0, ey, ex1, ey], fill=m("eye"))
        d.point([(hd["nose"][0], hd["nose"][1]), (hd["nose"][0] + 1, hd["nose"][1])], fill=m("skinShadow"))
        if spec.get("beard"):
            d.ellipse([face[0] + 2, ey + 3, face[2] - 2, face[3] + 4], fill=m("beard"))
            d.rectangle([hd["eyes"][0][0], ey + 3, hd["eyes"][1][1], ey + 4], fill=m("beard"))  # mustache
            d.line([(face[0] + 4, face[3] + 2), (face[0] + 5, face[3] + 3)], fill=m("beardShadow"))
        else:
            d.rectangle([hd["mouth"][0], hd["mouth"][1], hd["mouth"][0] + 1, hd["mouth"][1]], fill=m("mouth"))
            # blush/cheek shading
            d.point([(face[0] + 2, ey + 2), (face[2] - 2, ey + 2)], fill=m("skinShadow"))
    elif direction == "up":
        d.ellipse(list(face), fill=m("skinShadow"))
    else:  # side
        d.ellipse([face[0] + 3, face[1], face[2] + 2, face[3]], fill=m("skin"))
        ex = face[2] - 4
        d.rectangle([ex, ey, ex + 2, ey], fill=m("eye"))  # line eye
        d.point([(face[2] + 2, ey + 3)], fill=m("skinShadow"))  # nose bump
        if spec.get("beard"):
            d.rectangle([face[0] + 6, ey + 3, face[2] + 1, face[3] + 3], fill=m("beard"))
        else:
            d.point([(face[2] - 1, ey + 5)], fill=m("mouth"))

    def front_hair():
        if headgear == "helm":
            d.ellipse([cap[0], cap[1], cap[2], cap[3] - 2], fill=m("metal"))
            d.rectangle([cap[0], 15, cap[0] + 2, 23], fill=m("metal"))    # cheek guards
            d.rectangle([cap[2] - 2, 15, cap[2], 23], fill=m("metalShadow"))
            d.rectangle([15, 13, 16, 19], fill=m("metalShadow"))          # nose guard
            d.line([(cap[0] + 2, cap[1] + 3), (cap[0] + 2, cap[3] - 4)], fill=m("metalShadow"))
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] - 3, 12, cap[2] + 3, 17], fill=m("straw"))  # brim
            d.ellipse([cap[0] + 2, 5, cap[2] - 2, 14], fill=m("straw"))   # dome
            d.rectangle([cap[0] + 2, 12, cap[2] - 2, 13], fill=m("belt")) # band
            return
        # hair cap over the top half of the head
        d.ellipse([cap[0], cap[1], cap[2], cap[3]], fill=m("hair"))
        d.rectangle([cap[0], cap[3] - 5, cap[0] + 1, cap[3] + 1], fill=m("hair"))  # side tufts
        d.rectangle([cap[2] - 1, cap[3] - 5, cap[2], cap[3] + 1], fill=m("hair"))
        d.rectangle([cap[2] - 1, cap[3] - 3, cap[2], cap[3] + 1], fill=m("hairShadow"))
        # fringe: uneven teeth over the forehead
        fy = cap[3] - 2
        for fx0, fx1, fdrop in (
            (cap[0] + 2, cap[0] + 4, 2), (cap[0] + 5, cap[0] + 7, 1),
            (cap[0] + 8, cap[0] + 10, 3), (cap[0] + 11, cap[0] + 13, 1),
            (cap[0] + 14, cap[2] - 2, 2),
        ):
            fx1 = min(fx1, cap[2] - 2)
            if fx1 >= fx0:
                d.rectangle([fx0, fy, fx1, fy + fdrop], fill=m("hair"))
        if hair == "spiky":
            for sx in (cap[0] + 3, cap[0] + 8, cap[0] + 13):
                d.polygon([(sx, cap[1] + 2), (sx + 2, cap[1] - 2), (sx + 4, cap[1] + 2)], fill=m("hair"))
        if hair == "long":
            d.rectangle([cap[0] - 1, cap[3] - 6, cap[0], t_top + 4], fill=m("hair"))
            d.rectangle([cap[2], cap[3] - 6, cap[2] + 1, t_top + 4], fill=m("hair"))
        if hair == "bun":
            d.ellipse([cap[2] - 4, cap[1] - 2, cap[2] + 1, cap[1] + 3], fill=m("hair"))
            d.ellipse([cap[2] - 3, cap[1] - 1, cap[2], cap[1] + 2], fill=m("hairShadow"))
        if hair == "bald_fringe":
            # erase the cap: redraw scalp as skin, keep side tufts only
            d.ellipse([cap[0] + 1, cap[1] + 2, cap[2] - 1, cap[3]], fill=m("skin"))
            d.rectangle([cap[0], cap[3] - 5, cap[0] + 1, cap[3] + 2], fill=m("hair"))
            d.rectangle([cap[2] - 1, cap[3] - 5, cap[2], cap[3] + 2], fill=m("hair"))
        if headgear == "circlet":
            d.rectangle([cap[0] + 1, cap[3] - 4, cap[2] - 1, cap[3] - 3], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 1, cap[1] + 2, cap[2] - 1, cap[1] + 4], fill=m("gold"))
            for sx in (cap[0] + 3, 15, cap[2] - 4):
                d.rectangle([sx, cap[1], sx + 1, cap[1] + 2], fill=m("gold"))

    def back_hair():
        if headgear == "helm":
            d.ellipse([cap[0], cap[1], cap[2], cap[3] + 2], fill=m("metal"))
            d.rectangle([cap[0] + 2, cap[3] + 1, cap[2] - 2, cap[3] + 4], fill=m("metalShadow"))  # neck guard
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] - 3, 12, cap[2] + 3, 17], fill=m("straw"))
            d.ellipse([cap[0] + 2, 5, cap[2] - 2, 14], fill=m("straw"))
            return
        d.ellipse([cap[0], cap[1], cap[2], cap[3] + 4], fill=m("hair"))
        d.rectangle([cap[0] + 1, cap[3], cap[0] + 4, cap[3] + 3], fill=m("hairShadow"))
        if hair == "long":
            d.rectangle([cap[0], cap[3], cap[2], t_top + 5], fill=m("hair"))
            d.rectangle([cap[0], t_top + 4, cap[2], t_top + 5], fill=m("hairShadow"))
        if hair == "bun":
            d.ellipse([13, cap[1] - 2, 20, cap[1] + 5], fill=m("hair"))
            d.ellipse([14, cap[1] - 1, 19, cap[1] + 4], fill=m("hairShadow"))
        if hair == "bald_fringe":
            d.ellipse([cap[0] + 1, cap[1] + 2, cap[2] - 1, cap[3] + 2], fill=m("skin"))
            d.rectangle([cap[0], cap[3] - 4, cap[2], cap[3] + 3], fill=m("hair"))  # low band of hair
        if headgear == "circlet":
            d.rectangle([cap[0] + 1, cap[3] - 4, cap[2] - 1, cap[3] - 3], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 1, cap[1] + 2, cap[2] - 1, cap[1] + 4], fill=m("gold"))

    def side_hair():
        if headgear == "helm":
            d.ellipse([cap[0] + 1, cap[1], cap[2] + 1, cap[3] - 2], fill=m("metal"))
            d.rectangle([cap[2] - 4, 15, cap[2], 22], fill=m("metalShadow"))  # cheek guard
            return
        if headgear == "straw_hat":
            d.ellipse([cap[0] - 2, 12, cap[2] + 4, 17], fill=m("straw"))
            d.ellipse([cap[0] + 3, 5, cap[2] - 1, 14], fill=m("straw"))
            return
        d.ellipse([cap[0] + 1, cap[1], cap[2] + 1, cap[3] - 1], fill=m("hair"))
        d.rectangle([cap[0] + 1, cap[3] - 6, cap[0] + 5, cap[3] + 5], fill=m("hair"))  # back mass
        d.rectangle([cap[0] + 1, cap[3] - 2, cap[0] + 2, cap[3] + 4], fill=m("hairShadow"))
        if hair == "spiky":
            d.polygon([(cap[0] + 3, cap[1] + 2), (cap[0], cap[1] - 1), (cap[0] + 5, cap[1] + 1)], fill=m("hair"))
        if hair == "long":
            d.rectangle([cap[0] + 1, cap[3], cap[0] + 4, t_top + 4], fill=m("hair"))
        if hair == "bun":
            d.ellipse([cap[0] - 1, cap[1] + 3, cap[0] + 4, cap[1] + 9], fill=m("hair"))
            d.ellipse([cap[0], cap[1] + 4, cap[0] + 3, cap[1] + 8], fill=m("hairShadow"))
        if hair == "bald_fringe":
            d.ellipse([cap[0] + 2, cap[1] + 2, cap[2], cap[3] - 1], fill=m("skin"))
            d.rectangle([cap[0] + 1, cap[3] - 5, cap[0] + 4, cap[3] + 3], fill=m("hair"))
        if headgear == "circlet":
            d.rectangle([cap[0] + 2, cap[3] - 4, cap[2], cap[3] - 3], fill=m("gold"))
        if headgear == "crown":
            d.rectangle([cap[0] + 2, cap[1] + 2, cap[2], cap[1] + 4], fill=m("gold"))

    if direction == "down":
        front_hair()
    elif direction == "up":
        back_hair()
    else:
        side_hair()

    # ---------------- sword on the back (in hand during attacks) ----------------
    if spec.get("sword") and not attack:
        if direction == "up":
            d.line([(20, t_top + 2), (12, t_bot + 4)], fill=m("bootsShadow"), width=2)
            d.rectangle([20, t_top - 3, 21, t_top + 1], fill=m("wood"))
            d.rectangle([19, t_top + 1, 22, t_top + 1], fill=m("gold"))
        elif direction == "down":
            d.rectangle([24, t_top - 4, 25, t_top - 1], fill=m("wood"))
            d.rectangle([23, t_top - 1, 26, t_top - 1], fill=m("gold"))

    return img


# ---------------------------------------------------------------------------
# Character specs
# ---------------------------------------------------------------------------
CHARACTERS = {
    "player": dict(
        spec=dict(hair="short", strap=True, sword=True, fighter=True),
        bases=dict(hair="#4a3524", skin="#f0c9a2", torso="#4f6d80", accent="#6d4a30",
                   accent2="#65899c", belt="#8a6d42", pants="#33384c", boots="#5d4630",
                   wood="#7a5a38", gold="#d8b04a", metal="#b8bcc4", eye="#26303a"),
    ),
    "joran": dict(
        spec=dict(hair="spiky", strap=True, bracers=True, fighter=True),
        bases=dict(hair="#8a6b40", skin="#e0b088", torso="#5d6653", accent="#54402b",
                   accent2="#6f7a63", belt="#6d5638", pants="#3d3c38", boots="#4a3826",
                   gold="#d8b04a", wood="#7a5a38", metal="#b8bcc4", eye="#2e2a22"),
    ),
    "king": dict(
        spec=dict(hair="short", beard=True, headgear="circlet", garment="robe", sash=True),
        bases=dict(hair="#b8b2a8", skin="#dcb28c", torso="#7c2830", accent="#c9a44a",
                   accent2="#dcb054", beard="#c6c0b6", belt="#8a6d42", pants="#463824",
                   boots="#2e2620", gold="#e0bc54", eye="#2e2a26"),
    ),
    "marrow": dict(
        spec=dict(hair="bald_fringe", beard=True, garment="robe", staff=True),
        bases=dict(hair="#cac4bc", skin="#c8a684", torso="#4e3c6a", accent="#8d7a3a",
                   accent2="#6a5690", beard="#d4cec6", belt="#8a6d42", pants="#3a3050",
                   boots="#2a2422", wood="#6d5334", orb="#5ac8b4", gold="#d8b04a",
                   eye="#2a2632"),
    ),
    "villager_f": dict(  # Sela Vane -- one-armed, bun, long dress
        spec=dict(hair="bun", garment="dress", one_arm=True),
        bases=dict(hair="#6d5335", skin="#e2ba92", torso="#7a5a48", accent="#a89070",
                   accent2="#8d6d58", belt="#54402b", pants="#5d4838", boots="#463424",
                   eye="#322a22"),
    ),
    "villager_m": dict(  # Tobin / Garrick -- farmer
        spec=dict(hair="short", headgear="straw_hat", garment="overalls"),
        bases=dict(hair="#3d2e1e", skin="#d8a878", torso="#a08858", accent="#54402b",
                   accent2="#b09868", belt="#6d5638", pants="#4e5c74", boots="#4a3826",
                   straw="#cbb26a", eye="#2a241c"),
    ),
    "child": dict(  # Wren / Pell
        spec=dict(hair="spiky", child=True),
        bases=dict(hair="#b08c3c", skin="#f0c9a4", torso="#8c8a52", accent="#6d5a30",
                   accent2="#9c9a62", belt="#6d5638", pants="#5d5240", boots="#54402b",
                   eye="#32301e"),
    ),
    "soldier": dict(
        spec=dict(headgear="helm", garment="armor"),
        bases=dict(hair="#242220", skin="#d8a878", torso="#3d4148", accent="#5d2c2c",
                   accent2="#6d3434", metal="#8a8e96", belt="#3a3430", pants="#3a3e46",
                   boots="#26221e", gold="#c9a44a", eye="#26241e"),
    ),
}


# ---------------------------------------------------------------------------
# Dragons -- 32x44, two distinct species, three frames each.
# ---------------------------------------------------------------------------
def build_wyrmling(frame):
    """Round-bodied juvenile: big head, big eye, small folded wing. Faces right."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 2 if frame == "attack" else 0
    hx = lunge

    # tail curl on the left
    d.line([(6, 37), (1, 32 - bob)], fill=m("body"), width=3)
    d.polygon([(0, 33 - bob), (0, 29 - bob), (4, 31 - bob)], fill=m("horn"))
    # small folded wing on the back
    d.polygon([(6, 27 - bob), (3, 18 - bob), (13, 26 - bob)], fill=m("wing"))
    # round body, smaller than the head
    d.ellipse([5, 26 - bob, 23, 42], fill=m("body"))
    d.ellipse([9, 31 - bob, 20, 41], fill=m("belly"))
    d.line([(11, 37), (18, 37)], fill=m("bellyShadow"))
    # stubby feet
    d.rectangle([8, 41, 12, 43], fill=m("bodyShadow"))
    d.rectangle([16 + lunge, 41, 20 + lunge, 43], fill=m("bodyShadow"))
    # big head (chibi), nudges forward on the lunge
    d.ellipse([8 + hx, 6 - bob, 29 + hx, 27 - bob], fill=m("body"))
    d.ellipse([22 + hx, 16 - bob, 30 + hx, 23 - bob], fill=m("body"))  # snout
    d.point([(28 + hx, 18 - bob)], fill=m("bodyShadow"))  # nostril
    if frame == "attack":
        d.polygon([(22 + hx, 21 - bob), (29 + hx, 20 - bob), (25 + hx, 26 - bob)], fill=m("maw"))
        d.point([(23 + hx, 21 - bob), (28 + hx, 20 - bob)], fill=m("horn"))  # fangs
    else:
        d.line([(23 + hx, 21 - bob), (29 + hx, 20 - bob)], fill=m("bodyShadow"))
    # big cute eye: colored iris, dark pupil, light glint
    d.ellipse([13 + hx, 12 - bob, 18 + hx, 18 - bob], fill=m("eye"))
    d.rectangle([16 + hx, 14 - bob, 17 + hx, 16 - bob], fill=m("outline"))
    d.point([(14 + hx, 13 - bob)], fill=m("horn"))
    # two small horns
    d.polygon([(11 + hx, 8 - bob), (12 + hx, 3 - bob), (15 + hx, 7 - bob)], fill=m("horn"))
    d.polygon([(19 + hx, 6 - bob), (21 + hx, 2 - bob), (23 + hx, 7 - bob)], fill=m("horn"))
    return img


def build_skitterdrake(frame):
    """Low, long scavenger with a rounded back frill. Faces right."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 1 if frame == "idle2" else 0
    lunge = 1 if frame == "attack" else 0
    hx = lunge

    # tail
    d.line([(4, 33 - bob), (0, 27 - bob)], fill=m("body"), width=2)
    # rounded back frill bumps
    for fx in (5, 10, 15):
        d.ellipse([fx, 23 - bob, fx + 4, 28 - bob], fill=m("horn"))
    # long low body
    d.ellipse([2, 26 - bob, 22, 41], fill=m("body"))
    d.ellipse([6, 31 - bob, 19, 40], fill=m("belly"))
    d.line([(8, 36), (17, 36)], fill=m("bellyShadow"))
    # four stubby legs
    d.rectangle([5, 40, 8, 43], fill=m("bodyShadow"))
    d.rectangle([11, 40, 14, 43], fill=m("bodyShadow"))
    d.rectangle([17 + lunge, 40, 20 + lunge, 43], fill=m("body"))
    d.rectangle([23 + lunge, 40, 26 + lunge, 43], fill=m("body"))
    # head with a long rounded snout, held low
    d.ellipse([15 + hx, 13 - bob, 29 + hx, 28 - bob], fill=m("body"))
    d.rectangle([24 + hx, 19 - bob, 30 + hx, 24 - bob], fill=m("body"))
    d.point([(29 + hx, 20 - bob)], fill=m("bodyShadow"))  # nostril
    if frame == "attack":
        d.polygon([(23 + hx, 23 - bob), (30 + hx, 21 - bob), (26 + hx, 27 - bob)], fill=m("maw"))
        d.point([(24 + hx, 23 - bob), (28 + hx, 22 - bob)], fill=m("horn"))
    else:
        d.line([(24 + hx, 23 - bob), (29 + hx, 22 - bob)], fill=m("bodyShadow"))
    # big eye
    d.ellipse([19 + hx, 17 - bob, 23 + hx, 22 - bob], fill=m("eye"))
    d.rectangle([21 + hx, 19 - bob, 22 + hx, 20 - bob], fill=m("outline"))
    d.point([(20 + hx, 18 - bob)], fill=m("horn"))
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
                img = add_outline(build_humanoid(cfg["spec"], direction, 0, attack=True))
                shapes[direction]["attack"] = to_grid(img)
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
    out.append("// Chibi proportions at 32x44; every character has its own shape set.")
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
