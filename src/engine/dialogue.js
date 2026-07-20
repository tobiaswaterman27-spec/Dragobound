import { input } from "./input.js";

export class DialogueRunner {
  constructor(rootEl) {
    this.root = rootEl;
    this.nameEl = rootEl.querySelector(".dlg-name");
    this.textEl = rootEl.querySelector(".dlg-text");
    this.choicesEl = rootEl.querySelector(".dlg-choices");
    this.continueEl = rootEl.querySelector(".dlg-continue");
    this.active = false;
    this.tree = null;
    this.node = null;
    this.pages = [];
    this.pageIdx = 0;
    this.state = null;
    this.onEnd = null;
  }

  isActive() {
    return this.active;
  }

  start(tree, state, onEnd) {
    this.tree = tree;
    this.state = state;
    this.onEnd = onEnd;
    this.active = true;
    this.root.classList.remove("hidden");
    this._goto(tree.start);
  }

  _goto(nodeId) {
    let node = this.tree.nodes[nodeId];
    if (!node) {
      this._close();
      return;
    }
    if (typeof node.condition === "function" && !node.condition(this.state)) {
      if (node.else) {
        this._goto(node.else);
        return;
      }
      this._close();
      return;
    }
    if (typeof node.effect === "function") node.effect(this.state);
    this.node = node;
    let text = typeof node.text === "function" ? node.text(this.state) : node.text;
    this.pages = (text || "").split("|");
    this.pageIdx = 0;
    this.nameEl.textContent = node.speaker || "";
    this._renderPage();
  }

  _substitute(text) {
    const fullName = this.state?.character?.name || "friend";
    const firstName = fullName.split(" ")[0];
    return (text || "").replace(/\{name\}/g, firstName);
  }

  _renderPage() {
    this.textEl.textContent = this._substitute(this.pages[this.pageIdx]);
    const isLastPage = this.pageIdx === this.pages.length - 1;
    this.choicesEl.innerHTML = "";
    this.choicesEl.classList.add("hidden");
    this.continueEl.classList.add("hidden");
    if (isLastPage) {
      const choices = (this.node.choices || []).filter(
        (c) => typeof c.condition !== "function" || c.condition(this.state)
      );
      if (choices.length) {
        this.choicesEl.classList.remove("hidden");
        choices.forEach((choice, i) => {
          const btn = document.createElement("button");
          btn.className = "dlg-choice";
          btn.textContent = `${i + 1}. ${choice.label}`;
          btn.onclick = () => this._pick(choice);
          this.choicesEl.appendChild(btn);
        });
      } else {
        this.continueEl.classList.remove("hidden");
        this.continueEl.textContent = this.node.next ? "▼" : "(end)";
      }
    } else {
      this.continueEl.classList.remove("hidden");
      this.continueEl.textContent = "▼";
    }
  }

  _pick(choice) {
    if (typeof choice.effect === "function") choice.effect(this.state);
    if (choice.next) this._goto(choice.next);
    else this._close();
  }

  advance() {
    if (!this.active) return;
    const isLastPage = this.pageIdx === this.pages.length - 1;
    if (!isLastPage) {
      this.pageIdx++;
      this._renderPage();
      return;
    }
    const choices = (this.node.choices || []).filter(
      (c) => typeof c.condition !== "function" || c.condition(this.state)
    );
    if (choices.length) return; // must click / press number
    if (this.node.next) this._goto(this.node.next);
    else this._close();
  }

  handleNumberKey(n) {
    if (!this.active) return;
    const isLastPage = this.pageIdx === this.pages.length - 1;
    if (!isLastPage) return;
    const choices = (this.node.choices || []).filter(
      (c) => typeof c.condition !== "function" || c.condition(this.state)
    );
    if (choices[n - 1]) this._pick(choices[n - 1]);
  }

  _close() {
    this.active = false;
    this.root.classList.add("hidden");
    const cb = this.onEnd;
    this.onEnd = null;
    if (cb) cb();
  }

  update() {
    if (!this.active) return;
    if (input.wasPressed("interact") || input.wasPressed("attack")) {
      this.advance();
    }
    for (let n = 1; n <= 4; n++) {
      if (input.wasPressed("digit" + n)) this.handleNumberKey(n);
    }
  }
}
