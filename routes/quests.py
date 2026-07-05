from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Quest, Parcours, Player
from core import quests as quests_core

bp = Blueprint("quests", __name__, url_prefix="/quetes")


@bp.route("/")
def index():
    all_quests = Quest.query.all()
    parcours_list = Parcours.query.all()   # pour le select jalon au moment de la complétion
    return render_template(
        "quests.html", active="quests",
        quests=all_quests, parcours_list=parcours_list, types=Quest.TYPES,
    )


@bp.route("/nouvelle", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    qtype = request.form.get("type")
    description = request.form.get("description", "").strip() or None
    location = request.form.get("location", "").strip() or None
    deadline = request.form.get("deadline", "").strip() or None

    try:
        quests_core.create(
            title, qtype,
            description=description, location=location, deadline=deadline,
        )
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("quests.index"))


@bp.route("/completer/<int:quest_id>", methods=["POST"])
def complete(quest_id):
    player = Player.get()
    jalon_id = request.form.get("jalon_id", type=int)
    result = quests_core.complete(quest_id, player, jalon_id=jalon_id)

    jalon = result.get("jalon")
    if jalon:
        flash(f"Tu progresses vers le jalon « {jalon.title} » ({jalon.parcours.title}).")
        return redirect(url_for("parcours.detail", parcours_id=jalon.parcours_id))

    return redirect(url_for("quests.index"))


@bp.route("/supprimer/<int:quest_id>", methods=["POST"])
def delete(quest_id):
    quests_core.delete(quest_id)
    return redirect(url_for("quests.index"))
