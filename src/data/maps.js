// Map layout data. Row strings use the legend defined in engine/tilemap.js.
// Coordinates are tile indices (x = column, y = row), origin top-left.

const HOLLOW_ROWS = [
  "##################",
  "#.RRRRR..RRRR....#",
  "#.WWWWW.rWWWWr...#",
  "#.WWWWW..WDWW..~~#",
  "#.WWDWW........~~#",
  "#...p......p.....#",
  "#...p....b.p..r..#",
  "#...p.b....p.....#",
  "#pppppppppppppppp#",
  "#RRRR........RRRR#",
  "#WWWW........WWWW#",
  "#WDWW..r....rWDWW#",
  "#...p............#",
  "##################",
];

export const MAP_DEFS = {
  hollow: {
    id: "hollow",
    name: "Veth Hollow",
    rows: HOLLOW_ROWS,
    doors: [
      { x: 4, y: 4, to: "castle", spawn: { x: 4, y: 5, facing: "up" } },
      { x: 10, y: 3, to: "holt_house", spawn: { x: 3, y: 4, facing: "up" } },
      { x: 14, y: 11, to: "ashwood_house", spawn: { x: 3, y: 4, facing: "up" } },
      { x: 2, y: 11, to: "sela_house", spawn: { x: 3, y: 4, facing: "up" } },
    ],
    interactables: [],
    npcs: [
      {
        id: "joran",
        name: "Joran Holt",
        sheet: "joran",
        x: 7,
        y: 7,
        wanderRange: 2,
        dialogueId: (s) => (s.flags.q1Done ? "joran_after_q1" : "joran_intro"),
      },
    ],
    enemies: [{ id: "wyrmling_q1", kind: "wyrmling", x: 15, y: 6, hp: 10, damage: 2, aggroRange: 3, leashRange: 4 }],
    triggers: [
      {
        id: "q3_tribute",
        x: 8,
        y: 8,
        once: true,
        condition: (s) => s.flags.q2Done && !s.flags.q3Done,
        dialogueId: "king_tribute",
      },
    ],
  },

  castle: {
    id: "castle",
    name: "Veth Hollow -- Great Hall",
    rows: [
      "#########",
      "#wwwwwww#",
      "#wwwwwww#",
      "#wwwTwww#",
      "#wKwwwww#",
      "#wwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 6, to: "hollow", spawn: { x: 4, y: 5, facing: "down" } }],
    interactables: [{ x: 2, y: 4, id: "diary", dialogueId: "diary" }],
    npcs: [
      { id: "king", name: "King Alden Vethar", sheet: "king", x: 4, y: 2, facing: "down", wanderRange: 0,
        hideIf: (s) => s.flags.kingDead,
        dialogueId: (s) => (!s.flags.q1Done ? "king_locked" : !s.flags.q2Done ? "king_council" : "king_locked") },
      { id: "marrow", name: "Marrow Fenn", sheet: "marrow", x: 6, y: 2, facing: "down", wanderRange: 0, dialogueId: null },
    ],
    enemies: [],
    triggers: [],
  },

  holt_house: {
    id: "holt_house",
    name: "The Holts' House",
    rows: [
      "#########",
      "#wwwwwww#",
      "#wBwTwBw#",
      "#wwwwwww#",
      "#wwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 5, to: "hollow", spawn: { x: 10, y: 4, facing: "down" } }],
    interactables: [],
    npcs: [
      { id: "tobin_yssa", name: "Tobin Holt", sheet: "villager_m", x: 2, y: 3, wanderRange: 1, dialogueId: "tobin_yssa" },
      { id: "wren", name: "Wren Holt", sheet: "child", x: 6, y: 3, wanderRange: 1, dialogueId: "wren" },
    ],
    enemies: [],
    triggers: [],
  },

  ashwood_house: {
    id: "ashwood_house",
    name: "The Ashwoods' House",
    rows: [
      "#########",
      "#wwwwwww#",
      "#wBwTwCw#",
      "#wwwwwww#",
      "#wwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 5, to: "hollow", spawn: { x: 14, y: 12, facing: "down" } }],
    interactables: [],
    npcs: [
      { id: "garrick_mira", name: "Garrick Ashwood", sheet: "villager_m", x: 2, y: 3, wanderRange: 1,
        dialogueId: (s) => (s.flags.knifeReceived ? "garrick_mira_return" : "garrick_mira") },
      { id: "pell", name: "Pell Ashwood", sheet: "child", x: 6, y: 3, wanderRange: 1, dialogueId: "pell" },
    ],
    enemies: [],
    triggers: [],
  },

  sela_house: {
    id: "sela_house",
    name: "Sela's House",
    rows: [
      "#########",
      "#wwwwwww#",
      "#wwTwwww#",
      "#wwwwwww#",
      "#wwwBwww#",
      "#wwwwwww#",
      "####D####",
    ],
    doors: [{ x: 4, y: 6, to: "hollow", spawn: { x: 2, y: 12, facing: "down" } }],
    interactables: [],
    npcs: [{ id: "sela", name: "Sela Vane", sheet: "villager_f", x: 4, y: 2, wanderRange: 1, dialogueId: "sela" }],
    enemies: [],
    triggers: [],
  },
};
