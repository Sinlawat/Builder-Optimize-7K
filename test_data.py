"""Step 1 tests: data layer and constants are well-formed."""
import constants as C
from data import load_heroes, get_hero


def test_heroes_load():
    heroes = load_heroes()
    assert len(heroes) > 100
    assert "Vanessa" in heroes


def test_vanessa_stats():
    v = get_hero("Vanessa")
    assert v.atk == 1500
    assert v.grade == "LEGEND"
    assert v.star_main == "ATK"
    assert v.star4 == "EFF"


def test_get_hero_missing_raises():
    try:
        get_hero("Nobody")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


def test_every_option_has_a_target():
    # every substat and every main option must map to a known stat code
    for opt in set(C.SUBSTAT_TYPES) | set(C.MAIN_VALUE_OFFENSE) | set(C.MAIN_VALUE_DEFENSE):
        assert opt in C.OPTION_TARGET, opt
        assert C.OPTION_TARGET[opt] in C.STATS


def test_transcend_tables_have_13_levels():
    for name, table in C.TRANSCEND.items():
        assert len(table) == 13, name  # Q2 = 0..12


def test_percent_types_are_known_options():
    for p in C.PERCENT_TYPES:
        assert p in C.OPTION_TARGET
