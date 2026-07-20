import { input } from "./engine/input.js";
import { Player } from "./engine/player.js";
import { World } from "./engine/world.js";
import { DialogueRunner } from "./engine/dialogue.js";
import * as save from "./engine/save.js";

// Surface uncaught errors visibly -- a blank screen with no clue why is the
// worst failure mode, especially inside embeds where devtools aren't handy.
const fatalErrorEl = document.getElementById("fatal-error");
function showFatalError(message) {
  if (!fatalErrorEl) return;
  fatalErrorEl.textContent = `Dragobound hit an error and may not work correctly:\n${message}`;
  fatalErrorEl.classList.remove("hidden");
}
window.addEventListener("error", (e) => showFatalError(e.message || String(e.error)));
window.addEventListener("unhandledrejection", (e) => showFatalError(String(e.reason)));

// Corran Thorne is a set protagonist, not a customizable player character --
// no name entry, no palette picker.
const PROTAGONIST = { name: "Corran Thorne", palette: "player" };

const els = {
  titleScreen: document.getElementById("title-screen"),
  signinPanel: document.getElementById("signin-panel"),
  signinName: document.getElementById("signin-name"),
  btnSignin: document.getElementById("btn-signin"),
  profilePanel: document.getElementById("profile-panel"),
  profileNameLabel: document.getElementById("profile-name-label"),
  btnNewGame: document.getElementById("btn-new-game"),
  btnContinue: document.getElementById("btn-continue"),
  btnSwitchProfile: document.getElementById("btn-switch-profile"),

  gameScreen: document.getElementById("game-screen"),
  canvas: document.getElementById("game-canvas"),
  hpBar: document.getElementById("hp-bar"),
  objectiveText: document.getElementById("objective-text"),
  dialogueBox: document.getElementById("dialogue-box"),
};

const ctx = els.canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;

if (!save.isPersistent) {
  const hint = els.signinPanel.querySelector(".hint");
  if (hint) hint.textContent = "This browser is blocking saved progress here -- you can still play, it just won't be remembered after you leave.";
}

let currentSignIn = null;
let world = null;
let state = null;
let lastTime = performance.now();
let autosaveT = 0;

function showScreen(name) {
  els.titleScreen.classList.toggle("hidden", name !== "title");
  els.gameScreen.classList.toggle("hidden", name !== "game");
}

// ---------------------------------------------------------------------------
// Title screen / sign-in
// ---------------------------------------------------------------------------
function refreshProfilePanel() {
  if (!currentSignIn) return;
  els.signinPanel.classList.add("hidden");
  els.profilePanel.classList.remove("hidden");
  els.profileNameLabel.textContent = currentSignIn;
  const hasSave = save.profileExists(currentSignIn);
  els.btnContinue.classList.toggle("hidden", !hasSave);
}

els.btnSignin.addEventListener("click", () => {
  const name = els.signinName.value.trim();
  if (!name) return;
  currentSignIn = name;
  refreshProfilePanel();
});
els.signinName.addEventListener("keydown", (e) => {
  if (e.key === "Enter") els.btnSignin.click();
});

els.btnSwitchProfile.addEventListener("click", () => {
  currentSignIn = null;
  els.signinName.value = "";
  els.profilePanel.classList.add("hidden");
  els.signinPanel.classList.remove("hidden");
});

els.btnContinue.addEventListener("click", () => {
  const data = save.loadProfile(currentSignIn);
  if (!data) return;
  state = data;
  startWorld();
});

els.btnNewGame.addEventListener("click", () => {
  state = save.newGameState(currentSignIn, { ...PROTAGONIST });
  startWorld();
});

// ---------------------------------------------------------------------------
// Game bootstrap + loop
// ---------------------------------------------------------------------------
const dlg = new DialogueRunner(els.dialogueBox);

function objectiveText(s) {
  if (!s.flags.q1Done) return "A wyrmling has wandered near the east wall. Get close and press SPACE to attack!";
  if (!s.flags.q2Done) return "Find King Alden inside the Great Hall and speak with him.";
  if (!s.flags.q3Done) return "Explore Veth Hollow -- talk to people, look inside houses, find what's hidden.";
  if (s.flags.act1Complete) return "End of Act 1 (demo). Keep exploring Veth Hollow while you wait for what's next.";
  return "";
}

function startWorld() {
  showScreen("game");
  const player = new Player(state.x, state.y, `assets/sprites/${state.character.palette}.png`, state.hp, state.maxHp);
  world = new World(state, dlg, null);
  world.setPlayer(player);
  lastTime = performance.now();
  requestAnimationFrame(loop);
}

function loop(now) {
  const dt = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;

  world.update(dt);
  world.render(ctx);

  els.hpBar.style.width = `${Math.max(0, (world.player.hp / world.player.maxHp) * 100)}%`;
  els.objectiveText.textContent = objectiveText(state);

  autosaveT += dt;
  if (autosaveT > 3) {
    autosaveT = 0;
    save.saveProfile(state.signInName, state);
  }

  if (world.player.dead) {
    respawnPlayer();
  }

  input.endFrame();
  requestAnimationFrame(loop);
}

function respawnPlayer() {
  world.showToast("You were downed -- carried back to safety.");
  world.player.hp = world.player.maxHp;
  world.player.dead = false;
  const spawn = { x: 9, y: 10, facing: "down" };
  world._loadMap("hollow", spawn);
}

showScreen("title");

// Lightweight debug hook for manual/automated QA in the browser console.
window.dragobound = {
  get world() { return world; },
  get state() { return state; },
};
