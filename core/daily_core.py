"""
Port de daily_core.c + daily_core_system.c

Formules gardées à l'identique :
- score = (poids_done / poids_total) * 100   (division entière, comme en C)
- journée validée si score >= 80
- impact : score>=80 -> momentum+10, fatigue-5 (floor via >=5)
           score<50  -> fatigue+5, momentum-5 (floor via >=5)
"""
from extensions import db
from models import Foundation, Player, today_str


def compute_score() -> int:
    foundations = Foundation.query.all()
    total_weight = sum(f.weight or 0 for f in foundations)
    done_weight = sum(f.weight or 0 for f in foundations if f.status == Foundation.DONE)

    if total_weight == 0:
        return 0

    return (done_weight * 100) // total_weight


def is_validated() -> bool:
    return compute_score() >= 80


def validate_foundation(foundation_id: int):
    """Équivalent daily_core_validate (une seule fondation à la fois côté web)."""
    f = Foundation.query.get(foundation_id)
    if f is None or f.status == Foundation.DONE:
        return
    f.status = Foundation.DONE
    f.last_done = today_str()
    db.session.commit()


def unvalidate_foundation(foundation_id: int):
    f = Foundation.query.get(foundation_id)
    if f is None:
        return
    f.status = Foundation.PENDING
    f.last_done = ""
    db.session.commit()


def apply_impact():
    """Équivalent daily_core_apply_impact — appelle après validation/à minuit."""
    score = compute_score()
    player = Player.get()

    if score >= 80:
        player.momentum += 10
        if player.fatigue >= 5:
            player.fatigue -= 5
    elif score < 50:
        player.fatigue += 5
        if player.momentum >= 5:
            player.momentum -= 5

    db.session.commit()
    return score


def new_day_reset():
    """
    Équivalent daily_core_new_day (daily_core_system.c) + la décroissance
    fatigue*0.7 / momentum*0.8 que le C applique dans main.c au new_day.
    Appelé par le scheduler à minuit (voir scheduler.py).
    """
    apply_impact()

    for f in Foundation.query.all():
        f.status = Foundation.PENDING
        f.last_done = ""

    player = Player.get()
    player.fatigue = max(0, int(player.fatigue * 0.7))
    player.momentum = max(0, int(player.momentum * 0.8))

    db.session.commit()


def create_foundation(title: str, ftype: str, weight: int) -> Foundation:
    if ftype not in Foundation.TYPES:
        raise ValueError(f"Type invalide (attendu: {Foundation.TYPES})")
    if not (1 <= weight <= 10):
        raise ValueError("Poids invalide (1-10)")

    f = Foundation(title=title, type=ftype, weight=weight, status=Foundation.PENDING, last_done="")
    db.session.add(f)
    db.session.commit()
    return f
