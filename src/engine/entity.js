import { TILE_SIZE } from "./tilemap.js";

const MOVE_DURATION = 0.22; // seconds per tile

export class MovableEntity {
  constructor(gridX, gridY, facing = "down") {
    this.gridX = gridX;
    this.gridY = gridY;
    this.facing = facing;
    this.moving = false;
    this.moveT = 0;
    this.moveDuration = MOVE_DURATION;
    this.fromX = gridX * TILE_SIZE;
    this.fromY = gridY * TILE_SIZE;
    this.toX = this.fromX;
    this.toY = this.fromY;
    this.pixelX = this.fromX;
    this.pixelY = this.fromY;
  }

  get facingDelta() {
    switch (this.facing) {
      case "up": return { dx: 0, dy: -1 };
      case "down": return { dx: 0, dy: 1 };
      case "left": return { dx: -1, dy: 0 };
      case "right": return { dx: 1, dy: 0 };
      default: return { dx: 0, dy: 1 };
    }
  }

  get frontTile() {
    const { dx, dy } = this.facingDelta;
    return { x: this.gridX + dx, y: this.gridY + dy };
  }

  /** Returns true if a move was started. */
  startMove(dx, dy, canEnter) {
    if (this.moving) return false;
    if (dx !== 0) this.facing = dx > 0 ? "right" : "left";
    else if (dy !== 0) this.facing = dy > 0 ? "down" : "up";
    if (dx === 0 && dy === 0) return false;
    const nx = this.gridX + dx;
    const ny = this.gridY + dy;
    if (!canEnter(nx, ny)) return false;
    this.moving = true;
    this.moveT = 0;
    this.moveDuration = MOVE_DURATION;
    this.fromX = this.gridX * TILE_SIZE;
    this.fromY = this.gridY * TILE_SIZE;
    this.gridX = nx;
    this.gridY = ny;
    this.toX = nx * TILE_SIZE;
    this.toY = ny * TILE_SIZE;
    return true;
  }

  /** A longer, faster step in one direction -- stops at the first blocked tile. */
  startDash(dx, dy, canEnter, maxDist, duration) {
    if (this.moving) return false;
    if (dx !== 0) this.facing = dx > 0 ? "right" : "left";
    else if (dy !== 0) this.facing = dy > 0 ? "down" : "up";
    if (dx === 0 && dy === 0) return false;
    let nx = this.gridX;
    let ny = this.gridY;
    let dist = 0;
    for (let i = 1; i <= maxDist; i++) {
      const tx = this.gridX + dx * i;
      const ty = this.gridY + dy * i;
      if (!canEnter(tx, ty)) break;
      nx = tx;
      ny = ty;
      dist = i;
    }
    if (dist === 0) return false;
    this.moving = true;
    this.moveT = 0;
    this.moveDuration = duration;
    this.fromX = this.gridX * TILE_SIZE;
    this.fromY = this.gridY * TILE_SIZE;
    this.gridX = nx;
    this.gridY = ny;
    this.toX = nx * TILE_SIZE;
    this.toY = ny * TILE_SIZE;
    return true;
  }

  update(dt) {
    if (!this.moving) return;
    this.moveT += dt;
    const t = Math.min(1, this.moveT / this.moveDuration);
    this.pixelX = this.fromX + (this.toX - this.fromX) * t;
    this.pixelY = this.fromY + (this.toY - this.fromY) * t;
    if (t >= 1) {
      this.moving = false;
      this.pixelX = this.toX;
      this.pixelY = this.toY;
    }
  }
}

export { MOVE_DURATION };
