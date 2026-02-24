"""Matchmaking logic — pick a pair of NameCombos to battle."""

import random
import statistics
from database.db import get_session, get_setting
from database.models import NameCombo, Name, Gender


def _spread(scores: list[float]) -> float:
    return statistics.stdev(scores) if len(scores) >= 2 else 0.0


def _gender_ids(gender_mode: str) -> list[Gender]:
    """
    Return the Gender values eligible for the given mode.
    'M' -> masculine + neutral
    'F' -> feminine + neutral
    """
    if gender_mode == "M":
        return [Gender.M, Gender.N]
    elif gender_mode == "F":
        return [Gender.F, Gender.N]
    return [Gender.M, Gender.F, Gender.N]


def pick_combo_pair(profile_id: int, gender_mode: str) -> tuple[int, int] | None:
    """
    Return (combo_id_a, combo_id_b) for the next match.
    Filters combos so both first and middle names match the gender mode.
    Returns None if fewer than 2 eligible combos exist.
    """
    eligible_genders = _gender_ids(gender_mode)

    with get_session() as s:
        # Get all names eligible for this gender mode
        eligible_name_ids = set(
            n.id for n in s.query(Name).filter(Name.gender.in_(eligible_genders)).all()
        )

        # Get combos for this profile where BOTH names are eligible
        combos = (
            s.query(NameCombo)
            .filter(
                NameCombo.profile_id == profile_id,
                NameCombo.first_id.in_(eligible_name_ids),
                NameCombo.middle_id.in_(eligible_name_ids),
            )
            .all()
        )

    if len(combos) < 2:
        return None

    scores = [c.elo_score for c in combos]
    spread = _spread(scores)
    thresh = float(get_setting("elo_spread_thresh") or 50)
    rand_pct = int(get_setting("match_random_pct") or 30) / 100.0

    if spread < thresh:
        a, b = random.sample(combos, 2)
        return a.id, b.id

    use_random = random.random() < rand_pct
    if use_random:
        a, b = random.sample(combos, 2)
        return a.id, b.id
    else:
        return _close_pair(combos)


def _close_pair(combos: list[NameCombo]) -> tuple[int, int]:
    """Pick an underplayed combo, then find its closest Elo neighbor."""
    sorted_combos = sorted(combos, key=lambda c: c.elo_score)
    weights = [1.0 / (c.match_count + 1) for c in sorted_combos]
    anchor = random.choices(sorted_combos, weights=weights, k=1)[0]
    idx = sorted_combos.index(anchor)

    candidates = []
    if idx > 0:
        candidates.append(sorted_combos[idx - 1])
    if idx < len(sorted_combos) - 1:
        candidates.append(sorted_combos[idx + 1])

    opponent = random.choice(candidates)
    return anchor.id, opponent.id
