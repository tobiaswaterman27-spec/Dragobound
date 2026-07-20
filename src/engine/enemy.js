import { MovableEntity } from "./entity.js";
import { CreatureSprite, FRAME_W, FRAME_H } from "./sprite.js";
import { TILE_SIZE } from "./tilemap.js";

export class Enemy extends MovableEntity {
  constructor(def) {
    super(def.x, def.y, "down");
    this.id = def.id;
    this.kind = def.kind;
    this.name = def.name || "Wyrmling";
    this.sprite = new CreatureSprite(`assets/sprites/${def.kind}.png`);
    this.maxHp = def.hp || 12;
    this.hp = this.maxHp;
    this.damage = def.damage || 2;
    this.aggroRange = def.aggroRange ?? 3.5;
    this.homeX = def.x;
    this.homeY = def.y;
    this.leashRange = def.leashRange ?? 6;
    this.decisionT = Math.random() * 0.5;
    this.attackCd = 0;
    this.attackFlashT = 0;
    this.dead = false;
    this.facingLeft = false;
    this.deathT = 0;
  }

  takeDamage(amount) {
    if (this.dead) return;
    this.hp = Math.max(0, this.hp - amount);
    this.attackFlashT = 0.15;
    if (this.hp <= 0) {
      this.dead = true;
      this.deathT = 0;
    }
  }

  update(dt, map, player, onContactPlayer) {
    if (this.dead) {
      this.deathT += dt;
      return;
    }
    super.update(dt);
    if (this.attackCd > 0) this.attackCd -= dt;
    if (this.attackFlashT > 0) this.attackFlashT -= dt;

    const dist = Math.hypot(this.gridX - player.gridX, this.gridY - player.gridY);
    const state = this.attackCd > 0.5 ? "attack" : "idle";
    this.sprite.update(dt, state, this.facingLeft);

    if (!this.moving) {
      this.decisionT -= dt;
      if (this.decisionT <= 0) {
        this.decisionT = 0.35 + Math.random() * 0.25;
        if (dist <= this.aggroRange && dist > 1.05) {
          const homeDist = Math.hypot(this.gridX - this.homeX, this.gridY - this.homeY);
          if (homeDist < this.leashRange) this._stepToward(player, map);
        } else if (dist <= 1.05) {
          if (this.attackCd <= 0) {
            this.attackCd = 1.1;
            onContactPlayer && onContactPlayer(this);
          }
        } else if (Math.random() < 0.3) {
          this._wander(map);
        }
      }
    }
  }

  _stepToward(player, map) {
    const dx = player.gridX - this.gridX;
    const dy = player.gridY - this.gridY;
    const options = [];
    if (Math.abs(dx) >= Math.abs(dy)) {
      options.push([Math.sign(dx), 0], [0, Math.sign(dy)]);
    } else {
      options.push([0, Math.sign(dy)], [Math.sign(dx), 0]);
    }
    for (const [ddx, ddy] of options) {
      if (ddx === 0 && ddy === 0) continue;
      if (ddx !== 0) this.facingLeft = ddx < 0;
      const moved = this.startMove(ddx, ddy, (nx, ny) =>
        map.canWalk(nx, ny) && !(nx === player.gridX && ny === player.gridY)
      );
      if (moved) return;
    }
  }

  _wander(map) {
    const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    const [ddx, ddy] = dirs[Math.floor(Math.random() * dirs.length)];
    if (ddx !== 0) this.facingLeft = ddx < 0;
    this.startMove(ddx, ddy, (nx, ny) => {
      if (!map.canWalk(nx, ny)) return false;
      return Math.hypot(nx - this.homeX, ny - this.homeY) < this.leashRange;
    });
  }

  draw(ctx, camera) {
    if (this.dead && this.deathT > 0.5) return;
    const w = TILE_SIZE * 1.1;
    const h = FRAME_H * (w / FRAME_W);
    const sx = this.pixelX - camera.x + TILE_SIZE / 2 - w / 2;
    let sy = this.pixelY - camera.y + TILE_SIZE - h + 14;

    ctx.save();
    if (this.dead) {
      ctx.globalAlpha = Math.max(0, 1 - this.deathT / 0.5);
      sy += this.deathT * 30;
    } else if (this.attackFlashT > 0) {
      ctx.globalAlpha = 0.5;
      ctx.filter = "brightness(2) saturate(0)";
    }
    this.sprite.draw(ctx, sx, sy, w, h);
    ctx.restore();

    if (!this.dead) {
      const barW = TILE_SIZE * 0.8;
      const barX = this.pixelX - camera.x + TILE_SIZE / 2 - barW / 2;
      const barY = sy - 10;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(barX, barY, barW, 6);
      ctx.fillStyle = "#5fd35f";
      ctx.fillRect(barX, barY, barW * (this.hp / this.maxHp), 6);
    }
  }
}
