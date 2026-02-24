"""Elo rating logic — operates on NameCombo rows."""

from database.db import get_session, get_setting
from database.models import NameCombo, Match


def _k(match_count: int) -> float:
    threshold = int(get_setting("k_stable_threshold") or 20)
    k_default = float(get_setting("k_factor_default") or 32)
    k_stable = float(get_setting("k_factor_stable") or 16)
    return k_stable if match_count >= threshold else k_default


def expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def update_elo(profile_id: int, winner_combo_id: int, loser_combo_id: int):
    """Apply Elo update for a completed match and record it."""
    with get_session() as s:
        w = s.get(NameCombo, winner_combo_id)
        l = s.get(NameCombo, loser_combo_id)  # noqa: E741

        if not w or not l:
            return

        ea = expected(w.elo_score, l.elo_score)
        eb = expected(l.elo_score, w.elo_score)

        kw = _k(w.match_count)
        kl = _k(l.match_count)

        w.elo_score += kw * (1.0 - ea)
        l.elo_score += kl * (0.0 - eb)
        w.match_count += 1
        l.match_count += 1

        s.add(
            Match(
                profile_id=profile_id,
                winner_combo_id=winner_combo_id,
                loser_combo_id=loser_combo_id,
                was_skip=False,
            )
        )
        s.commit()


def record_skip(profile_id: int, combo_a_id: int, combo_b_id: int):
    """Record a skip — nudge match_count down so combos stay in rotation."""
    with get_session() as s:
        for cid in (combo_a_id, combo_b_id):
            combo = s.get(NameCombo, cid)
            if combo:
                combo.match_count = max(0, combo.match_count - 1)

        s.add(
            Match(
                profile_id=profile_id,
                winner_combo_id=None,
                loser_combo_id=None,
                was_skip=True,
            )
        )
        s.commit()
