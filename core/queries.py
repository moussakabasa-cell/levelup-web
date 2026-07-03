"""
Port des fonctions de requête analytics de database.c.
Toutes basées sur quest_completions, la source de vérité (pas quests.status).
"""
from datetime import date, timedelta
from extensions import db
from models import QuestCompletion


def _date_n_days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def get_days_since_skill_worked(skill_id: int) -> int:
    """Équivalent get_days_since_skill_worked — -1 si jamais travaillé."""
    last = (
        QuestCompletion.query.filter_by(skill_id=skill_id)
        .order_by(QuestCompletion.completed_date.desc())
        .first()
    )
    if last is None:
        return -1
    last_date = date.fromisoformat(last.completed_date)
    return (date.today() - last_date).days


def get_quests_done_today() -> int:
    today = date.today().isoformat()
    return (
        db.session.query(QuestCompletion.quest_id)
        .filter_by(completed_date=today)
        .distinct()
        .count()
    )


def get_quests_done_last_week() -> int:
    since = _date_n_days_ago(7)
    return QuestCompletion.query.filter(QuestCompletion.completed_date >= since).count()


def get_skill_quests_this_week(skill_id: int) -> int:
    since = _date_n_days_ago(7)
    return QuestCompletion.query.filter(
        QuestCompletion.skill_id == skill_id,
        QuestCompletion.completed_date >= since,
    ).count()


def get_discipline_score_7days() -> int:
    """Nombre de jours distincts (sur 7) avec >=1 quête complétée -> score/100."""
    since = _date_n_days_ago(7)
    rows = (
        QuestCompletion.query.with_entities(QuestCompletion.completed_date)
        .filter(QuestCompletion.completed_date >= since)
        .distinct()
        .all()
    )
    count = len(rows)
    return (count * 100) // 7


def quest_completed_today(quest_id: int) -> bool:
    today = date.today().isoformat()
    return (
        QuestCompletion.query.filter_by(quest_id=quest_id, completed_date=today).count() > 0
    )
