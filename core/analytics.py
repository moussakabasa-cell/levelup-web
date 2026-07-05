"""
Prépare les données pour la page /analytics.

- heatmap_completions : jours actifs (nb de quêtes complétées par jour),
  90 derniers jours — utilisable immédiatement (basé sur quest_completions,
  déjà en base).
- jalons_timeline : cumul de jalons cochés dans le temps — utilisable
  immédiatement (basé sur Jalon.checked_date).
- snapshot_series : fatigue/momentum/discipline/score de vie dans le temps
  — vide tant que le scheduler n'a pas capturé au moins un jour (voir
  scheduler.py : capture_daily_snapshot).
"""
from datetime import date, timedelta
from collections import defaultdict

from extensions import db
from models import QuestCompletion, Jalon, DailySnapshot


def heatmap_completions(days: int = 90) -> dict:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (
        QuestCompletion.query.with_entities(QuestCompletion.completed_date)
        .filter(QuestCompletion.completed_date >= since)
        .all()
    )
    counts = defaultdict(int)
    for (d,) in rows:
        counts[d] += 1

    # grille complète jour par jour (même les jours à 0, pour la heatmap)
    result = []
    for i in range(days, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        result.append({"date": d, "count": counts.get(d, 0)})
    return result


def jalons_timeline() -> list:
    rows = (
        Jalon.query.with_entities(Jalon.checked_date)
        .filter(Jalon.checked == 1, Jalon.checked_date != "")
        .all()
    )
    counts = defaultdict(int)
    for (d,) in rows:
        if d:
            counts[d] += 1

    dates_sorted = sorted(counts.keys())
    cumulative = []
    total = 0
    for d in dates_sorted:
        total += counts[d]
        cumulative.append({"date": d, "total": total})
    return cumulative


def snapshot_series(days: int = 30) -> list:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (
        DailySnapshot.query.filter(DailySnapshot.date >= since)
        .order_by(DailySnapshot.date.asc())
        .all()
    )
    return [
        {
            "date": r.date,
            "fatigue": r.fatigue,
            "momentum": r.momentum,
            "streak": r.streak,
            "daily_core_score": r.daily_core_score,
            "life_score_global": r.life_score_global,
            "discipline_score": r.discipline_score,
        }
        for r in rows
    ]


def foundation_validation_rates(days: int = 30) -> list:
    """Taux de validation par fondation sur N jours — un seul graphique,
    une barre par fondation, pas un graphique par fondation."""
    from models import Foundation, FoundationValidation

    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (
        FoundationValidation.query.with_entities(
            FoundationValidation.foundation_id, FoundationValidation.date
        )
        .filter(FoundationValidation.date >= since)
        .all()
    )
    counts = defaultdict(set)
    for fid, d in rows:
        counts[fid].add(d)

    result = []
    for f in Foundation.query.all():
        validated_days = len(counts.get(f.id, set()))
        rate = min(round(validated_days / days * 100), 100)
        result.append({"title": f.title, "rate": rate})
    return result


def quests_by_category(days: int = 30) -> list:
    """Quêtes complétées par catégorie de parcours sur N jours — un seul
    graphique en barres, pas un par catégorie."""
    from models import Jalon, Parcours

    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (
        db.session.query(Parcours.category, db.func.count(QuestCompletion.id))
        .select_from(QuestCompletion)
        .join(Jalon, QuestCompletion.jalon_id == Jalon.id)
        .join(Parcours, Jalon.parcours_id == Parcours.id)
        .filter(QuestCompletion.completed_date >= since)
        .group_by(Parcours.category)
        .all()
    )
    counts = {cat or "Sans catégorie": n for cat, n in rows}

    # complétions sans jalon lié (jalon_id NULL) — "non catégorisées"
    uncategorized = QuestCompletion.query.filter(
        QuestCompletion.completed_date >= since, QuestCompletion.jalon_id.is_(None)
    ).count()
    if uncategorized:
        counts["Sans jalon lié"] = counts.get("Sans jalon lié", 0) + uncategorized

    return [{"category": cat, "count": n} for cat, n in counts.items()]
