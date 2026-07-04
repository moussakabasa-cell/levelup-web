"""Quêtes — CRUD + reset auto daily. Lien vers un Jalon précis, plusieurs
quêtes peuvent partager le même jalon (Quest.jalon_id n'est pas unique)."""
from datetime import date
from extensions import db
from models import Quest, QuestCompletion, Jalon, today_str
from core import player_state


def create(title: str, jalon_id: int | None, qtype: str) -> Quest:
    if qtype not in Quest.TYPES:
        raise ValueError(f"Type invalide (attendu: {Quest.TYPES})")

    q = Quest(
        title=title,
        jalon_id=jalon_id if jalon_id else None,
        type=qtype,
        status=Quest.STATUS_AVAILABLE,
        last_completed="NEVER",
    )
    db.session.add(q)
    db.session.commit()
    return q


def delete(quest_id: int):
    q = Quest.query.get(quest_id)
    if q:
        db.session.delete(q)
        db.session.commit()


def complete(quest_id: int, player) -> dict:
    """
    Retourne {"quest": q, "jalon": Jalon|None} — si la quête est liée à un
    jalon, on le retourne pour afficher "tu progresses vers ce jalon" et
    proposer de le cocher, SANS jamais le cocher automatiquement (le
    cochage reste une validation consciente de l'utilisateur, y compris
    si le jalon est déjà coché ou si plusieurs quêtes y contribuent).
    """
    q = Quest.query.get(quest_id)
    if q is None:
        return {"quest": None, "jalon": None}

    q.status = Quest.STATUS_COMPLETED
    q.last_completed = today_str()

    completion = QuestCompletion(
        quest_id=q.id, jalon_id=q.jalon_id, completed_date=today_str()
    )
    db.session.add(completion)
    db.session.commit()

    player_state.apply_quest_completion_rewards(player)

    jalon = Jalon.query.get(q.jalon_id) if q.jalon_id else None

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
