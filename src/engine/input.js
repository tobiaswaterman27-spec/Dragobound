const KEY_MAP = {
  ArrowUp: "up", KeyW: "up",
  ArrowDown: "down", KeyS: "down",
  ArrowLeft: "left", KeyA: "left",
  ArrowRight: "right", KeyD: "right",
  Space: "attack",
  Enter: "interact", KeyE: "interact",
  Escape: "cancel",
  Digit1: "digit1", Digit2: "digit2", Digit3: "digit3", Digit4: "digit4",
};

class Input {
  constructor() {
    this.down = new Set();
    this.pressed = new Set();
    window.addEventListener("keydown", (e) => {
      const action = KEY_MAP[e.code];
      if (!action) return;
      if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
        e.preventDefault();
      }
      if (!this.down.has(action)) this.pressed.add(action);
      this.down.add(action);
    });
    window.addEventListener("keyup", (e) => {
      const action = KEY_MAP[e.code];
      if (!action) return;
      this.down.delete(action);
    });
    window.addEventListener("blur", () => {
      this.down.clear();
    });
  }

  isDown(action) {
    return this.down.has(action);
  }

  wasPressed(action) {
    return this.pressed.has(action);
  }

  endFrame() {
    this.pressed.clear();
  }
}

export const input = new Input();
