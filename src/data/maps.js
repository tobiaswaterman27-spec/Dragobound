// Map layout data. Row strings use the legend in engine/tilemap.js.
// Veth Hollow is a wasteland: barren ground, a ruined castle, a withered
// potato plot, a log wagon by the gate. Act 1 plays out here.

export const MAP_DEFS = {
  hollow: {
    id: "hollow",
    name: "Veth Hollow",
    rows: [
      "######################",
      "#aRRRRRaaa...........#",
      "#acucccaaa.....PPPPPt#",
      "#accDucaaa..t.pPPPPP.#",
      "#anaaanaaa.....PPPPP.#",
      "#aaupraaaa........r..#",
      "#aaapaaaaa..b..RRRR..#",
      '#...p"t....r.t.WWWWbt#',
      "#t..p.ro.......WDWW..#",
      "#...pppppppppppppp...#",
      '#.r.p.....p...r"p....#',
      '#.RRpR....p..b..pRRR"#',
      "#.WWpW.t.bp.....WWWW.#",
      "#.WDpWee..p.GL..WDWW.#",
      "#...p...e.p..ee....t.#",
      "##########AA##########",
    ],
    doors: [
      { x: 4, y: 3, to: "hall", spawn: { x: 5, y: 6, facing: "up" } },
      { x: 16, y: 8, to: "holt_house", spawn: { x: 4, y: 6, facing: "up" } },
      { x: 17, y: 13, to: "ashwood_house", spawn: { x: 4, y: 6, facing: "up" } },
      { x: 3, y: 13, to: "sela_house", spawn: { x: 4, y: 6, facing: "up" } },
      // the gate only opens once tribute day is over
      { x: 10, y: 15, to: "gate_road", spawn: { x: 4, y: 10, facing: "up" }, requires: "tributeDone" },
      { x: 11, y: 15, to: "gate_road", spawn: { x: 4, y: 10, facing: "up" }, requires: "tributeDone" },
    ],
    interactables: [],
    npcs: [
      { id: "alden", name: "King Alden Vethar", sheet: "king", x: 5, y: 8, wanderRange: 1,
        hideIf: (s) => s.flags.horn || s.flags.kingDead,
        dialogueId: "alden_hollow" },
      { id: "joran", name: "Joran Holt", sheet: "joran", x: 8, y: 10, wanderRange: 2,
        hideIf: (s) => s.flags.horn,
        dialogueId: "joran_intro" },
      { id: "marrow", name: "Marrow Fenn", sheet: "marrow", x: 3, y: 7, wanderRange: 1,
        hideIf: (s) => s.flags.horn,
        dialogueId: "marrow_hollow" },
      { id: "tobin", name: "Tobin Holt", sheet: "tobin", x: 14, y: 3, wanderRange: 1,
        hideIf: (s) => s.flags.horn,
        dialogueId: "tobin" },
      { id: "garrick", name: "Garrick Ashwood", sheet: "garrick", x: 11, y: 13, wanderRange: 1,
        hideIf: (s) => s.flags.horn,
        dialogueId: (s) => (s.flags.knifeReceived ? "garrick_return" : "garrick") },
      { id: "pell", name: "Pell Ashwood", sheet: "pell", x: 10, y: 14, wanderRange: 1,
        hideIf: (s) => s.flags.horn,
        dialogueId: "pell" },
      // Tribute Day: the Solmeran captain appears at the gate after the council
      { id: "captain", name: "Solmeran Captain", sheet: "soldier", x: 10, y: 14, facing: "up", wanderRange: 0,
        showIf: (s) => s.flags.councilDone && !s.flags.tributeDone,
        dialogueId: "tribute" },
    ],
    enemies: [],
    triggers: [
      // after the council, the soldiers are at the gate -- Tribute Day fires
      // as you approach it
      { id: "tribute_scene", x: 10, y: 11, once: true,
        condition: (s) => s.flags.councilDone && !s.flags.tributeDone,
        dialogueId: "tribute" },
    ],
  },

  // ---- Ruined great hall (Council scene + the hidden diary) ----
  hall: {
    id: "hall",
    name: "Veth Hollow -- The Ruined Hall",
    rows: [
      "###########",
      "#wwwwwwwww#",
      "#wn.....nw#",
      "#w.TTTTT.w#",
      "#w.H.H.H.w#",
      "#wK..h..uw#",
      "#wwwwwwwww#",
      "#####D#####",
    ],
    doors: [{ x: 5, y: 7, to: "hollow", spawn: { x: 4, y: 4, facing: "down" } }],
    interactables: [{ x: 2, y: 5, id: "diary", dialogueId: "diary" }],
    npcs: [],
    enemies: [],
    triggers: [
      // Q2/Q3: the Council speech and Pell's interruption fire the moment
      // everyone walks into the hall together.
      { id: "council_scene", x: 5, y: 6, once: true,
        condition: (s) => s.flags.horn && !s.flags.councilDone,
        dialogueId: "council" },
    ],
  },

  holt_house: {
    id: "holt_house",
    name: "The Holts' House",
    rows: [
      "#########",
      "#wsiwwis#",
      "#wB.T.Bw#",
      "#wg.H.gw#",
      "#w.q.h.w#",
      "#wwwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 6, to: "hollow", spawn: { x: 16, y: 9, facing: "down" } }],
    interactables: [],
    npcs: [
      { id: "yssa", name: "Yssa Holt", sheet: "yssa", x: 3, y: 3, wanderRange: 1,
        hideIf: (s) => s.flags.horn, dialogueId: "yssa" },
      { id: "wren", name: "Wren Holt", sheet: "wren", x: 6, y: 3, wanderRange: 1,
        hideIf: (s) => s.flags.horn, dialogueId: "wren" },
    ],
    enemies: [],
    triggers: [],
  },

  ashwood_house: {
    id: "ashwood_house",
    name: "The Ashwoods' House",
    rows: [
      "#########",
      "#wsiwwix#",
      "#wB.T.Xw#",
      "#wg.H..w#",
      "#w.h.q.w#",
      "#wwwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 6, to: "hollow", spawn: { x: 17, y: 14, facing: "down" } }],
    interactables: [],
    npcs: [
      { id: "mira", name: "Mira Ashwood", sheet: "mira", x: 3, y: 3, wanderRange: 1,
        hideIf: (s) => s.flags.horn, dialogueId: "mira" },
    ],
    enemies: [],
    triggers: [],
  },

  sela_house: {
    id: "sela_house",
    name: "Sela's House",
    rows: [
      "#########",
      "#wsiwwsw#",
      "#w.T.h.w#",
      "#wg.H..w#",
      "#w.B..yw#",
      "#wwwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 6, to: "hollow", spawn: { x: 3, y: 14, facing: "down" } }],
    interactables: [],
    npcs: [
      { id: "sela", name: "Sela Vane", sheet: "sela", x: 4, y: 2, wanderRange: 1,
        hideIf: (s) => s.flags.horn, dialogueId: "sela" },
    ],
    enemies: [],
    triggers: [],
  },

  // ---- Just beyond the gate: the tree line, and the first real fight ----
  gate_road: {
    id: "gate_road",
    name: "Beyond the Gate",
    rows: [
      ",,,,t,,,,",
      ",,t,,,t,,",
      ",,,,,,,,t",
      "t,,,,,,,,",
      ",,,,,,,,,",
      ",,,t,,,,,",
      ",,,,,,t,,",
      "t,,,,,,,,",
      ",,,,,,,,t",
      ",,t,,,,,,",
      ",,,,,,,,,",
      ",,,,#A#,,",
    ],
    doors: [],
    interactables: [],
    npcs: [],
    enemies: [
      { id: "wyrmling_gate", kind: "wyrmling", x: 4, y: 3, hp: 10, damage: 2, aggroRange: 4, leashRange: 6 },
    ],
    triggers: [
      { id: "gate_intro", x: 4, y: 10, once: true, condition: () => true, dialogueId: "gate_wyrmling" },
    ],
  },
};
