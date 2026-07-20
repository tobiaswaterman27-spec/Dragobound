// Renders the hand-authored pixel-matrix data in src/data/sprites.js. No
// external image files: each shape (a grid of role-key characters) is baked
// once into a small offscreen canvas per character/frame, then blitted with
// image smoothing off so the pixels stay sharp and blocky at any scale.
// Every character has its own authored shape set + palette (see
// tools/gen_pixel_art.py), not a palette swap of one shared body.
import { CHARACTERS, DRAGONS } from "../data/sprites.js";

export const FRAME_W = 32;
export const FRAME_H = 44;

function buildCanvas(rows, palette) {
  const h = rows.length;
  const w = rows[0].length;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const cctx = canvas.getContext("2d");
  const imageData = cctx.createImageData(w, h);
  const data = imageData.data;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const key = rows[y][x];
      const i = (y * w + x) * 4;
      if (key === ".") continue;
      const hex = palette[key];
      if (!hex) continue;
      data[i] = parseInt(hex.slice(1, 3), 16);
      data[i + 1] = parseInt(hex.slice(3, 5), 16);
      data[i + 2] = parseInt(hex.slice(5, 7), 16);
      data[i + 3] = 255;
    }
  }
  cctx.putImageData(imageData, 0, 0);
  return canvas;
}

const humanoidCache = new Map();
function humanoidCanvases(characterName) {
  if (humanoidCache.has(characterName)) return humanoidCache.get(characterName);
  const data = CHARACTERS[characterName] || CHARACTERS.villager_m;
  const built = {};
  for (const dir of ["down", "up", "side"]) {
    built[dir] = {};
    for (const frame of Object.keys(data.shapes[dir])) {
      built[dir][frame] = buildCanvas(data.shapes[dir][frame], data.palette);
    }
  }
  humanoidCache.set(characterName, built);
  return built;
}

const dragonCache = new Map();
function dragonCanvases(kind) {
  if (dragonCache.has(kind)) return dragonCache.get(kind);
  const data = DRAGONS[kind] || DRAGONS.wyrmling;
  const built = {};
  for (const frame of ["idle1", "idle2", "attack"]) {
    built[frame] = buildCanvas(data.shapes[frame], data.palette);
  }
  dragonCache.set(kind, built);
  return built;
}

const ROW_FOR_DIR = { down: "down", up: "up", left: "side", right: "side" };

/** Humanoid actor: 3 directions x 3 walk frames, all pixel-matrix data. */
export class ActorSprite {
  constructor(paletteName) {
    this.canvases = humanoidCanvases(paletteName);
    this.dir = "down";
    this.moving = false;
    this.attacking = false;
    this.animTime = 0;
  }

  update(dt, dir, moving, attacking = false) {
    this.dir = dir;
    this.moving = moving;
    this.attacking = attacking;
    if (moving) this.animTime += dt;
    else this.animTime = 0;
  }

  _frame() {
    if (this.attacking) return "attack";
    if (!this.moving) return "idle";
    const cycle = Math.floor(this.animTime / 0.14) % 4;
    return cycle === 0 ? "idle" : cycle === 1 ? "step1" : cycle === 2 ? "idle" : "step2";
  }

  draw(ctx, screenX, screenY, w = FRAME_W, h = FRAME_H) {
    const dirKey = ROW_FOR_DIR[this.dir] ?? "down";
    const frames = this.canvases[dirKey];
    const canvas = frames[this._frame()] || frames.idle;
    const flip = this.dir === "left";
    ctx.save();
    if (flip) {
      ctx.translate(screenX + w, screenY);
      ctx.scale(-1, 1);
      ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, w, h);
    } else {
      ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, screenX, screenY, w, h);
    }
    ctx.restore();
  }

  /** Single static idle-down frame, for portraits/menus. */
  static drawPortrait(ctx, paletteName, x, y, w, h) {
    const canvas = humanoidCanvases(paletteName).down.idle;
    ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, x, y, w, h);
  }
}

/** Small creature: idle1/idle2 (bob) + attack (lunge), all pixel-matrix data. */
export class CreatureSprite {
  constructor(paletteName) {
    this.canvases = dragonCanvases(paletteName);
    this.state = "idle";
    this.animTime = 0;
    this.facingLeft = false;
  }

  update(dt, state, facingLeft) {
    if (this.state !== state) this.animTime = 0;
    this.state = state;
    this.facingLeft = facingLeft;
    this.animTime += dt;
  }

  draw(ctx, screenX, screenY, w = FRAME_W, h = FRAME_H) {
    let frame = "idle1";
    if (this.state === "idle") {
      frame = Math.floor(this.animTime / 0.4) % 2 === 0 ? "idle1" : "idle2";
    } else if (this.state === "attack") {
      frame = "attack";
    }
    const canvas = this.canvases[frame];
    ctx.save();
    if (this.facingLeft) {
      ctx.translate(screenX + w, screenY);
      ctx.scale(-1, 1);
      ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, w, h);
    } else {
      ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, screenX, screenY, w, h);
    }
    ctx.restore();
  }
}
