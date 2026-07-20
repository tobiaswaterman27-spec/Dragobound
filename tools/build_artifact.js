// Bundles the multi-file ES-module game into a single self-contained HTML
// file (inline CSS/JS) so it can be published as a Claude Artifact, which
// forbids external requests. All art is hand-authored pixel-matrix data in
// src/data/sprites.js -- there are no image files to embed.
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const OUT = process.argv[2] || "/tmp/dragobound_artifact.html";

function stripModuleSyntax(src) {
  return src
    .replace(/^import\s+.*?;\s*$/gm, "")
    .replace(/^import\s+\*\s+as\s+\w+\s+from\s+.*?;\s*$/gm, "")
    .replace(/^export\s+default\s+/gm, "")
    .replace(/^export\s+\{[^}]*\};?\s*$/gm, "")
    .replace(/^export\s+/gm, "");
}

const MODULE_ORDER = [
  "src/engine/input.js",
  "src/engine/save.js",
  "src/data/sprites.js",
  "src/engine/sprite.js",
  "src/engine/tilemap.js",
  "src/engine/entity.js",
  "src/engine/player.js",
  "src/engine/enemy.js",
  "src/engine/npc.js",
  "src/engine/dialogue.js",
  "src/data/dialogues.js",
  "src/data/maps.js",
  "src/engine/world.js",
  "src/main.js",
];

// --- 1. Bundle JS modules in dependency order, stripping import/export. ---
let bundle = "";
for (const rel of MODULE_ORDER) {
  const src = fs.readFileSync(path.join(ROOT, rel), "utf8");
  bundle += `\n// ---- ${rel} ----\n` + stripModuleSyntax(src) + "\n";
  if (rel === "src/engine/save.js") {
    // main.js does `import * as save from "./engine/save.js"` -- rebuild that
    // namespace object since named exports were flattened into this scope.
    bundle += "\nconst save = { listProfiles, profileExists, loadProfile, saveProfile, deleteProfile, newGameState };\n";
  }
}

// --- 2. Inline CSS. ---
const css = fs.readFileSync(path.join(ROOT, "src/style.css"), "utf8");

// --- 3. Reuse the body markup from index.html (everything between <body> and the module script). ---
const indexHtml = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const bodyMatch = indexHtml.match(/<body>([\s\S]*?)<script type="module"/);
const bodyMarkup = bodyMatch[1].trim();

const html = `<meta charset="UTF-8" />
<title>Dragobound</title>
<style>
${css}
</style>
${bodyMarkup}
<script>
${bundle}
</script>
`;

fs.writeFileSync(OUT, html, "utf8");
console.log("wrote", OUT, `(${(html.length / 1024).toFixed(1)} KB)`);
