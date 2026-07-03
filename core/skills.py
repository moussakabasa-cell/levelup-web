"""Port de skill.c + skill_category.c + la partie skills/jalons de gameplay.c."""
from extensions import db
from models import Skill, SkillMilestone, today_str


def create(name: str, category: str) -> Skill:
    name = name.strip().lower()

    if not name or not all(c.isalpha() or c == " " for c in name):
        raise ValueError("Nom de skill invalide (lettres uniquement).")

    if category not in Skill.CATEGORIES:
        raise ValueError(f"Categorie invalide (attendu: {Skill.CATEGORIES})")

    if Skill.query.filter_by(name=name).first() is not None:
        raise ValueError("Skill deja existant.")

    s = Skill(name=name, category=category, level=0, xp=0)
    db.session.add(s)
    db.session.commit()
    return s


def delete(skill_id: int):
    s = Skill.query.get(skill_id)
    if s:
        db.session.delete(s)  # cascade supprime les jalons
        db.session.commit()


def add_milestone(skill_id: int, title: str) -> SkillMilestone:
    m = SkillMilestone(skill_id=skill_id, title=title, checked=0, checked_date="")
    db.session.add(m)
    db.session.commit()
    return m


def check_milestone(milestone_id: int):
    m = SkillMilestone.query.get(milestone_id)
    if m is None:
        return
    m.checked = 1
    m.checked_date = today_str()
    db.session.commit()


def uncheck_milestone(milestone_id: int):
    m = SkillMilestone.query.get(milestone_id)
    if m is None:
        return
    m.checked = 0
    m.checked_date = ""
    db.session.commit()


def delete_milestone(milestone_id: int):
    m = SkillMilestone.query.get(milestone_id)
    if m:
        db.session.delete(m)
        db.session.commit()
