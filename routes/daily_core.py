from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Foundation
from core import daily_core

bp = Blueprint("daily_core", __name__, url_prefix="/fondations")


@bp.route("/")
def index():
    foundations = Foundation.query.all()
    score = daily_core.compute_score()
    validated = score >= 80
    return render_template(
        "daily_core.html", active="daily_core",
        foundations=foundations, score=score, validated=validated,
        types=Foundation.TYPES,
    )


@bp.route("/valider/<int:foundation_id>", methods=["POST"])
def validate(foundation_id):
    daily_core.validate_foundation(foundation_id)
    daily_core.apply_impact()
    return redirect(url_for("daily_core.index"))


@bp.route("/devalider/<int:foundation_id>", methods=["POST"])
def unvalidate(foundation_id):
    daily_core.unvalidate_foundation(foundation_id)
    return redirect(url_for("daily_core.index"))


@bp.route("/nouvelle", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    ftype = request.form.get("type")
    weight = request.form.get("weight", type=int)

    try:
        daily_core.create_foundation(title, ftype, weight)
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("daily_core.index"))


@bp.route("/supprimer/<int:foundation_id>", methods=["POST"])
def delete(foundation_id):
    daily_core.delete_foundation(foundation_id)
    return redirect(url_for("daily_core.index"))
