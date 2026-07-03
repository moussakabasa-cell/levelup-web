from flask import Blueprint, render_template

from models import Player, Foundation
from core import daily_core, life_score, profiling, alerts as alerts_core, recommendation
from core.queries import get_discipline_score_7days, quest_completed_today
from models import Quest

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    player = Player.get()
    discipline = get_discipline_score_7days()
    daily_score = daily_core.compute_score()
    day_validated = daily_score >= 80
    foundation_count = Foundation.query.count()

    ls = life_score.calculate()
    profile = profiling.generate_profile()
    alerts = alerts_core.build_alerts()
    recommended = recommendation.recommend()

    daily_quests = Quest.query.filter_by(type="DAILY").all()
    commitments = [
        {"quest": q, "done": quest_completed_today(q.id)} for q in daily_quests
    ]

    return render_template(
        "dashboard.html",
        active="dashboard",
        player=player,
        discipline=discipline,
        daily_score=daily_score,
        day_validated=day_validated,
        foundation_count=foundation_count,
        life_score=ls,
        profile=profile,
        alerts=alerts,
        recommended=recommended,
        commitments=commitments,
    )
