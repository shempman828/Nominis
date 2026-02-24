"""Elo rating logic."""

from database.db import get_session, get_setting
from database.models import ProfileName, Match


def _k(match_count: int) -> float:
    threshold = int(get_setting("k_stable_threshold") or 20)
    k_default = float(get_setting("k_factor_default") or 32)
    k_stable = float(get_setting("k_factor_stable") or 16)
    return k_stable if match_count >= threshold else k_default


def expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def update_elo(profile_id: int, winner_id: int, loser_id: int):
    """Apply Elo update for a completed match and record it."""
    with get_session() as s:
        w_pn = (
            s.query(ProfileName)
            .filter_by(profile_id=profile_id, name_id=winner_id)
            .first()
        )
        l_pn = (
            s.query(ProfileName)
            .filter_by(profile_id=profile_id, name_id=loser_id)
            .first()
        )

        if not w_pn or not l_pn:
            return

        ea = expected(w_pn.elo_score, l_pn.elo_score)
        eb = expected(l_pn.elo_score, w_pn.elo_score)

        kw = _k(w_pn.match_count)
        kl = _k(l_pn.match_count)

        w_pn.elo_score += kw * (1.0 - ea)
        l_pn.elo_score += kl * (0.0 - eb)
        w_pn.match_count += 1
        l_pn.match_count += 1

        s.add(
            Match(
                profile_id=profile_id,
                winner_id=winner_id,
                loser_id=loser_id,
                was_skip=False,
            )
        )
        s.commit()


def record_skip(profile_id: int, name_a_id: int, name_b_id: int):
    """Record a skip — increment skip counts, no Elo change."""
    with get_session() as s:
        for nid in (name_a_id, name_b_id):
            name = (
                s.query(ProfileName)
                .filter_by(profile_id=profile_id, name_id=nid)
                .first()
            )
            if name:
                # Re-queue: nudge match_count down slightly so they stay active
                name.match_count = max(0, name.match_count - 1)

            from database.models import Name

            nm = s.get(Name, nid)
            if nm:
                nm.skip_count += 1

        s.add(
            Match(profile_id=profile_id, winner_id=None, loser_id=None, was_skip=True)
        )
        s.commit()
