from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Skill
from core import skills as skills_core

bp = Blueprint("skills", __name__, url_prefix="/skills")


@bp.route("/")
def index():
    all_skills = Skill.query.all()
    return render_template(
        "skills.html", active="skills", skills=all_skills, categories=Skill.CATEGORIES
    )


@bp.route("/nouveau", methods=["POST"])
def create():
    name = request.form.get("name", "")
    category = request.form.get("category")

    try:
        skills_core.create(name, category)
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("skills.index"))


@bp.route("/supprimer/<int:skill_id>", methods=["POST"])
def delete(skill_id):
    skills_core.delete(skill_id)
    return redirect(url_for("skills.index"))


@bp.route("/<int:skill_id>/jalons")
def milestones(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    return render_template("milestones.html", active="skills", skill=skill)


@bp.route("/<int:skill_id>/jalons/nouveau", methods=["POST"])
def add_milestone(skill_id):
    title = request.form.get("title", "").strip()
    if title:
        skills_core.add_milestone(skill_id, title)
    return redirect(url_for("skills.milestones", skill_id=skill_id))


@bp.route("/<int:skill_id>/jalons/cocher/<int:milestone_id>", methods=["POST"])
def check_milestone(skill_id, milestone_id):
    skills_core.check_milestone(milestone_id)
    return redirect(url_for("skills.milestones", skill_id=skill_id))


@bp.route("/<int:skill_id>/jalons/decocher/<int:milestone_id>", methods=["POST"])
def uncheck_milestone(skill_id, milestone_id):
    skills_core.uncheck_milestone(milestone_id)
    return redirect(url_for("skills.milestones", skill_id=skill_id))


@bp.route("/<int:skill_id>/jalons/supprimer/<int:milestone_id>", methods=["POST"])
def delete_milestone(skill_id, milestone_id):
    skills_core.delete_milestone(milestone_id)
    return redirect(url_for("skills.milestones", skill_id=skill_id))
