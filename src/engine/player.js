import { MovableEntity } from "./entity.js";
import { ActorSprite, FRAME_W, FRAME_H } from "./sprite.js";
import { TILE_SIZE } from "./tilemap.js";
import { input } from "./input.js";

const ATTACK_DURATION = 0.28;
const ATTACK_COOLDOWN = 0.12;
const HURT_INVULN = 0.7;

export class Player extends MovableEntity {
  constructor(gridX, gridY, sheetSrc, hp, maxHp) {
    super(gridX, gridY, "down");
    this.sprite = new ActorSprite(sheetSrc);
    this.hp = hp;
    this.maxHp = maxHp;
    this.attackT = -1;
    this.attackCooldown = 0;
    this.hurtT = 0;
    this.dead = false;
    this.controlsEnabled = true;
  }

  get attacking() {
    return this.attackT >= 0 && this.attackT < ATTACK_DURATION;
  }

  get invulnerable() {
    return this.hurtT > 0;
  }

  takeDamage(amount) {
    if (this.invulnerable || this.dead) return;
    this.hp = Math.max(0, this.hp - amount);
    this.hurtT = HURT_INVULN;
    if (this.hp <= 0) this.dead = true;
  }

  heal(amount) {
    this.hp = Math.min(this.maxHp, this.hp + amount);
  }

  update(dt, map, onAttack) {
    const wasMoving = this.moving;
    super.update(dt);
    if (this.hurtT > 0) this.hurtT = Math.max(0, this.hurtT - dt);
    if (this.attackCooldown > 0) this.attackCooldown -= dt;
    if (this.attackT >= 0) {
      this.attackT += dt;
      if (this.attackT > ATTACK_DURATION * 0.4 && this.attackT - dt <= ATTACK_DURATION * 0.4) {
        onAttack && onAttack(this.frontTile);
      }
      if (this.attackT >= ATTACK_DURATION) this.attackT = -1;
    }

    if (!this.controlsEnabled) {
      this.sprite.update(dt, this.facing, false);
      return;
    }

    if (input.wasPressed("attack") && this.attackCooldown <= 0 && !this.moving) {
      this.attackT = 0;
      this.attackCooldown = ATTACK_DURATION + ATTACK_COOLDOWN;
    }

    if (!wasMoving && !this.moving && !this.attacking) {
      let dx = 0, dy = 0;
      if (input.isDown("up")) dy = -1;
      else if (input.isDown("down")) dy = 1;
      else if (input.isDown("left")) dx = -1;
      else if (input.isDown("right")) dx = 1;
      if (dx !== 0 || dy !== 0) {
        const moved = this.startMove(dx, dy, (nx, ny) => map.canWalk(nx, ny));
        if (!moved) {
          if (dx !== 0) this.facing = dx > 0 ? "right" : "left";
          else this.facing = dy > 0 ? "down" : "up";
        }
      }
    }

    this.sprite.update(dt, this.facing, this.moving);
  }

  draw(ctx, camera) {
    const w = TILE_SIZE * 1.05;
    const h = FRAME_H * (w / FRAME_W);
    const sx = this.pixelX - camera.x + TILE_SIZE / 2 - w / 2;
    const sy = this.pixelY - camera.y + TILE_SIZE - h + 6;
    if (this.invulnerable && Math.floor(this.hurtT * 20) % 2 === 0) {
      ctx.globalAlpha = 0.4;
    }
    this.sprite.draw(ctx, sx, sy, w, h);
    ctx.globalAlpha = 1;

    if (this.attacking) {
      const { dx, dy } = this.facingDelta;
      const cx = this.pixelX - camera.x + TILE_SIZE / 2 + dx * TILE_SIZE * 0.65;
      const cy = this.pixelY - camera.y + TILE_SIZE / 2 + dy * TILE_SIZE * 0.65;
      ctx.save();
      ctx.strokeStyle = "rgba(255,255,255,0.9)";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(cx, cy, TILE_SIZE * 0.32, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }
}
