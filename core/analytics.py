"""
Prépare les données pour la page /analytics.

- heatmap_completions : jours actifs (nb de quêtes complétées par jour),
  90 derniers jours — utilisable immédiatement (basé sur quest_completions,
  déjà en base).
- jalons_timeline : cumul de jalons cochés dans le temps — utilisable
  immédiatement (basé sur Jalon.checked_date).
- snapshot_series : fatigue/momentum/discipline/score de vie dans le temps
  — vide tant que le scheduler n'a pas capturé au moins un jour.
"""
from datetime import date, timedelta
from collections import defaultdict

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