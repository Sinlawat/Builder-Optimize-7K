"""Step 6 tests: the ILP exact solver is correct and dominates greedy.

The most important test is `test_exact_equals_greedy_without_targets`: with no targets
greedy is provably optimal, so if exact disagrees the ILP MODEL has a bug (not greedy).
"""
import pytest

pulp = pytest.importorskip("pulp")

from solver import solve
from optimizer_exact import solve_exact
from stats import validate_build

CTX = dict(transcend=6, atk_lvl=30, ring=6)


def test_exact_equals_greedy_without_targets():
    # model-correctness net: pure maximization has a known optimum (6848)
    e = solve_exact("Vanessa", "Assassin", priority=["ATK", "CDM"], **CTX)
    g = solve("Vanessa", "Assassin", priority=["ATK", "CDM"], **CTX)
    assert e.stats["ATK"] == g.stats["ATK"] == 6848


def test_exact_build_is_legal():
    e = solve_exact("Vanessa", "Assassin",
                    targets={"CR": 71, "WK": 25}, priority=["ATK"], **CTX)
    assert validate_build(e.build) == []


def test_exact_meets_feasible_targets():
    e = solve_exact("Vanessa", "Assassin",
                    targets={"CR": 71, "WK": 25, "SPD": 29}, priority=["ATK", "CDM"], **CTX)
    assert e.targets_met
    assert e.stats["CR"] >= 71 and e.stats["WK"] >= 25 and e.stats["SPD"] >= 29


def test_exact_dominates_greedy_on_conflicting_targets():
    tg = {"CR": 71, "WK": 25, "SPD": 29}
    e = solve_exact("Vanessa", "Assassin", targets=tg, priority=["ATK", "CDM"], **CTX)
    g = solve("Vanessa", "Assassin", targets=tg, priority=["ATK", "CDM"], **CTX)
    assert e.targets_met
    assert e.stats["ATK"] >= g.stats["ATK"]      # exact never worse than greedy


def test_exact_infeasible_reports_failure():
    e = solve_exact("Vanessa", "Assassin", targets={"CR": 999}, priority=["ATK"], **CTX)
    assert e.targets_met is False
    assert validate_build(e.build) == []         # still returns a legal best-effort build


def test_exact_priority_respected():
    a = solve_exact("Vanessa", "Assassin", priority=["ATK"], **CTX)
    hp = solve_exact("Vanessa", "Assassin", priority=["HP"], **CTX)
    assert a.stats["ATK"] > hp.stats["ATK"]
    assert hp.stats["HP"] > a.stats["HP"]
