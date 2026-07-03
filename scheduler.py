"""
Remplace la logique de reset "au lancement" de main.c (comparaison
last_done vs aujourd'hui) par un job planifié à minuit. Plus fiable pour
une app web que tu n'ouvres pas forcément tous les jours à la même heure.
"""
from apscheduler.schedulers.background import BackgroundScheduler

from extensions import db
from models import TimeSystem
from core import daily_core, quests as quests_core


def run_new_day(app):
    with app.app_context():
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
