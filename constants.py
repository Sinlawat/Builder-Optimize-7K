"""All game constants reverse-engineered from the SKRE Build Maker (BETA.4).

Stat codes used throughout the project:
    ATK DEF HP SPD CR CDM WK BLK RED EHR ERes
"""

# Canonical stat codes (order matters for display / lexicographic tiers)
STATS = ["ATK", "DEF", "HP", "SPD", "CR", "CDM", "WK", "BLK", "RED", "EHR", "ERes"]

# Flat base contributed by equipment regardless of choices (from 304*2 etc.)
EQUIP_FLAT_BASE = {"ATK": 608, "DEF": 378, "HP": 2158}

# Innate base stats not coming from the hero table
INNATE_BASE = {"CR": 5, "CDM": 150}

# Stats expressed as a percent of the hero base stat (scale off X3/X4/X5)
PERCENT_TYPES = {"Attack %", "Defense %", "HP %"}

# Equipment option -> which final stat it feeds
OPTION_TARGET = {
    "Attack %": "ATK", "Attack Flat": "ATK",
    "Defense %": "DEF", "Defense Flat": "DEF",
    "HP %": "HP", "HP Flat": "HP",
    "Speed": "SPD",
    "Crit Rate": "CR", "Crit Damage": "CDM",
    "Weakness Hit Chance": "WK", "Block Rate": "BLK",
    "Effect Hit Rate": "EHR", "Effect Resistance": "ERes",
    "Damage Taken Reduction": "RED",
}

# Substat base value; final value = base * (rolls + 1). None = not a valid substat.
SUBSTAT_BASE = {
    "Attack %": 5, "Attack Flat": 50,
    "Defense %": 5, "Defense Flat": 30,
    "HP %": 5, "HP Flat": 180,
    "Speed": 4,
    "Crit Rate": 4, "Crit Damage": 6,
    "Weakness Hit Chance": 5, "Block Rate": 4,
    "Effect Hit Rate": 5, "Effect Resistance": 5,
}
SUBSTAT_TYPES = list(SUBSTAT_BASE.keys())

# Max main-stat value. Two pools: offense piece (left) and defense piece (right).
MAIN_VALUE_OFFENSE = {
    "Attack %": 28, "Attack Flat": 240, "Defense %": 28, "Defense Flat": 160,
    "HP %": 28, "HP Flat": 850, "Crit Rate": 24, "Crit Damage": 36,
    "Weakness Hit Chance": 28, "Effect Hit Rate": 30,
}
MAIN_VALUE_DEFENSE = {
    "Attack %": 28, "Attack Flat": 240, "Defense %": 28, "Defense Flat": 160,
    "HP %": 28, "HP Flat": 850, "Block Rate": 24,
    "Damage Taken Reduction": 16, "Effect Resistance": 30,
}

# Rolls budget per piece (distribute among the 4 substats)
ROLLS_PER_PIECE = 5
SUBSTATS_PER_PIECE = 4
PIECES = {"offense": 2, "defense": 2}  # 2 offense + 2 defense = 4 pieces

# Transcend % tables indexed by transcend level Q2 (0..12)
TRANSCEND = {
    "legend_main": [0, 12, 18, 18, 18, 30, 36, 38, 40, 42, 44, 46, 48],
    "nonmain":     [0, 0, 0, 0, 0, 0, 0, 2, 4, 6, 8, 10, 12],
    "rare_main":   [0, 9, 13.5, 13.5, 13.5, 22.5, 27, 29, 31, 33, 35, 37, 39],
    "legend_hp":   [0, 0, 0, 18, 18, 18, 18, 20, 22, 24, 26, 28, 30],
    "rare_hp":     [0, 0, 0, 14, 14, 14, 14, 16, 18, 20, 22, 24, 36],
}

# Flat transcend bonus to rate stats, granted only when Q2>=4 and star4 matches.
TRANSCEND_FLAT = {"CR": 18, "CDM": 24, "WK": 20, "BLK": 18, "RED": 10, "EFF": 24}
# star4 code -> stat code it boosts
STAR4_TO_STAT = {"CR": "CR", "CDM": "CDM", "WK": "WK", "BLK": "BLK", "RED": "RED", "EFF": "EHR"}
TRANSCEND_FLAT_LEVEL = 4  # requires Q2 >= 4

# Awakening level bonuses (flat)
LEVEL_BONUS = {
    "ATK": {0: 0, 10: 100, 20: 220, 30: 370},
    "DEF": {0: 0, 10: 70, 20: 150, 30: 250},
    "HP":  {0: 0, 10: 320, 20: 680, 30: 1130},
}

# Ring: percent of base ATK/DEF/HP by ring star
RING_PERCENT = {4: 5, 5: 7, 6: 10}

# Set bonuses. Each entry: stat -> (four_piece, two_piece).
# Percent sets (Vanguard/Guardian/Paladin) apply as % of the hero base stat.
SET_BONUS = {
    "Vanguard":       {"ATK_pct": (45, 20), "EHR": (20, 0)},
    "Guardian":       {"DEF_pct": (45, 20), "ERes": (20, 0)},
    "Paladin":        {"HP_pct": (40, 17)},
    "Assassin":       {"CR": (30, 15)},
    "Bounty Tracker": {"WK": (35, 15)},
    "Gatekeeper":     {"BLK": (30, 15)},
    "Spellweaver":    {"EHR": (35, 17)},
    "Orchestrator":   {"ERes": (35, 17)},
    "Avenger":        {},  # 4pc damage effect only, no flat stat
}
SET_NAMES = list(SET_BONUS.keys())

# 4-piece special effect text (display only)
SET_EFFECT_4PC = {
    "Paladin": "Income Healing Boots 20%",
    "Gatekeeper": "Block Damage Reduction 10%",
    "Avenger": "Damage Dealt 30% + Boss Damage 40%",
    "Assassin": "Ignore Defense 15%",
    "Bounty Tracker": "Weakness Hit Damage 35%",
    "Spellweaver": "Effect Probability 10%",
    "Orchestrator": "CC Immunity 1 turn",
}
