"""
Port de recommendation.c — version SIMPLE confirmée (top 3 disponibles),
celle qui matche réellement ton schéma Quest actuel (skill_id unique,
pas de difficulty/skill_ids[]).
"""
from models import Quest


def recommend(limit: int = 3) -> list[Quest]:
    return (
        Quest.query.filter_by(status=Quest.STATUS_AVAILABLE)
        .limit(limit)
        .all()
    )
