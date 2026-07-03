"""
Port de life_score.c.

Pondération RÉELLE (celle du calcul, pas celle du commentaire du code C
qui dit 35/30/20/15 mais calcule en fait avec ces coefficients) :
    academique 30% + projet 25% + perso 15% + humain 10% + daily_core 20%

category_score : proxy = jalons cochés / catégorie, moyenne par skill,
plafonné à 100 (20 jalons cochés en moyenne = 100).
"""
from models import Skill
from core import daily_core


def _category_score(category: str) -> int:
    skills = Skill.query.filter_by(category=category).all()
    if not skills:
        return 0

    total_checked = sum(s.checked_milestone_count() for s in skills)
    avg = total_checked // len(skills)

    score = (avg * 100) // 20
    return min(score, 100)


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


def weakest_category(scores: dict) -> tuple[str, int]:
    """Retourne (nom, score) de la catégorie la plus faible, pour l'alerte déséquilibre."""
    cats = {
        "Academique": scores["academique"],
        "Projet": scores["projet"],
        "Perso": scores["perso"],
        "Humain": scores["humain"],
    }
    name = min(cats, key=cats.get)
    return name, cats[name]
