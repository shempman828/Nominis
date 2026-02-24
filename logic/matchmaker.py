"""
Matchmaking — reputation-first, streak-aware combo pairing.

Two-stage selection
───────────────────
Stage 1 — Pick a FEATURED NAME by reputation weight.
  Each name's weight = reputation score (0.2–2.0), which is derived
  from its slot-agnostic win rate across all combos it has appeared in.
  High-rep names get featured more often → their combos get sorted faster.
  Low-rep names stay in rotation at reduced weight (never fully excluded).

Stage 2 — Pick a FEATURED COMBO for that name.
  Among all combos containing the featured name, weight by:
    • Under-played bonus  (new combos need exposure)
    • Hot-streak bonus    (winning combos climb quickly)
    • Cold-streak penalty (losing combos appear less)

Stage 3 — Pick an OPPONENT COMBO.
  The opponent is also chosen reputation-first (same Stage 1 logic for
  the opposing name), then the specific combo is the one most similar
  in Elo to the anchor — keeping matches competitive.
  Hot-streak anchors reach slightly higher in Elo for faster climbing.

Dark horse
──────────
  With probability = match_random_pct, skip all of the above and pick
  two combos at random. Keeps the long tail alive.
"""

import random
import statistics
from database.db import get_session, get_setting
from database.models import NameCombo, Name, Gender


# ── Gender helpers ─────────────────────────────────────────────────────────────


def _gender_enums(gender_mode: str) -> list[Gender]:
    if gender_mode == "M":
        return [Gender.M, Gender.N]
    elif gender_mode == "F":
        return [Gender.F, Gender.N]
    return [Gender.M, Gender.F, Gender.N]


# ── Weight helpers ─────────────────────────────────────────────────────────────


def _combo_weight(combo: NameCombo) -> float:
    """Under-played bonus × streak multiplier."""
    underplayed = 1.0 / (combo.match_count + 1)
    s = combo.streak
    if s > 0:
        streak_mult = 1.0 + 0.3 * s  # 1.3 … 2.5
    elif s < 0:
        streak_mult = max(0.25, 1.0 + 0.15 * s)  # 0.85 … 0.25
    else:
        streak_mult = 1.0
    return underplayed * streak_mult


def _reach(streak: int) -> float:
    """How far above anchor Elo (in std-devs) we target for opponent."""
    if streak <= 0:
        return 0.4
    elif streak == 1:
        return 0.7
    elif streak == 2:
        return 1.0
    else:
        return 1.4


# ── Core selection ─────────────────────────────────────────────────────────────


def _pick_featured_name(
    eligible_name_ids: set[int],
    all_names_by_id: dict[int, Name],
    exclude_id: int | None = None,
) -> int | None:
    """Pick a name ID weighted by reputation. Exclude one ID if given."""
    pool = [
        nid for nid in eligible_name_ids if nid != exclude_id and nid in all_names_by_id
    ]
    if not pool:
        return None
    weights = [all_names_by_id[nid].reputation for nid in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def _pick_anchor_combo(
    combos_by_name: dict[int, list[NameCombo]],
    featured_name_id: int,
) -> NameCombo | None:
    """From combos featuring the chosen name, pick one by combo weight."""
    candidates = combos_by_name.get(featured_name_id, [])
    if not candidates:
        return None
    weights = [_combo_weight(c) for c in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def _pick_opponent_combo(
    anchor: NameCombo,
    eligible_name_ids: set[int],
    all_names_by_id: dict[int, Name],
    combos_by_name: dict[int, list[NameCombo]],
    all_combos: list[NameCombo],
    std: float,
) -> NameCombo | None:
    """
    Pick an opponent:
      1. Choose an opposing featured name by reputation (excluding anchor names).
      2. From that name's combos, pick the one closest in Elo to our target.
      3. Fallback: any combo not equal to anchor, closest to target Elo.
    """
    exclude = {anchor.first_id, anchor.middle_id}
    opp_pool = [
        nid
        for nid in eligible_name_ids
        if nid not in exclude and nid in all_names_by_id
    ]

    target_elo = anchor.elo_score + _reach(anchor.streak) * std

    if opp_pool:
        opp_weights = [all_names_by_id[nid].reputation for nid in opp_pool]
        opp_name_id = random.choices(opp_pool, weights=opp_weights, k=1)[0]
        candidates = [
            c for c in combos_by_name.get(opp_name_id, []) if c.id != anchor.id
        ]
        if candidates:
            return min(candidates, key=lambda c: abs(c.elo_score - target_elo))

    # Fallback — any combo, closest Elo to target
    fallback = [c for c in all_combos if c.id != anchor.id]
    if not fallback:
        return None
    return min(fallback, key=lambda c: abs(c.elo_score - target_elo))


# ── Public API ─────────────────────────────────────────────────────────────────


def pick_combo_pair(profile_id: int, gender_mode: str) -> tuple[int, int] | None:
    """
    Return (combo_id_a, combo_id_b) for the next match.
    Returns None if fewer than 2 eligible combos exist.
    """
    eligible_genders = _gender_enums(gender_mode)

    with get_session() as s:
        eligible_name_ids = set(
            n.id for n in s.query(Name).filter(Name.gender.in_(eligible_genders)).all()
        )
        all_names_by_id = {
            n.id: n for n in s.query(Name).filter(Name.id.in_(eligible_name_ids)).all()
        }
        all_combos: list[NameCombo] = (
            s.query(NameCombo)
            .filter(
                NameCombo.profile_id == profile_id,
                NameCombo.first_id.in_(eligible_name_ids),
                NameCombo.middle_id.in_(eligible_name_ids),
            )
            .all()
        )

    if len(all_combos) < 2:
        return None

    # Dark horse — fully random
    rand_pct = int(get_setting("match_random_pct") or 25) / 100.0
    if random.random() < rand_pct:
        a, b = random.sample(all_combos, 2)
        return a.id, b.id

    # Build name → combos index
    combos_by_name: dict[int, list[NameCombo]] = {}
    for c in all_combos:
        combos_by_name.setdefault(c.first_id, []).append(c)
        combos_by_name.setdefault(c.middle_id, []).append(c)

    scores = [c.elo_score for c in all_combos]
    std = statistics.stdev(scores) if len(scores) >= 2 else 100.0

    # Stage 1+2: anchor
    anchor_name_id = _pick_featured_name(eligible_name_ids, all_names_by_id)
    if anchor_name_id is None:
        a, b = random.sample(all_combos, 2)
        return a.id, b.id

    anchor = _pick_anchor_combo(combos_by_name, anchor_name_id)
    if anchor is None:
        a, b = random.sample(all_combos, 2)
        return a.id, b.id

    # Stage 3: opponent
    opponent = _pick_opponent_combo(
        anchor,
        eligible_name_ids,
        all_names_by_id,
        combos_by_name,
        all_combos,
        std,
    )
    if opponent is None:
        fallback = [c for c in all_combos if c.id != anchor.id]
        opponent = random.choice(fallback)

    return anchor.id, opponent.id
