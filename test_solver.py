"""Step 3 tests: the solver meets targets, maximizes the objective, and stays legal."""
from solver import solve
from stats import validate_build


CTX = dict(transcend=6, atk_lvl=30, ring=6)


def test_pure_max_matches_known_optimum():
    # no targets, ATK-priority -> must equal the sheet/Excel optimum for Vanessa
    r = solve("Vanessa", "Assassin", priority=["ATK", "CDM"], **CTX)
    assert r.stats["ATK"] == 6848


def test_result_build_is_always_legal():
    r = solve("Vanessa", "Assassin", targets={"CR": 71, "WK": 25}, priority=["ATK"], **CTX)
    assert validate_build(r.build) == []


def test_feasible_targets_are_met():
    r = solve("Vanessa", "Assassin",
              targets={"CR": 71, "WK": 25, "SPD": 29}, priority=["ATK", "CDM"], **CTX)
    assert r.targets_met
    assert r.stats["CR"] >= 71
    assert r.stats["WK"] >= 25
    assert r.stats["SPD"] >= 29


def test_base_already_met_target_uses_no_slots():
    r = solve("Vanessa", "Assassin", targets={"SPD": 29}, priority=["ATK"], **CTX)
    assert any("SPD" in line and "ไม่ต้องใช้ช่อง" in line for line in r.reasoning)


def test_infeasible_target_reports_failure():
    r = solve("Vanessa", "Assassin", targets={"CR": 999}, priority=["ATK"], **CTX)
    assert r.targets_met is False
    assert any("ไม่พอ" in line for line in r.reasoning)


def test_targets_cost_objective():
    # spending slots on targets should not raise ATK above the unconstrained max
    free = solve("Vanessa", "Assassin", priority=["ATK", "CDM"], **CTX)
    constrained = solve("Vanessa", "Assassin",
                        targets={"CR": 71, "WK": 25}, priority=["ATK", "CDM"], **CTX)
    assert constrained.stats["ATK"] <= free.stats["ATK"]


def test_priority_is_respected():
    atk_first = solve("Vanessa", "Assassin", priority=["ATK"], **CTX)
    hp_first = solve("Vanessa", "Assassin", priority=["HP"], **CTX)
    assert atk_first.stats["ATK"] > hp_first.stats["ATK"]
    assert hp_first.stats["HP"] > atk_first.stats["HP"]
