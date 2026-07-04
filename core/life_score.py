"""
Score de vie — basé sur les Parcours ayant une catégorie renseignée
(peu importe la deadline).
Pondération : académique 30% + projet 25% + perso 15% + humain 10% + fondations 20%
"""
from models import Parcours
from core import daily_core


def _category_score(category: str) -> int:
    items = Parcours.query.filter_by(category=category).all()
    if not items:
        return 0

    total_checked = sum(p.checked_jalon_count() for p in items)
    avg = total_checked // len(items)

    return min((avg * 100) // 20, 100)


def calculate() -> dict:
    academique = _category_score("ACADEMIQUE")
    projet = _category_score("PROJET")
    perso = _category_score("PERSO")
    humain = _category_score("HUMAIN")
    daily_score = daily_core.compute_score()

    global_score = (
        academique * 30 + projet * 25 + perso * 15 + humain * 10 + daily_score * 20
    ) // 100

    return {
        "global": global_score,
        "academique": academique,
        "projet": projet,
        "perso": perso,
        "humain": humain,
    }
