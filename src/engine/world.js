import { TileMap, TILE_SIZE } from "./tilemap.js";
import { Npc } from "./npc.js";
import { Enemy } from "./enemy.js";
import { Player } from "./player.js";
import { input } from "./input.js";
import { MAP_DEFS } from "../data/maps.js";
import { DIALOGUES } from "../data/dialogues.js";

const VIEW_W = 704;
const VIEW_H = 576;

function resolveDialogueId(spec, state) {
  return typeof spec === "function" ? spec(state) : spec;
}

export class World {
  constructor(state, dialogueRunner, hud) {
    this.state = state;
    this.dlg = dialogueRunner;
    this.hud = hud;
    this.map = null;
    this.player = null;
    this.npcs = [];
    this.enemies = [];
    this.camera = { x: 0, y: 0 };
    this.fadeT = 0;
    this.fading = false;
    this.pendingSpawn = null;
    this.toast = null;
    this.toastT = 0;
  }

  _loadMap(mapId, spawn) {
    const def = MAP_DEFS[mapId];
    this.map = new TileMap(def);
    this.npcs = (def.npcs || [])
      .filter((n) => !n.hideIf || !n.hideIf(this.state))
      .map((n) => new Npc(n));
    this.enemies = (def.enemies || [])
      .filter((e) => !this.state.flags["defeated_" + e.id])
      .map((e) => new Enemy(e));
    this.triggers = (def.triggers || []).map((t) => ({ ...t, fired: !!this.state.flags["trigger_" + t.id] }));

    this.player.gridX = spawn.x;
    this.player.gridY = spawn.y;
    this.player.facing = spawn.facing || "down";
    this.player.pixelX = spawn.x * TILE_SIZE;
    this.player.pixelY = spawn.y * TILE_SIZE;
    this.player.moving = false;

    this.state.map = mapId;
    this.state.x = spawn.x;
    this.state.y = spawn.y;
    this.state.facing = this.player.facing;
  }

  setPlayer(player) {
    this.player = player;
    const spawn = { x: this.state.x, y: this.state.y, facing: this.state.facing };
    this._loadMap(this.state.map, spawn);
  }

  canWalk(x, y) {
    if (this.map.isSolid(x, y)) return false;
    if (this.npcs.some((n) => n.gridX === x && n.gridY === y)) return false;
    if (this.enemies.some((e) => !e.dead && e.gridX === x && e.gridY === y)) return false;
    if (this.player && this.player.gridX === x && this.player.gridY === y) return false;
    return true;
  }

  showToast(text, dur = 2.5) {
    this.toast = text;
    this.toastT = dur;
  }

  _startDialogue(id, npc) {
    const tree = DIALOGUES[id];
    if (!tree) return;
    this.player.controlsEnabled = false;
    this.dlg.start(tree, this.state, () => {
      this.player.controlsEnabled = true;
      if (npc && npc.facePlayerAfter) {
        // no-op hook for future use
      }
    });
  }

  handleInteract() {
    if (this.dlg.isActive()) return;
    const front = this.player.frontTile;
    const npc = this.npcs.find((n) => n.gridX === front.x && n.gridY === front.y);
    if (npc) {
      npc.facing = oppositeDir(this.player.facing);
      const id = npc.dialogueId ? resolveDialogueId(npc.dialogueId, this.state) : null;
      if (id) this._startDialogue(id, npc);
      return;
    }
    const inter = this.map.interactableAt(front.x, front.y);
    if (inter) {
      this._startDialogue(inter.dialogueId, null);
    }
  }

  _checkDoors() {
    const door = this.map.doorAt(this.player.gridX, this.player.gridY);
    if (door) {
      this._loadMap(door.to, door.spawn);
    }
  }

  _checkTriggers() {
    for (const t of this.triggers) {
      if (t.fired) continue;
      if (t.x === this.player.gridX && t.y === this.player.gridY) {
        if (t.condition && !t.condition(this.state)) continue;
        t.fired = true;
        this.state.flags["trigger_" + t.id] = true;
        this._startDialogue(t.dialogueId, null);
      }
    }
  }

