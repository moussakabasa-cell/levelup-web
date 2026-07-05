"""
Quêtes — CRUD + reset auto daily.

Changement (retour d'expérience) : le jalon n'est plus fixé sur la quête
elle-même (une quête DAILY comme "Séance de maths" ne travaille pas le même
jalon tous les jours). Le jalon se choisit maintenant à chaque COMPLÉTION,
optionnellement — pas à la création de la quête.
"""
from datetime import date
from extensions import db
from models import Quest, QuestCompletion, Jalon, today_str
from core import player_state


def create(title: str, qtype: str, description: str | None = None,
           location: str | None = None, deadline: str | None = None) -> Quest:
    if qtype not in Quest.TYPES:
        raise ValueError(f"Type invalide (attendu: {Quest.TYPES})")

    q = Quest(
        title=title,
        type=qtype,
        status=Quest.STATUS_AVAILABLE,
        last_completed="NEVER",
        description=description or None,
        location=location or None,
        deadline=deadline or None,
    )
    db.session.add(q)
    db.session.commit()
    return q


def delete(quest_id: int):
    q = Quest.query.get(quest_id)
    if q:
        db.session.delete(q)
        db.session.commit()


def complete(quest_id: int, player, jalon_id: int | None = None) -> dict:
    """
    jalon_id : choisi au moment de la complétion (optionnel), pas fixé sur
    la quête. Retourne {"quest": q, "jalon": Jalon|None} pour affichage —
    le jalon n'est jamais coché automatiquement, juste signalé comme
    "en progression".
    """
    q = Quest.query.get(quest_id)
    if q is None:
        return {"quest": None, "jalon": None}

    q.status = Quest.STATUS_COMPLETED
    q.last_completed = today_str()

    completion = QuestCompletion(
        quest_id=q.id, jalon_id=jalon_id, completed_date=today_str()
    )
    db.session.add(completion)
    db.session.commit()

    player_state.apply_quest_completion_rewards(player)

    jalon = Jalon.query.get(jalon_id) if jalon_id else None

    return {"quest": q, "jalon": jalon}


def reset_all_daily():
    for q in Quest.query.filter_by(type="DAILY").all():
        q.status = Quest.STATUS_AVAILABLE
    db.session.commit()


def auto_reset_stale_daily():
    today = date.today().isoformat()
    for q in Quest.query.filter_by(type="DAILY").all():
        if q.last_completed != "NEVER" and q.last_completed != today:
            q.status = Quest.STATUS_AVAILABLE
    db.session.commit()
