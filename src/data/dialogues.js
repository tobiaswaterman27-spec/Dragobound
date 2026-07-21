// Dialogue trees for Act 1. Each node: { speaker, text (pages separated by "|"),
// choices: [{label, next, effect, condition}], next, condition, effect, else }
// `state` is the live save-state object (state.flags holds story flags).

export const DIALOGUES = {
  // ---- Q1: A Quiet Morning -- ten short personal scenes ----

  alden_hollow: {
    start: "root",
    nodes: {
      root: {
        speaker: "King Alden Vethar",
        condition: (s) => !s.flags.met_alden,
        effect: (s) => { s.flags.met_alden = true; },
        text: "Up early, {name}. Good. I'll want you sharp today.|Solmere's collectors are due within the week. I mean to have words with their captain this time, about the tribute weighing more each season while we have less and less to give.|You've grown into a fine young man. Your father would be proud of the knight you're becoming -- I only wish I could say I did more than watch from a distance.",
        next: null,
        else: "again",
      },
      again: {
        speaker: "King Alden Vethar",
        text: "Go on, {name}. See to the others before the day gets away from us.",
        next: null,
      },
    },
  },

  joran_intro: {
    start: "root",
    nodes: {
      root: {
        speaker: "Joran Holt",
        condition: (s) => !s.flags.met_joran,
        effect: (s) => { s.flags.met_joran = true; },
        text: "Couldn't sleep either, huh?|Feels wrong, doesn't it. Same cracked walls, same eleven doors, same wasteland past the fence line. Some mornings I forget there's a whole world past the Greywood.|Marrow says a wyrmling's been sniffing around the tree line again. Watch yourself if you go past the gate.",
        next: null,
        else: "again",
      },
      again: {
        speaker: "Joran Holt",
        text: "Quiet morning. Won't stay that way, I'd bet.",
        next: null,
      },
    },
  },

  marrow_hollow: {
    start: "root",
    nodes: {
      root: {
        speaker: "Marrow Fenn",
        condition: (s) => !s.flags.met_marrow,
        effect: (s) => { s.flags.met_marrow = true; },
        text: "You're up before the sun's earned it. Come to pick my brain, or just to see if I ever actually sleep?|I've been at the old records again. Solmere never formally annexed the Hollow, never renamed it, never resettled it -- for a hundred years of conquest, that's not carelessness. That's a rule someone's still following.|I don't have the shape of it yet. But I will. Ask me again when I do.",
        next: null,
        else: "again",
      },
      again: {
        speaker: "Marrow Fenn",
        text: "Still turning it over in my head. Give me time.",
        next: null,
      },
    },
  },

  tobin: {
    start: "root",
    nodes: {
      root: {
        speaker: "Tobin Holt",
        condition: (s) => !s.flags.met_tobin,
        effect: (s) => { s.flags.met_tobin = true; },
        text: "Morning, {name}. Come look at this if you want to see something sorry.|Potatoes are smaller every year. Soil's gone tired and grey same as the rest of the Hollow. Half this row won't be worth pulling.|But we feed the Hollow before we feed ourselves, and we'll find something to hand the collectors besides. Always have.",
        next: null,
        else: "again",
      },
      again: {
        speaker: "Tobin Holt",
        text: "Still not much to show for it. But it's ours.",
        next: null,
      },
    },
  },

  yssa: {
    start: "root",
    nodes: {
      root: {
        speaker: "Yssa Holt",
        condition: (s) => !s.flags.met_yssa,
        effect: (s) => { s.flags.met_yssa = true; },
        text: "Don't mind Tobin, he tells that potato story to anyone who'll stand still.|You watch out for our boy when you two are off together. Joran puts on a brave face, but he's scared same as anyone -- he just won't say it where Wren can hear.",
        next: null,
        else: "again",
      },
      again: { speaker: "Yssa Holt", text: "Go on, dear. Long day ahead, I expect.", next: null },
    },
  },

  wren: {
    start: "root",
    nodes: {
      root: {
        speaker: "Wren Holt",
        condition: (s) => !s.flags.met_wren,
        effect: (s) => { s.flags.met_wren = true; },
        text: "You and Joran are always off somewhere together. Never me.|I'm not a baby, you know. I could hold a sword if anyone bothered to teach me.|...Just don't let him do anything stupid out there. He listens to you more than he lets on.",
        next: null,
        else: "again",
      },
      again: { speaker: "Wren Holt", text: "One day I'm coming with you. Just watch.", next: null },
    },
  },

  garrick: {
    start: "root",
    nodes: {
      root: {
        speaker: "Garrick Ashwood",
        text: "Figured you'd come by before the day got ahead of us. Here.",
        next: "give_knife",
      },
      give_knife: {
        speaker: "Garrick Ashwood",
        condition: (s) => !s.flags.knifeReceived,
        effect: (s) => { s.flags.knifeReceived = true; s.flags.met_garrick = true; },
        text: "This was your father's. I kept it since the day I found him in the Greywood and buried him myself -- didn't feel right leaving it with the dirt.|Good edge. Never once let me down out there. It's past time it went back to Thorne blood.|Bring yourself home in one piece. Don't much care about the knife.",
        next: null,
        else: "return",
      },
      return: { speaker: "Garrick Ashwood", text: "Knife treating you well? Good.", next: null },
    },
  },
  garrick_return: {
    start: "root",
    nodes: {
      root: {
        speaker: "Garrick Ashwood",
        text: "Knife treating you well?|Good. Now get moving before Mira starts fussing over you too.",
        next: null,
      },
    },
  },

  mira: {
    start: "root",
    nodes: {
      root: {
        speaker: "Mira Ashwood",
        condition: (s) => !s.flags.met_mira,
        effect: (s) => { s.flags.met_mira = true; },
        text: "Garrick would give away his own boots if you asked him twice. Hope he didn't talk your ear off.|Pell hasn't stopped following you with his eyes since he could walk. Go easy on him -- he's young enough to still think all this is exciting.",
        next: null,
        else: "again",
      },
      again: { speaker: "Mira Ashwood", text: "Mind yourself out there, {name}.", next: null },
    },
  },

  pell: {
    start: "root",
    nodes: {
      root: {
        speaker: "Pell Ashwood",
        condition: (s) => !s.flags.met_pell,
        effect: (s) => { s.flags.met_pell = true; },
        text: "I'm keeping watch today! Da says someone's got to and I've got the sharpest eyes in the Hollow.|Someday I'm going to fight one of those things myself. A big one, not just a wyrmling.",
        choices: [
          { label: "Maybe someday.", next: "maybe" },
          { label: "Stay safe up there, Pell.", next: "safe" },
        ],
      },
      maybe: { speaker: "Pell Ashwood", text: "You'll see! I mean it!", next: null },
      safe: { speaker: "Pell Ashwood", text: "...Yeah. Okay. I'll shout if I see anything.", next: null },
    },
  },

  sela: {
    start: "root",
    nodes: {
      root: {
        speaker: "Sela Vane",
        condition: (s) => !s.flags.met_sela,
        effect: (s) => { s.flags.met_sela = true; },
        text: "Come to check on the widow, have you? You're kind, for a soon-to-be knight.|Careful out there, {name}. The Greywood doesn't care how brave you are, and neither does Solmere.",
        choices: [
          { label: "How did you lose your arm?", next: "arm" },
          { label: "Do you have family besides yourself?", next: "family" },
          { label: "Take care, Sela.", next: null },
        ],
      },
      arm: {
        speaker: "Sela Vane",
        text: "A long time ago. A different kind of war than the one you're about to see.|I don't talk about it much. Some days I still reach for things with a hand that isn't there anymore.",
        next: null,
      },
      family: {
        speaker: "Sela Vane",
        text: "...Not anymore. Just me and these four walls.",
        next: null,
      },
    },
  },

  diary: {
    start: "root",
    nodes: {
      root: {
        speaker: "Weathered Diary",
        condition: (s) => !s.flags.diaryFound,
        effect: (s) => { s.flags.diaryFound = true; },
        text: "Tucked under a loose stone in the ruined hall, forgotten by everyone but you. The leather cover has gone soft with age.|The early pages are just a household ledger -- grain counts, a bad winter, a cough that wouldn't quit.|Near the end, the handwriting changes. Smaller. Faster.|\"...if you're old enough to read this, I'm sorry I couldn't stay to explain it myself. Garrick will see you get this, if nothing else of mine. Be good. Be brave. I love you more than the Hollow itself.\"|You sit with that a while before you put it back.",
        next: null,
        else: "reread",
      },
      reread: {
        speaker: "Weathered Diary",
        text: "You already read this, all the way to the last page.|You don't need to again. You remember it.",
        next: null,
      },
    },
  },

  // ---- The horn sounds once everyone has been met ----
  horn_sounds: {
    start: "root",
    nodes: {
      root: {
        speaker: "",
        effect: (s) => { s.flags.horn = true; },
        text: "A horn sounds across the Hollow -- long, low, unmistakable.|One by one, doors open. Every face you've spoken to this morning turns toward the ruined hall.|Alden is calling the whole town in.",
        next: null,
      },
    },
  },

  // ---- Q2 + Q3: The Council, interrupted ----
  council: {
    start: "root",
    nodes: {
      root: {
        speaker: "",
        text: "The town files into the ruined hall together, packing in around the broken columns. Alden waits at the far end, alone with the weight of what he's about to say.",
        next: "alden_speech",
      },
      alden_speech: {
        speaker: "King Alden Vethar",
        text: "Thank you for coming. All of you.|You all know Solmere has let Veth Hollow keep its own name, its own roof, its own king, when every other conquered village lost all three in a season. You've heard me call it mercy. It was never mercy.|There is an old word for what we are -- older than the war itself. So long as Veth Hollow still stands as its own people, Solmere fears what ceasing to exist would bring down on them. That fear is the only wall that has ever truly protected us.|I believe that wall is wearing thin. I believe Solmere is done being afraid of us.",
        next: "pell_burst",
      },
      pell_burst: {
        speaker: "Pell Ashwood",
        text: "They're here! I saw them coming through the forest -- soldiers, a whole column of them!",
        next: "yssa_fear",
      },
      yssa_fear: { speaker: "Yssa Holt", text: "Already? It's not even tribute season yet--", next: "tobin_calm" },
      tobin_calm: { speaker: "Tobin Holt", text: "Easy. Easy. Panicking won't slow them down any.", next: "mira_fear" },
      mira_fear: { speaker: "Mira Ashwood", text: "Pell, get behind me. Now.", next: "marrow_calm" },
      marrow_calm: { speaker: "Marrow Fenn", text: "This early is wrong. Whatever they want, it isn't routine.", next: "joran_calm" },
      joran_calm: { speaker: "Joran Holt", text: "Then we go out and find out together. Standing in here won't help anyone.", next: "alden_lead" },
      alden_lead: {
        speaker: "King Alden Vethar",
        effect: (s) => {
          s.flags.councilDone = true;
          s.flags.pendingMapTransition = { to: "hollow", spawn: { x: 10, y: 11, facing: "down" } };
        },
        text: "Everyone, outside. Stay together.|Whatever this is, we face it as the Hollow. Not scattered.",
        next: null,
      },
    },
  },

  // ---- Q4: Tribute Day ----
  tribute: {
    start: "root",
    nodes: {
      root: {
        speaker: "",
        condition: (s) => !s.flags.tributeDone,
        text: "Five Solmeran soldiers stand at the gate, banners limp in the still air. Their captain steps forward, unhurried, like this is the easiest part of his day.",
        next: "captain_demand",
        else: "already",
      },
      already: { speaker: "", text: "The soldiers have already come and gone.", next: null },
      captain_demand: {
        speaker: "Solmeran Captain",
        text: "Veth Hollow's tribute. Grain, timber, whatever you're calling coin these days. Now.",
        next: "tobin_offer",
      },
      tobin_offer: {
        speaker: "Tobin Holt",
        text: "It's -- it's what we could spare this season, Captain. The soil's given us little enough as it is.",
        next: "captain_potatoes",
      },
      captain_potatoes: {
        speaker: "",
        text: "Tobin holds out a thin, half-full sack of withered potatoes. The captain takes it by two fingers, weighs it, and lets his disgust show plainly before shoving it at a soldier behind him.",
        next: "captain_logs",
      },
      captain_logs: {
        speaker: "Solmeran Captain",
        effect: (s) => { s.flags.logsGone = true; },
        text: "That, and the wood.|The soldiers strip the wagon log by log, until the bed sits bare and splintered.",
        next: "captain_soldiers",
      },
      captain_soldiers: {
        speaker: "Solmeran Captain",
        text: "One more matter. The mountain war has thinned our ranks. Effective today, Veth Hollow provides two able bodies for the eastern front.",
        next: "alden_refuse",
      },
      alden_refuse: {
        speaker: "King Alden Vethar",
        text: "No. You have the tribute you came for. These are my people, not Solmere's to spend.",
        next: "captain_kill",
      },
      captain_kill: {
        speaker: "",
        effect: (s) => { s.flags.kingDead = true; },
        text: "The captain doesn't argue. He doesn't even look angry.|It happens in a single, almost bored motion. King Alden Vethar -- the only king Veth Hollow has known in your lifetime -- falls where he stands, in front of everyone he swore to protect.|No one moves. No one breathes. Somewhere behind you, Wren has started to cry.",
        next: "captain_ask",
      },
      captain_ask: {
        speaker: "Solmeran Captain",
        text: "Two able bodies. That hasn't changed. Who are the knights?",
        next: "volunteer_choice",
      },
      volunteer_choice: {
        speaker: "",
        text: "Joran is already moving before you've finished deciding, jaw set, refusing to look at what's left in the square.",
        choices: [
          {
            label: "Step forward with him, at the same time.",
            next: "volunteer_together",
            effect: (s) => { s.flags.volunteered = "immediate"; },
          },
          {
            label: "Hesitate -- let Joran go first.",
            next: "volunteer_hesitate",
            effect: (s) => { s.flags.volunteered = "hesitant"; },
          },
        ],
      },
      volunteer_together: {
        speaker: "Joran Holt",
        text: "...Together, then. Didn't figure you'd make me ask twice.",
        next: "marrow_insists",
      },
      volunteer_hesitate: {
        speaker: "Joran Holt",
        text: "I've got this. Stay with the others.",
        next: "dain_follows",
      },
      dain_follows: {
        speaker: "",
        text: "A breath later, you step forward anyway. Joran doesn't look surprised.",
        next: "marrow_insists",
      },
      marrow_insists: {
        speaker: "Marrow Fenn",
        text: "Then I'm coming too. Someone ought to keep both of these two alive.",
        next: "captain_laugh",
      },
      captain_laugh: {
        speaker: "Solmeran Captain",
        effect: (s) => { s.flags.tributeDone = true; s.flags.act1PartyKnown = true; },
        text: "The soldiers laugh, but no one refuses her. One more mouth on the road changes nothing to them.|Move out. The gate opens at dusk, whether the Hollow is ready or not.",
        next: null,
      },
    },
  },

  // ---- Q5: Through the Gate -- the first fight ----
  gate_wyrmling: {
    start: "root",
    nodes: {
      root: {
        speaker: "",
        text: "The gate falls shut behind you with a sound like a verdict. Ahead, the tree line is dark and close.",
        next: "marrow_warn",
      },
      marrow_warn: {
        speaker: "Marrow Fenn",
        text: "Something's moving out there. Keep your knife up.",
        next: "break",
      },
      break: {
        speaker: "",
        text: "A wyrmling breaks from the tree line, low and fast, scales the grey-green of old bark.",
        next: "marrow_coach",
      },
      marrow_coach: {
        speaker: "Marrow Fenn",
        text: "WASD or the arrows to move. Space to swing that knife. Hold a direction and tap Q to dodge if it lunges -- it's on a cooldown, so don't waste it.|Go on, {name}. Show me Garrick taught you something.",
        next: null,
      },
    },
  },
};
