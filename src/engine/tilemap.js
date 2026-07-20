import { TILES } from "../data/sprites.js";

export const TILE_SIZE = 64;

const LEGEND = {
  ".": { tile: "grass", solid: false },
  p: { tile: "dirt", solid: false },
  S: { tile: "stone", solid: false },
  "~": { tile: "water", solid: true },
  b: { tile: "bush", solid: true },
  r: { tile: "rubble", solid: true },
  "#": { tile: "wall", solid: true },
  W: { tile: "house_wall", solid: true },
  R: { tile: "house_roof", solid: true },
  D: { tile: "door", solid: false },
  w: { tile: "wood_floor", solid: false },
  T: { tile: "table", solid: true },
  B: { tile: "bed", solid: true },
  C: { tile: "chest", solid: true },
  K: { tile: "diary", solid: true },
};

// Tiles are baked once from the pixel-matrix data in src/data/sprites.js
// into small offscreen canvases -- no external image files.
const tileCanvasCache = {};
export function tileImage(name) {
  if (tileCanvasCache[name]) return tileCanvasCache[name];
  const def = TILES[name];
  const h = def.rows.length;
  const w = def.rows[0].length;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const cctx = canvas.getContext("2d");
  const imageData = cctx.createImageData(w, h);
  const data = imageData.data;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const key = def.rows[y][x];
      const i = (y * w + x) * 4;
      if (key === ".") continue;
      const hex = def.palette[key];
      data[i] = parseInt(hex.slice(1, 3), 16);
      data[i + 1] = parseInt(hex.slice(3, 5), 16);
      data[i + 2] = parseInt(hex.slice(5, 7), 16);
      data[i + 3] = 255;
    }
  }
  cctx.putImageData(imageData, 0, 0);
  tileCanvasCache[name] = canvas;
  return canvas;
}

export class TileMap {
  constructor(def) {
    this.id = def.id;
    this.rows = def.rows;
    this.height = def.rows.length;
    this.width = def.rows[0].length;
    this.doors = def.doors || [];
    this.interactables = def.interactables || [];
    this.npcs = def.npcs || [];
    this.enemies = def.enemies || [];
    this.name = def.name || "";
    this.ambient = def.ambient || null;
  }

  charAt(x, y) {
    if (x < 0 || y < 0 || y >= this.height || x >= this.width) return "#";
    return this.rows[y][x];
  }

  legendAt(x, y) {
    return LEGEND[this.charAt(x, y)] || LEGEND["#"];
  }

  isSolid(x, y) {
    return this.legendAt(x, y).solid;
  }

  doorAt(x, y) {
    return this.doors.find((d) => d.x === x && d.y === y);
  }

  interactableAt(x, y) {
    return this.interactables.find((i) => i.x === x && i.y === y);
  }

  npcAt(x, y) {
    return this.npcs.find((n) => n.entity && n.entity.gridX === x && n.entity.gridY === y);
  }

  render(ctx, camera, viewW, viewH) {
    const startCol = Math.max(0, Math.floor(camera.x / TILE_SIZE) - 1);
    const endCol = Math.min(this.width, Math.ceil((camera.x + viewW) / TILE_SIZE) + 1);
    const startRow = Math.max(0, Math.floor(camera.y / TILE_SIZE) - 1);
    const endRow = Math.min(this.height, Math.ceil((camera.y + viewH) / TILE_SIZE) + 1);

    for (let y = startRow; y < endRow; y++) {
      for (let x = startCol; x < endCol; x++) {
        const legend = this.legendAt(x, y);
        const img = tileImage(legend.tile);
        const sx = Math.round(x * TILE_SIZE - camera.x);
        const sy = Math.round(y * TILE_SIZE - camera.y);
        ctx.drawImage(img, 0, 0, img.width, img.height, sx, sy, TILE_SIZE, TILE_SIZE);
      }
    }
  }
}
