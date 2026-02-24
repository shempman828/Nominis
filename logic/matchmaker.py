"""Matchmaking logic — blended close/random pairings."""

import random
import statistics
from database.db import get_session, get_setting
from database.models import ProfileName


def _spread(scores: list[float]) -> float:
    return statistics.stdev(scores) if len(scores) >= 2 else 0.0


def pick_pair(profile_id: int) -> tuple[int, int] | None:
    """
    Return (name_id_a, name_id_b) for the next match.
    Returns None if fewer than 2 names exist for the profile.
    """
    with get_session() as s:
        pns = s.query(ProfileName).filter_by(profile_id=profile_id).all()

    if len(pns) < 2:
        return None

    scores = [p.elo_score for p in pns]
    spread = _spread(scores)
    thresh = float(get_setting("elo_spread_thresh") or 50)
    rand_pct = int(get_setting("match_random_pct") or 30) / 100.0

    # Before the pool has differentiated, pure random is fine
    if spread < thresh:
        a, b = random.sample(pns, 2)
        return a.name_id, b.name_id

    # Blended mode
    use_random = random.random() < rand_pct

    if use_random:
        a, b = random.sample(pns, 2)
        return a.name_id, b.name_id
    else:
        return _close_pair(pns)


def _close_pair(pns: list[ProfileName]) -> tuple[int, int]:
    """Pick a name at random, then find its closest Elo neighbor."""
    sorted_pns = sorted(pns, key=lambda p: p.elo_score)
    # Pick a random anchor, biased slightly toward underplayed names
    weights = [1.0 / (p.match_count + 1) for p in sorted_pns]
    anchor = random.choices(sorted_pns, weights=weights, k=1)[0]
    idx = sorted_pns.index(anchor)

    # Candidate = immediate neighbor (above or below)
    candidates = []
    if idx > 0:
        candidates.append(sorted_pns[idx - 1])
    if idx < len(sorted_pns) - 1:
        candidates.append(sorted_pns[idx + 1])

    opponent = random.choice(candidates)
    return anchor.name_id, opponent.name_id
