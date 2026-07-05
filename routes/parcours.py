from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Parcours
from core import parcours as parcours_core

bp = Blueprint("parcours", __name__, url_prefix="/parcours")


@bp.route("/")
def index():
    parcours_core.refresh_all()
    perpetuels = Parcours.query.filter(Parcours.deadline.is_(None)).all()
    bornes = Parcours.query.filter(Parcours.deadline.isnot(None)).all()
    return render_template(
        "parcours.html", active="parcours",
        perpetuels=perpetuels, bornes=bornes,
        labels=Parcours.STATUS_LABELS, categories=Parcours.CATEGORIES,
    )


@bp.route("/nouveau", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    deadline = request.form.get("deadline", "").strip() or None
    category = request.form.get("category", "").strip() or None

    if not title:
        flash("Titre requis.")
    else:
        try:
            parcours_core.create(title, deadline=deadline, category=category)
        except ValueError as e:
            flash(str(e))

    return redirect(url_for("parcours.index"))


@bp.route("/supprimer/<int:parcours_id>", methods=["POST"])
def delete(parcours_id):
    parcours_core.delete(parcours_id)
    return redirect(url_for("parcours.index"))


@bp.route("/<int:parcours_id>/modifier", methods=["POST"])
def update(parcours_id):
    title = request.form.get("title", "").strip()
    deadline = request.form.get("deadline", "").strip() or None
    category = request.form.get("category", "").strip() or None
    description = request.form.get("description", "").strip() or None

    try:
        parcours_core.update(
            parcours_id, title=title or None, deadline=deadline,
            category=category, description=description,
        )
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("parcours.detail", parcours_id=parcours_id))


@bp.route("/<int:parcours_id>")
def detail(parcours_id):
    p = Parcours.query.get_or_404(parcours_id)
    parcours_core.refresh_status(p)
    autres_parcours = Parcours.query.filter(Parcours.id != parcours_id).all()
    return render_template(
        "parcours_detail.html", active="parcours", p=p,
        labels=Parcours.STATUS_LABELS, categories=Parcours.CATEGORIES,
        autres_parcours=autres_parcours,
    )


@bp.route("/<int:parcours_id>/jalons/nouveau", methods=["POST"])
def add_jalon(parcours_id):
    title = request.form.get("title", "").strip()
    if title:
        parcours_core.add_jalon(parcours_id, title)
    return redirect(url_for("parcours.detail", parcours_id=parcours_id))


@bp.route("/<int:parcours_id>/jalons/cocher/<int:jalon_id>", methods=["POST"])
def check_jalon(parcours_id, jalon_id):
    parcours_core.check_jalon(jalon_id)
    return redirect(url_for("parcours.detail", parcours_id=parcours_id))


@bp.route("/<int:parcours_id>/jalons/decocher/<int:jalon_id>", methods=["POST"])
def uncheck_jalon(parcours_id, jalon_id):
    parcours_core.uncheck_jalon(jalon_id)
    return redirect(url_for("parcours.detail", parcours_id=parcours_id))


@bp.route("/<int:parcours_id>/jalons/supprimer/<int:jalon_id>", methods=["POST"])
def delete_jalon(parcours_id, jalon_id):
    parcours_core.delete_jalon(jalon_id)
    return redirect(url_for("parcours.detail", parcours_id=parcours_id))


@bp.route("/<int:parcours_id>/jalons/dupliquer/<int:jalon_id>", methods=["POST"])
def duplicate_jalon(parcours_id, jalon_id):
    target_id = request.form.get("target_parcours_id", type=int)
    if target_id:
        parcours_core.duplicate_jalon(jalon_id, target_id)
        flash("Jalon dupliqué — c'est une copie indépendante, cocher l'un ne touche pas l'autre.")
    return redirect(url_for("parcours.detail", parcours_id=parcours_id))