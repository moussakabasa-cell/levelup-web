"""
Port de ltg_system.c (check_long_term_goals) + long_term_goal.c + database.c.

Port fidèle y compris un détail du C : quand tous les sous-objectifs sont
cochés, le code calcule d'abord un statut temporel (EN_AVANCE/DANS_LES_TEMPS/
EN_RETARD) puis l'écrase immédiatement par COMPLETE. Résultat : un LTG avec
tous ses sous-objectifs cochés est TOUJOURS marqué COMPLETE, peu importe la
deadline. Gardé tel quel pour rester fidèle au comportement réel du moteur.
"""
from datetime import date
from extensions import db
from models import LongTermGoal, LtgSubObjective, today_str


def _days_left(deadline_str: str) -> int:
    deadline = date.fromisoformat(deadline_str)
    return (deadline - date.today()).days


def refresh_status(ltg: LongTermGoal):
    if ltg.status == LongTermGoal.COMPLETE:
        return

    if len(ltg.sub_objectives) == 0:
        ltg.status = LongTermGoal.INCONNU
        return

    all_checked = all(s.checked for s in ltg.sub_objectives)

    if all_checked:
        # cf. docstring : le statut temporel est calculé puis écrasé par COMPLETE
        ltg.status = LongTermGoal.COMPLETE
    else:
        days_left = _days_left(ltg.deadline)
        if days_left < 0:
            ltg.status = LongTermGoal.EN_RETARD
        elif days_left > 30:
            ltg.status = LongTermGoal.EN_AVANCE
        else:
            ltg.status = LongTermGoal.DANS_LES_TEMPS


def refresh_all():
    for ltg in LongTermGoal.query.all():
        refresh_status(ltg)
    db.session.commit()


def create(title: str, deadline: str) -> LongTermGoal:
    ltg = LongTermGoal(title=title, deadline=deadline, status=LongTermGoal.INCONNU)
    db.session.add(ltg)
    db.session.commit()
    return ltg


def delete(ltg_id: int):
    ltg = LongTermGoal.query.get(ltg_id)
    if ltg:
        db.session.delete(ltg)
        db.session.commit()


def add_sub_objective(ltg_id: int, title: str) -> LtgSubObjective:
    sub = LtgSubObjective(ltg_id=ltg_id, title=title, checked=0, checked_date="")
    db.session.add(sub)
    db.session.commit()
    return sub


def check_sub_objective(sub_id: int):
    sub = LtgSubObjective.query.get(sub_id)
    if sub is None:
        return
    sub.checked = 1
    sub.checked_date = today_str()
    db.session.commit()
    refresh_status(sub.ltg)
    db.session.commit()


def uncheck_sub_objective(sub_id: int):
    sub = LtgSubObjective.query.get(sub_id)
    if sub is None:
        return
    sub.checked = 0
    sub.checked_date = ""
    db.session.commit()


def delete_sub_objective(sub_id: int):
    sub = LtgSubObjective.query.get(sub_id)
    if sub:
        db.session.delete(sub)
        db.session.commit()


def has_work_this_week() -> dict:
    """
    Pour l'alerte cohérence dashboard : pour chaque LTG non complété, indique
    si AU MOINS UNE quête (sur n'importe quel skill) a été faite cette semaine
    — c'est le comportement réel du C (la boucle ne filtre pas par skill du LTG,
    puisque LongTermGoal n'a pas de skill_id peuplé). Un seul LTG en défaut
    suffit à déclencher l'alerte (le C s'arrête au premier trouvé).
    """
    from core.queries import get_skill_quests_this_week
    from models import Skill

    any_work_anywhere = any(
        get_skill_quests_this_week(s.id) > 0 for s in Skill.query.all()
    )

    result = {}
    for ltg in LongTermGoal.query.all():
        if ltg.status == LongTermGoal.COMPLETE:
            continue
        result[ltg.id] = any_work_anywhere
    return result
