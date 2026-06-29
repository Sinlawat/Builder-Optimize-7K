"""Step 4 tests: Top-N alternatives and CLI."""
from solver import top_builds, _build_sig
from cli import _parse_targets, main as cli_main

CTX = dict(transcend=6, atk_lvl=30, ring=6)


def test_top_builds_returns_distinct_and_capped():
    builds = top_builds("Vanessa", "Assassin", targets={"CR": 71, "WK": 25},
                        priority=["ATK", "CDM"], n=3, **CTX)
    assert 1 <= len(builds) <= 3
    sigs = {_build_sig(b.build) for b in builds}
    assert len(sigs) == len(builds)          # all distinct


def test_top_builds_all_meet_feasible_targets():
    builds = top_builds("Vanessa", "Assassin", targets={"CR": 71, "WK": 25},
                        priority=["ATK"], n=5, **CTX)
    assert all(b.targets_met for b in builds)


def test_top_builds_ranked_by_objective():
    builds = top_builds("Vanessa", "Assassin", targets={"CR": 71},
                        priority=["ATK", "CDM"], n=5, **CTX)
    atks = [b.stats["ATK"] for b in builds]
    assert atks == sorted(atks, reverse=True)


def test_parse_targets():
    assert _parse_targets(["CR=71", "SPD=29"]) == {"CR": 71, "SPD": 29}


def test_cli_runs(capsys):
    cli_main(["Vanessa", "--set", "Assassin", "--target", "CR=71",
              "--priority", "ATK", "CDM", "--transcend", "6", "--atk-lvl", "30", "--top", "2"])
    out = capsys.readouterr().out
    assert "Hero: Vanessa" in out
    assert "#1" in out
