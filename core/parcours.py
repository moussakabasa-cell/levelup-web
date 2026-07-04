"""
Parcours + Jalons — système unifié (remplace core/skills.py + core/ltg.py).

Un Parcours a une deadline optionnelle :
    - deadline = None -> compétence infinie (ancien "skill")
    - deadline = date -> projet borné (ancien "LTG"), statut recalculé

Un Jalon peut avoir plusieurs quêtes liées (Quest.jalon_id n'est pas
unique) — plusieurs actions concrètes peuvent faire progresser vers le
même jalon avant que l'utilisateur le coche consciemment.
"""
from datetime import date
from extensions import db
from models import Parcours, Jalon, today_str


def _days_left(deadline_str: str) -> int:
    return (date.fromisoformat(deadline_str) - date.today()).days


def refresh_status(p: Parcours):
    if p.is_perpetual():
        return  # pas de deadline -> pas de statut temporel pertinent

    if p.status == Parcours.COMPLETE:
        return

    if len(p.jalons) == 0:
        p.status = Parcours.INCONNU
        return

    all_checked = all(j.checked for j in p.jalons)

    if all_checked:
        p.status = Parcours.COMPLETE
    else:
        days_left = _days_left(p.deadline)
        if days_left < 0:
            p.status = Parcours.EN_RETARD
        elif days_left > 30:
            p.status = Parcours.EN_AVANCE
        else:
            p.status = Parcours.DANS_LES_TEMPS


def refresh_all():
    for p in Parcours.query.all():
        refresh_status(p)
    db.session.commit()


def create(title: str, deadline: str | None = None, category: str | None = None,
           description: str | None = None) -> Parcours:
    if category and category not in Parcours.CATEGORIES:
        raise ValueError(f"Categorie invalide (attendu: {Parcours.CATEGORIES})")

    p = Parcours(
        title=title.strip(), deadline=deadline or None, category=category or None,
        description=description or None, status=Parcours.INCONNU,
    )
    db.session.add(p)
    db.session.commit()
    return p


def delete(parcours_id: int):
    p = Parcours.query.get(parcours_id)
    if p:
        db.session.delete(p)
        db.session.commit()


def add_jalon(parcours_id: int, title: str) -> Jalon:
    j = Jalon(parcours_id=parcours_id, title=title.strip(), checked=0, checked_date="")
    db.session.add(j)
    db.session.commit()
    return j


def check_jalon(jalon_id: int):
    j = Jalon.query.get(jalon_id)
    if j is None:
        return
    j.checked = 1
    j.checked_date = today_str()
    db.session.commit()
    refresh_status(j.parcours)
    db.session.commit()


def uncheck_jalon(jalon_id: int):
    j = Jalon.query.get(jalon_id)
    if j is None:
        return
    j.checked = 0
    j.checked_date = ""
    db.session.commit()
    refresh_status(j.parcours)
    db.session.commit()


def delete_jalon(jalon_id: int):
    j = Jalon.query.get(jalon_id)
    if j:
        db.session.delete(j)
        db.session.commit()


def has_work_this_week() -> dict:
    """
    Alerte cohérence — uniquement pour les parcours AVEC deadline (l'ancien
    comportement LTG). Un parcours perpétuel (sans deadline) n'a pas de
    notion d'urgence hebdomadaire, donc pas concerné par cette alerte.
    """
    from core.queries import get_parcours_quests_this_week

    result = {}
    for p in Parcours.query.filter(Parcours.deadline.isnot(None)).all():
        if p.status == Parcours.COMPLETE:
            continue
        result[p.id] = get_parcours_quests_this_week(p.id) > 0
    return result