  _onPlayerAttack(frontTile) {
    for (const e of this.enemies) {
      if (e.dead) continue;
      if (e.gridX === frontTile.x && e.gridY === frontTile.y) {
        e.takeDamage(5);
        if (e.dead) {
          this.state.flags["defeated_" + e.id] = true;
          if (e.id === "wyrmling_q1") {
            this.state.flags.q1Done = true;
            this.showToast("Wyrmling defeated!");
          }
        }
      }
    }
  }

  update(dt) {
    if (this.dlg.isActive()) {
      this.dlg.update();
      this.player.sprite.update(dt, this.player.facing, false);
      return;
    }

    if (input.wasPressed("interact")) this.handleInteract();

    this.player.update(dt, this, (frontTile) => this._onPlayerAttack(frontTile));
    if (!this.player.moving) {
      this._checkDoors();
      this._checkTriggers();
    }
    this.state.x = this.player.gridX;
    this.state.y = this.player.gridY;
    this.state.facing = this.player.facing;
    this.state.hp = this.player.hp;

    this.npcs.forEach((n) => n.update(dt, this, (x, y) => this.enemies.some((e) => !e.dead && e.gridX === x && e.gridY === y)));
    this.enemies.forEach((e) => e.update(dt, this, this.player, (enemy) => this.player.takeDamage(enemy.damage)));

    const camX = this.player.pixelX + TILE_SIZE / 2 - VIEW_W / 2;
    const camY = this.player.pixelY + TILE_SIZE / 2 - VIEW_H / 2;
    const maxX = Math.max(0, this.map.width * TILE_SIZE - VIEW_W);
    const maxY = Math.max(0, this.map.height * TILE_SIZE - VIEW_H);
    this.camera.x = Math.min(Math.max(0, camX), maxX);
    this.camera.y = Math.min(Math.max(0, camY), maxY);

    if (this.toastT > 0) this.toastT -= dt;
  }

  render(ctx) {
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, VIEW_W, VIEW_H);
    this.map.render(ctx, this.camera, VIEW_W, VIEW_H);

    const drawables = [
      ...this.npcs.map((n) => ({ y: n.gridY, draw: () => n.draw(ctx, this.camera) })),
      ...this.enemies.map((e) => ({ y: e.gridY, draw: () => e.draw(ctx, this.camera) })),
      { y: this.player.gridY, draw: () => this.player.draw(ctx, this.camera) },
    ];
    drawables.sort((a, b) => a.y - b.y);
    drawables.forEach((d) => d.draw());

    this._renderPrompt(ctx);
    this._renderToast(ctx);
  }

  _renderPrompt(ctx) {
    if (this.dlg.isActive()) return;
    const front = this.player.frontTile;
    const hasNpc = this.npcs.some((n) => n.gridX === front.x && n.gridY === front.y);
    const hasInteractable = this.map.interactableAt(front.x, front.y);
    if (!hasNpc && !hasInteractable) return;
    const sx = front.x * TILE_SIZE - this.camera.x + TILE_SIZE / 2;
    const sy = front.y * TILE_SIZE - this.camera.y - 6;
    ctx.save();
    ctx.font = "bold 20px monospace";
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(sx - 26, sy - 24, 52, 26);
    ctx.fillStyle = "#ffe9a8";
    ctx.fillText("[E]", sx, sy - 5);
    ctx.restore();
  }

  _renderToast(ctx) {
    if (this.toastT <= 0) return;
    ctx.save();
    ctx.globalAlpha = Math.min(1, this.toastT);
    ctx.font = "bold 22px monospace";
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(20,16,10,0.8)";
    ctx.fillRect(VIEW_W / 2 - 160, 24, 320, 40);
    ctx.fillStyle = "#ffe9a8";
    ctx.fillText(this.toast, VIEW_W / 2, 50);
    ctx.restore();
  }
}

function oppositeDir(dir) {
  return { up: "down", down: "up", left: "right", right: "left" }[dir] || "down";
}

export { VIEW_W, VIEW_H };
