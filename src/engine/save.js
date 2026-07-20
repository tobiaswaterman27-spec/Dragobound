const INDEX_KEY = "dragobound:profiles";
const SAVE_PREFIX = "dragobound:save:";

// Sandboxed iframes (including the one Artifacts render in) sometimes block
// localStorage entirely -- reads/writes can throw, or the object can be
// missing. Fall back to an in-memory store so the game stays playable for
// the session even when nothing can actually persist.
function makeStorage() {
  try {
    const probeKey = "dragobound:probe";
    window.localStorage.setItem(probeKey, "1");
    window.localStorage.removeItem(probeKey);
    return {
      get: (k) => window.localStorage.getItem(k),
      set: (k, v) => window.localStorage.setItem(k, v),
      remove: (k) => window.localStorage.removeItem(k),
      persistent: true,
    };
  } catch {
    const mem = new Map();
    return {
      get: (k) => (mem.has(k) ? mem.get(k) : null),
      set: (k, v) => mem.set(k, v),
      remove: (k) => mem.delete(k),
      persistent: false,
    };
  }
}

const storage = makeStorage();
export const isPersistent = storage.persistent;

function readIndex() {
  try {
    return JSON.parse(storage.get(INDEX_KEY)) || [];
  } catch {
    return [];
  }
}

function writeIndex(list) {
  try {
    storage.set(INDEX_KEY, JSON.stringify(list));
  } catch {
    // Storage full or blocked mid-session -- progress just won't persist.
  }
}

export function listProfiles() {
  return readIndex();
}

export function profileExists(name) {
  return readIndex().includes(name.toLowerCase());
}

export function loadProfile(name) {
  let raw;
  try {
    raw = storage.get(SAVE_PREFIX + name.toLowerCase());
  } catch {
    return null;
  }
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
  try {
    storage.set(SAVE_PREFIX + key, JSON.stringify({ ...data, savedAt: Date.now() }));
  } catch {
    // Storage full or blocked mid-session -- progress just won't persist.
  }
}

export function deleteProfile(name) {
  const key = name.toLowerCase();
  const idx = readIndex().filter((n) => n !== key);
  writeIndex(idx);
  try {
    storage.remove(SAVE_PREFIX + key);
  } catch {
    // ignore
  }
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
