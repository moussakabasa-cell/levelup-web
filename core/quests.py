"""Port de quest.c + quest_system.c + la partie quêtes de gameplay.c."""
from datetime import date
from extensions import db
from models import Quest, QuestCompletion, today_str
from core import player_state


def create(title: str, skill_id: int, qtype: str) -> Quest:
    if qtype not in Quest.TYPES:
        raise ValueError(f"Type invalide (attendu: {Quest.TYPES})")

    q = Quest(
        title=title,
        skill_id=skill_id if skill_id else None,
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


def complete(quest_id: int, player):
    """Équivalent complete_quest_menu + distribute_quest_rewards."""
    q = Quest.query.get(quest_id)
    if q is None:
        return None

    q.status = Quest.STATUS_COMPLETED
    q.last_completed = today_str()

    completion = QuestCompletion(
        quest_id=q.id, skill_id=q.skill_id, completed_date=today_str()
    )
    db.session.add(completion)
    db.session.commit()

    player_state.apply_quest_completion_rewards(player)
    return q


def reset_all_daily():
    """Équivalent reset_daily_quests — remet TOUTES les DAILY à AVAILABLE."""
    for q in Quest.query.filter_by(type="DAILY").all():
        q.status = Quest.STATUS_AVAILABLE
    db.session.commit()


def auto_reset_stale_daily():
    """
    Équivalent auto_reset_quests — ne remet à AVAILABLE que les DAILY dont
    last_completed n'est pas aujourd'hui (utile au tout premier chargement
    de la journée si le scheduler n'est pas encore passé).
    """
    today = date.today().isoformat()
    for q in Quest.query.filter_by(type="DAILY").all():
        if q.last_completed != "NEVER" and q.last_completed != today:
            q.status = Quest.STATUS_AVAILABLE
    db.session.commit()
