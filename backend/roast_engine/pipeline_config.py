from typing import Dict, Any

ROAST_INTENSITY: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Playful",
        "aggression": 2,
        "profanity": 0,
        "exaggeration": 3,
        "sarcasm": 3,
        "punchline_impact": 4,
        "description": "Friendly teasing, clever observations, light-hearted jabs.",
        "tone_directive": "Keep it playful, witty, and lighthearted. No harsh profanity.",
    },
    2: {
        "name": "Spicy",
        "aggression": 4,
        "profanity": 2,
        "exaggeration": 5,
        "sarcasm": 5,
        "punchline_impact": 6,
        "description": "Sharper comparisons, noticeable sarcasm, moderate exaggeration.",
        "tone_directive": "Turn up the sarcasm and bite. Mild adult humor allowed.",
    },
    3: {
        "name": "Savage",
        "aggression": 6,
        "profanity": 5,
        "exaggeration": 7,
        "sarcasm": 7,
        "punchline_impact": 8,
        "description": "Aggressive comedic delivery, strong punchlines, confident roasting.",
        "tone_directive": "Uncensored 21+ club roast energy. Sharp, ruthless, hilarious.",
    },
    4: {
        "name": "Brutal",
        "aggression": 8,
        "profanity": 7,
        "exaggeration": 9,
        "sarcasm": 9,
        "punchline_impact": 9,
        "description": "High-impact insults, elaborate exaggerations, heavy sarcasm & wordplay.",
        "tone_directive": "No-holds-barred 21+ Comedy Central Roast level. Creative profanity and devastating punchlines.",
    },
    5: {
        "name": "Nuclear",
        "aggression": 10,
        "profanity": 10,
        "exaggeration": 10,
        "sarcasm": 10,
        "punchline_impact": 10,
        "description": "Maximum comedic intensity, rapid-fire punchlines, relentless escalation.",
        "tone_directive": "Absolute scorched-earth 21+ uncensored adult comedy. Maximum shock value, absurd escalation, lethal closers, zero generic filler.",
    },
}

COMEDY_STYLES: Dict[str, Dict[str, str]] = {
    "roast_battle": {
        "name": "Roast Battle",
        "description": "Direct insults, rapid-fire attacks, devastating closing lines.",
        "directive": "Write like a ruthless Roast Battle champion: direct, punchy, aggressive setups with lethal 1-2 punchlines.",
    },
    "stand_up": {
        "name": "Stand-Up Comedian",
        "description": "Setup, misdirection, escalating story, unexpected punchline.",
        "directive": "Write like a headlining stand-up comic: conversational rhythm, clever misdirection, escalating absurdity, and a killer tag.",
    },
    "dark_comedy": {
        "name": "Dark Comedy",
        "description": "Dramatic irony, absurdity, theatrical exaggeration.",
        "directive": "Lean into dark, twisted, absurd fictional scenarios and dramatic irony. Unapologetically bleak and hilarious.",
    },
    "rap_battle": {
        "name": "Rap Battle Writer",
        "description": "Internal rhymes, multisyllabic rhymes, wordplay, double meanings.",
        "directive": "Write with internal rhymes, multisyllabic schemes, double entendres, and mic-drop bar structure.",
    },
    "satirical": {
        "name": "Satirical Commentator",
        "description": "Ridiculous observations, mock-serious reporting, exaggerated analysis.",
        "directive": "Deliver deadpan, mock-serious investigative commentary treating their outfit/vibe like a national crisis.",
    },
    "documentary": {
        "name": "Documentary Narrator",
        "description": "Deadpan delivery, mock investigation, increasingly absurd conclusions.",
        "directive": "Narrate like a cynical nature/crime documentary observing a fascinatingly flawed specimen in the wild.",
    },
    "sarcastic": {
        "name": "Sarcastic Commentator",
        "description": "Sharp observations, dismissive wit, clever comparisons.",
        "directive": "Dripping with condescending wit, surgical sarcasm, and effortlessly dismissive comparisons.",
    },
    "blend": {
        "name": "Writers' Room Blend",
        "description": "40% Roast Battle + 30% Dark Comedy + 30% Stand-Up.",
        "directive": "Blend 40% Roast Battle aggression, 30% Dark Comedy absurdity, and 30% Stand-Up misdirection for maximum variety.",
    },
}
