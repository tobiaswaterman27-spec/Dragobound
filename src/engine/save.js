const INDEX_KEY = "dragobound:profiles";
const SAVE_PREFIX = "dragobound:save:";

function readIndex() {
  try {
    return JSON.parse(localStorage.getItem(INDEX_KEY)) || [];
  } catch {
    return [];
  }
}

function writeIndex(list) {
  localStorage.setItem(INDEX_KEY, JSON.stringify(list));
}

export function listProfiles() {
  return readIndex();
}

export function profileExists(name) {
  return readIndex().includes(name.toLowerCase());
}

export function loadProfile(name) {
  const raw = localStorage.getItem(SAVE_PREFIX + name.toLowerCase());
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveProfile(name, data) {
  const key = name.toLowerCase();
  const idx = readIndex();
  if (!idx.includes(key)) {
    idx.push(key);
    writeIndex(idx);
  }
  localStorage.setItem(
    SAVE_PREFIX + key,
    JSON.stringify({ ...data, savedAt: Date.now() })
  );
}

export function deleteProfile(name) {
  const key = name.toLowerCase();
  const idx = readIndex().filter((n) => n !== key);
  writeIndex(idx);
  localStorage.removeItem(SAVE_PREFIX + key);
}

export function newGameState(signInName, character) {
  return {
    signInName,
    character,
    flags: {},
    map: "hollow",
    x: 9,
    y: 10,
    facing: "down",
    hp: 20,
    maxHp: 20,
  };
}
