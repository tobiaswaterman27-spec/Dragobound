// Dialogue trees for Act 1. Each node: { speaker, text (pages separated by "|"),
// choices: [{label, next, effect, condition}], next, condition, effect, else }
// `state` is the live save-state object (state.flags holds story flags).

export const DIALOGUES = {
  joran_intro: {
    start: "root",
    nodes: {
      root: {
        speaker: "Joran Holt",
        text: "Still can't sleep either, huh?|Feels wrong, doesn't it. Same ruins we grew up in. Same eleven doors.|My mother says a wyrmling's been sniffing around the east wall again. Probably worth a look before it gets bold.",
        next: "hub",
      },
      hub: {
        speaker: "Joran Holt",
        text: "Anything else?",
        choices: [
          { label: "How's your family holding up?", next: "family" },
          { label: "Do you ever think about what's past the Greywood?", next: "greywood" },
          { label: "I should go.", next: null },
        ],
      },
      family: {
        speaker: "Joran Holt",
        text: "Ma and Pa don't complain. Wren does enough of that for all of us.|Small mercy is we've still got each other. Not everyone here can say that.",
        next: "hub",
      },
      greywood: {
        speaker: "Joran Holt",
        text: "Sometimes. Then I remember what lives in it, and I stop.|Marrow says even the small dragons that pass through are older than this whole village. Doesn't exactly make we want to go looking.",
        next: "hub",
      },
    },
  },

  joran_after_q1: {
    start: "root",
    nodes: {
      root: {
        speaker: "Joran Holt",
        text: "Good work back there. You didn't hesitate.|Wish I could say the same the first time I saw one of those things up close.",
        next: null,
      },
    },
  },

  sela: {
    start: "root",
    nodes: {
      root: {
        speaker: "Sela Vane",
        text: "Come to check on the widow, have you? You're kind, for a soon-to-be knight.|Careful out there. The Greywood doesn't care how brave you are.",
        choices: [
          { label: "How did you lose your arm?", next: "arm" },
          { label: "Do you have any family besides yourself?", next: "family" },
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
        text: "...",
        next: "family2",
      },
      family2: {
        speaker: "Sela Vane",
        text: "No. Not anymore.|Go on, now. Alden will want you at the council.",
        next: null,
      },
    },
  },

  tobin: {
    start: "root",
    nodes: {
      root: {
        speaker: "Tobin Holt",
        text: "The potatoes are smaller every year. Soil's tired, same as the rest of us.|But we feed the Hollow before we feed ourselves. Always have.",
        next: null,
      },
    },
  },

  yssa: {
    start: "root",
    nodes: {
      root: {
        speaker: "Yssa Holt",
        text: "Don't mind Tobin, he tells that potato story to everyone.|You watch out for our boy out there. He puts on a brave face, but he's scared same as anyone.",
        next: null,
      },
    },
  },

  wren: {
    start: "root",
    nodes: {
      root: {
        speaker: "Wren Holt",
        text: "You're going with Joran when the soldiers come, aren't you.|Tell him... tell him to come back. He always says he will. Make him mean it this time.",
        next: null,
      },
    },
  },

  garrick: {
    start: "root",
    nodes: {
      root: {
        speaker: "Garrick Ashwood",
        text: "Figured you'd come by before you left. Here.",
        next: "give_knife",
      },
      give_knife: {
        speaker: "Garrick Ashwood",
        condition: (s) => !s.flags.knifeReceived,
        effect: (s) => { s.flags.knifeReceived = true; },
        text: "Old hunting knife. Not much, but it's got a good edge and it's never once let me down in the Greywood.|Bring it home in one piece. Don't much care about the knife.",
        next: null,
      },
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
        text: "Garrick would give away his own boots if you asked twice.|Pell hasn't stopped talking about you since he heard you volunteered. Go easy on him, he's young enough to still think this is exciting.",
        next: null,
      },
    },
  },

  pell: {
    start: "root",
    nodes: {
      root: {
        speaker: "Pell Ashwood",
        text: "I saw the wyrmling first, you know. Before anyone. I shouted loud enough Ma heard me from inside.|Someday I'm going to fight one of those things myself. A big one.",
        choices: [
          { label: "Maybe someday.", next: "maybe" },
          { label: "Stay safe, Pell.", next: "safe" },
        ],
      },
      maybe: { speaker: "Pell Ashwood", text: "You'll see! I mean it!", next: null },
      safe: { speaker: "Pell Ashwood", text: "...Yeah. Okay.", next: null },
    },
  },

  diary: {
    start: "root",
    nodes: {
      root: {
        speaker: "Weathered Diary",
        condition: (s) => !s.flags.diaryFound,
        effect: (s) => { s.flags.diaryFound = true; },
        text: "Tucked under a loose stone, forgotten by everyone but you. The leather cover has gone soft with age.|The early pages are just a household ledger -- grain counts, a bad winter, a cough that wouldn't quit.|Near the end, the handwriting changes. Smaller. Faster.|\"...if you're old enough to read this, I'm sorry I couldn't stay to explain it myself. Alden will look after you. He's a better man than this crown ever deserved. Be good. Be brave. I love you more than the Hollow itself.\"|You sit with that a while before you put it back.",
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

  king_locked: {
    start: "root",
    nodes: {
      root: {
        speaker: "King Alden Vethar",
        condition: (s) => !s.flags.q1Done,
        text: "Not yet, {name}. That wyrmling won't wait for a council meeting.|See to the east wall first. Joran should be close by.",
        next: null,
      },
    },
  },

  king_council: {
    start: "root",
    nodes: {
      root: {
        speaker: "King Alden Vethar",
        condition: (s) => s.flags.q1Done && !s.flags.q2Done,
        text: "There you are. Good -- Marrow, come sit, both of you.|Solmere's collectors are due within the week. I mean to have words with their commander this time, about the tribute weighing more each season while we have less to give.",
        next: "marrow_join",
      },
      marrow_join: {
        speaker: "Marrow Fenn",
        text: "Words won't move Solmere, Alden. They never have.|Still. Better to ask than to simply hand over what little we have left.",
        next: "choices_hub",
      },
      choices_hub: {
        speaker: "King Alden Vethar",
        text: "Ask what you like. I owe you both honesty, at least.",
        choices: [
          { label: "Why does Solmere even bother with us? We have nothing.", next: "why_bother" },
          { label: "Is it true the Hollow was never truly conquered?", next: "prophecy" },
          { label: "What happened to my parents?", next: "parents" },
          { label: "I'm ready.", next: "end", effect: (s) => { s.flags.q2Done = true; } },
        ],
      },
      why_bother: {
        speaker: "Marrow Fenn",
        text: "Because 'nothing' still grows grain and cuts timber. And because a beaten people who still remember being free are a habit Solmere would rather break than risk.",
        next: "choices_hub",
      },
      prophecy: {
        speaker: "King Alden Vethar",
        text: "There's an old word for it, older than the war. I won't pretend to understand all of it.|Only that Solmere never formally annexed us. Never renamed the Hollow, never resettled it. For a hundred years of conquest, that's... odd. Marrow's studied it longer than I have.",
        next: "marrow_prophecy",
      },
      marrow_prophecy: {
        speaker: "Marrow Fenn",
        text: "Odd is a kind word for it. I have my theories. None I'd stake a life on yet.|Ask me again when I have more than theories.",
        next: "choices_hub",
      },
      parents: {
        speaker: "King Alden Vethar",
        text: "You know the shape of it as well as I do. A bad winter took more than crops that year.|I made you a promise the day I took you in, and I mean to keep it as long as I'm able. That's all the answer I have.",
        next: "choices_hub",
      },
      end: {
        speaker: "King Alden Vethar",
        text: "Go on, both of you. Rest while you still can.",
        next: null,
      },
    },
  },

  king_tribute: {
    start: "root",
    nodes: {
      root: {
        speaker: "",
        condition: (s) => s.flags.q2Done && !s.flags.q3Done,
        text: "Horns, out past the east wall. Not the wyrmling this time.|Solmeran banners crest the ridge -- more soldiers than Veth Hollow has seen in a decade, marching in tight formation toward the square.",
        next: "commander",
      },
      commander: {
        speaker: "Solmeran Officer",
        text: "By order of the Crown, Veth Hollow's tribute is reassessed. Effective immediately, this settlement provides two able bodies for the eastern campaign.|King Alden. Step forward.",
        next: "alden_step",
      },
      alden_step: {
        speaker: "King Alden Vethar",
        text: "Take it from me and no one else. These people have given Solmere everything already.",
        next: "commander2",
      },
      commander2: {
        speaker: "Solmeran Officer",
        text: "That isn't how tribute works, old man.",
        next: "strike",
      },
      strike: {
        speaker: "",
        text: "It happens too fast to stop. A single motion, almost bored.|King Alden Vethar, the last king Veth Hollow will ever crown, falls in the square he ruled over for thirty years -- in front of everyone he swore to protect.",
        next: "silence",
      },
      silence: {
        speaker: "",
        effect: (s) => { s.flags.kingDead = true; },
        text: "No one moves. No one breathes. Somewhere behind you, Wren starts to cry.",
        next: "officer_demand",
      },
      officer_demand: {
        speaker: "Solmeran Officer",
        text: "Two able bodies. That requirement hasn't changed. Volunteer, or I start choosing for you -- and I promise you won't like my taste.",
        next: "volunteer_choice",
      },
      volunteer_choice: {
        speaker: "",
        text: "Joran is already moving, jaw set, refusing to look at what's left in the square.|The officer's eyes drift over the crowd, unhurried, daring someone else to step forward first.",
        choices: [
          {
            label: "Step forward immediately.",
            next: "volunteer_yes",
            effect: (s) => { s.flags.volunteered = "immediate"; },
          },
          {
            label: "Hesitate. Let Joran go alone if no one else moves.",
            next: "volunteer_hesitate",
            effect: (s) => { s.flags.volunteered = "hesitant"; },
          },
        ],
      },
      volunteer_yes: {
        speaker: "Joran Holt",
        text: "...Yeah. Together, then.|Didn't figure you'd make me ask twice.",
        next: "aftermath",
      },
      volunteer_hesitate: {
        speaker: "Joran Holt",
        text: "I've got this. Stay with the others.|...Fine. Change your mind fast, if you're changing it at all.",
        next: "aftermath",
      },
      aftermath: {
        speaker: "",
        effect: (s) => { s.flags.q3Done = true; s.flags.act1Complete = true; },
        text: "By dusk, Veth Hollow has a new knight -- or two -- and one fewer king.|The soldiers make camp in the square as if it belongs to them now. Perhaps, in every way that matters, it already did.|-- END OF ACT 1 (DEMO) --|Explore the Hollow while you can. The road to the Greywood, and everything past it, comes next.",
        next: null,
      },
    },
  },
};
