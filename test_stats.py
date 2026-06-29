"""Step 2 tests: the stat engine must reproduce the sheet's numbers exactly."""
import constants as C
from stats import Build, Piece, compute_stats, validate_build


def _vanessa_optimal_build():
    """The build the Excel optimizer produced for Vanessa (Assassin, T6, DPS).

    Offense/defense mains = Attack %, substats = Attack % (5 rolls) + 3 zero-roll subs,
    all 4 pieces identical.
    """
    subs = [("Attack %", 5), ("Attack Flat", 0), ("Crit Rate", 0), ("Weakness Hit Chance", 0)]
    pieces = [
        Piece("offense", "Attack %", subs),
        Piece("offense", "Attack %", subs),
        Piece("defense", "Attack %", subs),
        Piece("defense", "Attack %", subs),
    ]
    return Build(hero="Vanessa", set_name="Assassin", pieces=pieces,
                 transcend=6, atk_lvl=30, def_lvl=0, hp_lvl=0, ring=6)


def test_vanessa_matches_sheet():
    s = compute_stats(_vanessa_optimal_build())
    assert s["ATK"] == 6848
    assert s["DEF"] == 1006
    assert s["HP"] == 6414
    assert s["SPD"] == 29
    assert s["CR"] == 51          # 5 base + 30 Assassin + 16 substat
    assert s["CDM"] == 150
    assert s["WK"] == 20          # 4 pieces x Weakness sub (5 each)
    assert s["EHR"] == 24         # transcend EFF flat (Q2>=4, star4=EFF)
    assert s["BLK"] == 0
    assert s["RED"] == 0
    assert s["ERes"] == 0


def test_transcend_off_removes_bonus():
    b = _vanessa_optimal_build()
    b.transcend = 0
    s = compute_stats(b)
    # no transcend ATK bonus, no EFF flat
    assert s["EHR"] == 0
    assert s["ATK"] < 6848


def test_set_swap_changes_only_set_stat():
    base = compute_stats(_vanessa_optimal_build())
    b = _vanessa_optimal_build()
    b.set_name = "Bounty Tracker"          # WK set instead of Assassin CR set
    swapped = compute_stats(b)
    assert swapped["CR"] == base["CR"] - 30        # lost Assassin +30 CR
    assert swapped["WK"] == base["WK"] + 35        # gained Bounty Tracker +35 WK


def test_percent_substat_scales_with_hero_base():
    # Attack % substat should add hero.atk * value/100, not a flat number
    subs = [("Attack %", 5)]
    p = Piece("offense", "Crit Rate", subs)   # main irrelevant to ATK
    b = Build("Vanessa", "Avenger", [p], transcend=0, ring=4)
    s = compute_stats(b)
    # Attack% value = 5*(5+1)=30  -> 1500*30/100 = 450 added to ATK
    bare = compute_stats(Build("Vanessa", "Avenger",
                               [Piece("offense", "Crit Rate", [])], transcend=0, ring=4))
    assert s["ATK"] - bare["ATK"] == 450


def test_validate_catches_duplicates_and_overrolls():
    bad = Build("Vanessa", "Assassin",
                [Piece("offense", "Attack %", [("Crit Rate", 3), ("Crit Rate", 3)])])
    errs = validate_build(bad)
    assert any("duplicate" in e for e in errs)
    assert any("rolls exceed" in e for e in errs)


def test_validate_passes_clean_build():
    assert validate_build(_vanessa_optimal_build()) == []
