"""
Score de vie — basé sur les Parcours ayant une catégorie renseignée.

Pondération (point de départ, ajustable facilement si besoin — ce sont
juste des nombres dans WEIGHTS ci-dessous) :
    académique 20 + projet 16 + santé 12 + perso 10 + humain 8
    + spirituel 6 + social 4 + financier 4 + fondations 20 = 100
"""
from models import Parcours
from core import daily_core

WEIGHTS = {
    "ACADEMIQUE": 20,
    "PROJET": 16,
    "SANTE": 12,
    "PERSO": 10,
    "HUMAIN": 8,
    "SPIRITUEL": 6,
    "SOCIAL": 4,
    "FINANCIER": 4,
}
DAILY_CORE_WEIGHT = 20


def _category_score(category: str) -> int:
    items = Parcours.query.filter_by(category=category).all()
    if not items:
        return 0

    total_checked = sum(p.checked_jalon_count() for p in items)
    avg = total_checked // len(items)

    return min((avg * 100) // 20, 100)


def calculate() -> dict:
    scores = {cat: _category_score(cat) for cat in WEIGHTS}
    daily_score = daily_core.compute_score()

    global_score = sum(scores[cat] * WEIGHTS[cat] for cat in WEIGHTS)
    global_score += daily_score * DAILY_CORE_WEIGHT
    global_score //= 100

    result = {"global": global_score, "daily_core": daily_score}
    result.update({cat.lower(): score for cat, score in scores.items()})
    return result
