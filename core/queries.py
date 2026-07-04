"""
Requêtes analytics — schéma Parcours/Jalon.
Toutes basées sur quest_completions, la source de vérité.
"""
from datetime import date, timedelta
from extensions import db
from models import QuestCompletion, Jalon


def _date_n_days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def _jalon_ids_for_parcours(parcours_id: int) -> list[int]:
    return [j.id for j in Jalon.query.filter_by(parcours_id=parcours_id).all()]


def get_days_since_parcours_worked(parcours_id: int) -> int:
    """-1 si jamais travaillé. Regarde toutes les complétions liées à
    n'importe quel jalon de ce parcours."""
    jalon_ids = _jalon_ids_for_parcours(parcours_id)
    if not jalon_ids:
        return -1

    last = (
        QuestCompletion.query.filter(QuestCompletion.jalon_id.in_(jalon_ids))
        .order_by(QuestCompletion.completed_date.desc())
        .first()
    )
    if last is None:
        return -1
    return (date.today() - date.fromisoformat(last.completed_date)).days


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


def get_parcours_quests_this_week(parcours_id: int) -> int:
    jalon_ids = _jalon_ids_for_parcours(parcours_id)
    if not jalon_ids:
        return 0
    since = _date_n_days_ago(7)
    return QuestCompletion.query.filter(
        QuestCompletion.jalon_id.in_(jalon_ids),
        QuestCompletion.completed_date >= since,
    ).count()


def get_discipline_score_7days() -> int:
    since = _date_n_days_ago(7)
    rows = (
        QuestCompletion.query.with_entities(QuestCompletion.completed_date)
        .filter(QuestCompletion.completed_date >= since)
        .distinct()
        .all()
    )
    return (len(rows) * 100) // 7


def quest_completed_today(quest_id: int) -> bool:
    today = date.today().isoformat()
    return (
        QuestCompletion.query.filter_by(quest_id=quest_id, completed_date=today).count() > 0
    )
