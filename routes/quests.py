from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Quest, Skill, Player
from core import quests as quests_core

bp = Blueprint("quests", __name__, url_prefix="/quetes")


@bp.route("/")
def index():
    all_quests = Quest.query.all()
    skills = Skill.query.all()
    return render_template(
        "quests.html", active="quests",
        quests=all_quests, skills=skills, types=Quest.TYPES,
    )


@bp.route("/nouvelle", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    skill_id = request.form.get("skill_id", type=int)
    qtype = request.form.get("type")

    try:
        quests_core.create(title, skill_id, qtype)
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("quests.index"))


@bp.route("/completer/<int:quest_id>", methods=["POST"])
def complete(quest_id):
    player = Player.get()
    quests_core.complete(quest_id, player)
    return redirect(url_for("quests.index"))


@bp.route("/supprimer/<int:quest_id>", methods=["POST"])
def delete(quest_id):
    quests_core.delete(quest_id)
    return redirect(url_for("quests.index"))
