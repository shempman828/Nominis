"""Combo generation — create all ordered (first, middle) pairs for a new name."""

from database.db import get_session
from database.models import Name, NameCombo


def generate_combos_for_new_name(new_name_id: int):
    """
    When a new name is added, create all ordered pairs involving it:
      - (new, existing) and (existing, new) for every other name
      - across both profiles (1 and 2)
    A name cannot be paired with itself.
    """
    with get_session() as s:
        all_names = s.query(Name).all()
        all_ids = [n.id for n in all_names]

        existing_combos = set(
            (c.profile_id, c.first_id, c.middle_id)
            for c in s.query(
                NameCombo.profile_id, NameCombo.first_id, NameCombo.middle_id
            ).all()
        )

        new_rows = []
        for pid in (1, 2):
            for other_id in all_ids:
                if other_id == new_name_id:
                    continue
                # new as first
                if (pid, new_name_id, other_id) not in existing_combos:
                    new_rows.append(
                        NameCombo(
                            profile_id=pid, first_id=new_name_id, middle_id=other_id
                        )
                    )
                    existing_combos.add((pid, new_name_id, other_id))
                # new as middle
                if (pid, other_id, new_name_id) not in existing_combos:
                    new_rows.append(
                        NameCombo(
                            profile_id=pid, first_id=other_id, middle_id=new_name_id
                        )
                    )
                    existing_combos.add((pid, other_id, new_name_id))

        if new_rows:
            s.add_all(new_rows)
            s.commit()

    return len(new_rows)
