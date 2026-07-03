from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import LongTermGoal
from core import ltg as ltg_core

bp = Blueprint("ltg", __name__, url_prefix="/objectifs")


@bp.route("/")
def index():
    ltg_core.refresh_all()
    goals = LongTermGoal.query.all()
    return render_template(
        "ltg.html", active="ltg", goals=goals, labels=LongTermGoal.STATUS_LABELS
    )


@bp.route("/nouveau", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    deadline = request.form.get("deadline", "").strip()

    if not title or not deadline:
        flash("Titre et deadline requis.")
    else:
        ltg_core.create(title, deadline)

    return redirect(url_for("ltg.index"))


@bp.route("/supprimer/<int:ltg_id>", methods=["POST"])
def delete(ltg_id):
    ltg_core.delete(ltg_id)
    return redirect(url_for("ltg.index"))


@bp.route("/<int:ltg_id>")
def detail(ltg_id):
    goal = LongTermGoal.query.get_or_404(ltg_id)
    return render_template(
        "ltg_detail.html", active="ltg", goal=goal, labels=LongTermGoal.STATUS_LABELS
    )


@bp.route("/<int:ltg_id>/sous-objectifs/nouveau", methods=["POST"])
def add_sub(ltg_id):
    title = request.form.get("title", "").strip()
    if title:
        ltg_core.add_sub_objective(ltg_id, title)
    return redirect(url_for("ltg.detail", ltg_id=ltg_id))


@bp.route("/<int:ltg_id>/sous-objectifs/cocher/<int:sub_id>", methods=["POST"])
def check_sub(ltg_id, sub_id):
    ltg_core.check_sub_objective(sub_id)
    return redirect(url_for("ltg.detail", ltg_id=ltg_id))


@bp.route("/<int:ltg_id>/sous-objectifs/decocher/<int:sub_id>", methods=["POST"])
def uncheck_sub(ltg_id, sub_id):
    ltg_core.uncheck_sub_objective(sub_id)
    return redirect(url_for("ltg.detail", ltg_id=ltg_id))


@bp.route("/<int:ltg_id>/sous-objectifs/supprimer/<int:sub_id>", methods=["POST"])
def delete_sub(ltg_id, sub_id):
    ltg_core.delete_sub_objective(sub_id)
    return redirect(url_for("ltg.detail", ltg_id=ltg_id))
