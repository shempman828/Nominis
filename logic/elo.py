"""Elo rating logic — operates on NameCombo rows, also updates Name reputation."""

from database.db import get_session, get_setting
from database.models import NameCombo, Name, Match


def _k(match_count: int) -> float:
    threshold = int(get_setting("k_stable_threshold") or 30)
    k_default = float(get_setting("k_factor_default") or 64)
    k_stable = float(get_setting("k_factor_stable") or 32)
    return k_stable if match_count >= threshold else k_default


def expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def _update_streak(combo: NameCombo, won: bool):
    """
    Extend or break the streak (capped ±5).
      Win  after wins   → grow hot streak
      Win  after losses → reset to +1
      Loss after losses → deepen cold streak
      Loss after wins   → reset to -1
    """
    if won:
        combo.streak = max(combo.streak + 1, 1) if combo.streak >= 0 else 1
    else:
        combo.streak = min(combo.streak - 1, -1) if combo.streak <= 0 else -1
    combo.streak = max(-5, min(5, combo.streak))


def _update_name_rep(s, combo: NameCombo, won: bool):
    """Increment slot-agnostic win/loss on both names in a combo."""
    for name_id in (combo.first_id, combo.middle_id):
        name = s.get(Name, name_id)
        if name is None:
            continue
        if won:
            name.rep_wins += 1
        else:
            name.rep_losses += 1


def update_elo(profile_id: int, winner_combo_id: int, loser_combo_id: int):
    """Apply Elo update, update streaks, update name reputations, record match."""
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

        _update_streak(w, won=True)
        _update_streak(l, won=False)

        _update_name_rep(s, w, won=True)
        _update_name_rep(s, l, won=False)

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
    """Record a skip — nudge match_count down, cool streaks slightly."""
    with get_session() as s:
        for cid in (combo_a_id, combo_b_id):
            combo = s.get(NameCombo, cid)
            if combo:
                combo.match_count = max(0, combo.match_count - 1)
                if combo.streak > 0:
                    combo.streak = max(0, combo.streak - 1)
                elif combo.streak < 0:
                    combo.streak = min(0, combo.streak + 1)

        s.add(
            Match(
                profile_id=profile_id,
                winner_combo_id=None,
                loser_combo_id=None,
                was_skip=True,
            )
        )
        s.commit()
