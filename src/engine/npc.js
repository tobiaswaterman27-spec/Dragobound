import { MovableEntity } from "./entity.js";
import { ActorSprite, FRAME_W, FRAME_H } from "./sprite.js";
import { TILE_SIZE } from "./tilemap.js";

export class Npc extends MovableEntity {
  constructor(def) {
    super(def.x, def.y, def.facing || "down");
    this.id = def.id;
    this.name = def.name;
    this.sheet = def.sheet;
    this.sprite = new ActorSprite(`assets/sprites/${def.sheet}.png`);
    this.dialogueId = def.dialogueId;
    this.homeX = def.x;
    this.homeY = def.y;
    this.wanderRange = def.wanderRange ?? 0;
    this.decisionT = 1 + Math.random();
    this.stationary = def.stationary ?? this.wanderRange === 0;
  }

  update(dt, map, isBlockedByOther) {
    super.update(dt);
    if (!this.stationary && !this.moving) {
      this.decisionT -= dt;
      if (this.decisionT <= 0) {
        this.decisionT = 1.5 + Math.random() * 2;
        if (Math.random() < 0.4) {
          const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
          const [dx, dy] = dirs[Math.floor(Math.random() * dirs.length)];
          this.startMove(dx, dy, (nx, ny) => {
            if (!map.canWalk(nx, ny)) return false;
            if (isBlockedByOther && isBlockedByOther(nx, ny)) return false;
            return Math.hypot(nx - this.homeX, ny - this.homeY) <= this.wanderRange;
          });
        } else {
          const facings = ["up", "down", "left", "right"];
          this.facing = facings[Math.floor(Math.random() * facings.length)];
        }
      }
    }
    this.sprite.update(dt, this.facing, this.moving);
  }

  draw(ctx, camera) {
    const w = TILE_SIZE * 1.3;
    const h = FRAME_H * (w / FRAME_W);
    const sx = this.pixelX - camera.x + TILE_SIZE / 2 - w / 2;
    const sy = this.pixelY - camera.y + TILE_SIZE - h + 6;
    this.sprite.draw(ctx, sx, sy, w, h);
  }
}
