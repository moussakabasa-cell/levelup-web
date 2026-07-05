"""
Remplace la logique de reset "au lancement" de main.c (comparaison
last_done vs aujourd'hui) par un job planifié à minuit. Plus fiable pour
une app web que tu n'ouvres pas forcément tous les jours à la même heure.

Capture aussi un instantané quotidien (fatigue/momentum/discipline/score
de vie) AVANT le reset, pour alimenter les courbes d'évolution.
"""
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler

from extensions import db
from models import TimeSystem, Player, DailySnapshot
from core import daily_core, quests as quests_core, life_score
from core.queries import get_discipline_score_7days


def capture_daily_snapshot():
    """Capture l'état du jour qui se termine, avant tout reset."""
    today = date.today().isoformat()
    if DailySnapshot.query.filter_by(date=today).first():
        return  # déjà capturé (évite les doublons si le job tourne 2x)

    player = Player.get()
    snap = DailySnapshot(
        date=today,
        fatigue=player.fatigue,
        momentum=player.momentum,
        streak=player.streak,
        daily_core_score=daily_core.compute_score(),
        life_score_global=life_score.calculate()["global"],
        discipline_score=get_discipline_score_7days(),
    )
    db.session.add(snap)
    db.session.commit()


def run_new_day(app):
    with app.app_context():
        capture_daily_snapshot()

        daily_core.new_day_reset()
        quests_core.reset_all_daily()

        ts = TimeSystem.get()
        ts.current_day += 1
        ts.total_days_played += 1
        db.session.commit()


def init_scheduler(app):
    scheduler = BackgroundScheduler(timezone=app.config["TIMEZONE"])
    scheduler.add_job(
        run_new_day,
        trigger="cron",
        hour=0,
        minute=0,
        args=[app],
        id="daily_reset",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler