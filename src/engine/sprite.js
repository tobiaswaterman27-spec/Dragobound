export const FRAME_W = 64;
export const FRAME_H = 96;

const cache = new Map();

export function loadImage(src) {
  if (cache.has(src)) return cache.get(src);
  const img = new Image();
  img.src = src;
  const promise = new Promise((resolve) => {
    img.onload = () => resolve(img);
    img.onerror = () => resolve(img);
  });
  cache.set(src, img);
  cache.set(src + ":promise", promise);
  return img;
}

export function preload(srcs) {
  return Promise.all(srcs.map((s) => loadImage(s), cache.get(s + ":promise")));
}

const ROW_FOR_DIR = { down: 0, up: 1, left: 2, right: 2 };

/** Humanoid-style 3x3 (dir x step) animated sprite. */
export class ActorSprite {
  constructor(sheetSrc) {
    this.img = loadImage(sheetSrc);
    this.dir = "down";
    this.moving = false;
    this.animTime = 0;
  }

  update(dt, dir, moving) {
    this.dir = dir;
    this.moving = moving;
    if (moving) this.animTime += dt;
    else this.animTime = 0;
  }

  _frameCol() {
    if (!this.moving) return 0;
    const cycle = Math.floor(this.animTime / 0.14) % 4;
    return cycle === 0 ? 0 : cycle === 1 ? 1 : cycle === 2 ? 0 : 2;
  }

  draw(ctx, screenX, screenY, w = FRAME_W, h = FRAME_H) {
    const row = ROW_FOR_DIR[this.dir] ?? 0;
    const col = this._frameCol();
    const flip = this.dir === "left";
    ctx.save();
    if (flip) {
      ctx.translate(screenX + w, screenY);
      ctx.scale(-1, 1);
      ctx.drawImage(this.img, col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H, 0, 0, w, h);
    } else {
      ctx.drawImage(this.img, col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H, screenX, screenY, w, h);
    }
    ctx.restore();
  }

  /** Single static idle-down frame, for portraits/menus. */
  static drawPortrait(ctx, sheetSrc, x, y, w, h) {
    const img = loadImage(sheetSrc);
    ctx.drawImage(img, 0, 0, FRAME_W, FRAME_H, x, y, w, h);
  }
}

/** Small creature sheet: 1 row x 3 cols (idle1, idle2, attack). */
export class CreatureSprite {
  constructor(sheetSrc) {
    this.img = loadImage(sheetSrc);
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
    let col = 0;
    if (this.state === "idle") {
      col = Math.floor(this.animTime / 0.4) % 2;
    } else if (this.state === "attack") {
      col = 2;
    }
    ctx.save();
    if (this.facingLeft) {
      ctx.translate(screenX + w, screenY);
      ctx.scale(-1, 1);
      ctx.drawImage(this.img, col * FRAME_W, 0, FRAME_W, FRAME_H, 0, 0, w, h);
    } else {
      ctx.drawImage(this.img, col * FRAME_W, 0, FRAME_W, FRAME_H, screenX, screenY, w, h);
    }
    ctx.restore();
  }
}
