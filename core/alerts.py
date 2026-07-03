"""
Port fidèle du bloc ALERTES de dashboard.c — même ordre, mêmes seuils.

Note de correction (signalée à Moks) : le C compare `status != 2` en
commentant "2 = COMPLETE", mais dans l'enum LtgStatus réel COMPLETE vaut 3
(EN_AVANCE=0, DANS_LES_TEMPS=1, EN_RETARD=2, COMPLETE=3). C'est un bug —
le code excluait par erreur les LTG "EN RETARD" au lieu des LTG "COMPLETE".
Ici on utilise le vrai statut COMPLETE, conformément à l'intention du
commentaire d'origine.
"""
from models import Skill, Foundation, LongTermGoal, Player
from core import daily_core, profiling, ltg as ltg_core
from core.queries import get_days_since_skill_worked


def build_alerts() -> list[str]:
    alerts = []
    player = Player.get()
    daily_score = daily_core.compute_score()
    foundation_count = Foundation.query.count()

    if player.fatigue >= 60:
        alerts.append(f"Fatigue elevee ({player.fatigue})")

    if player.streak == 0:
        alerts.append("Streak perdu. Reprends aujourd'hui.")

    if daily_score < 50 and foundation_count > 0:
        alerts.append(f"Fondations faibles ({daily_score}/100)")

    profile = profiling.generate_profile()
    if profile["stagnation_detected"]:
        alerts.append(f"Stagnation detectee sur {profile['dominant_skill']}")

    for skill in Skill.query.all():
        days = get_days_since_skill_worked(skill.id)
        if days >= 7:
            alerts.append(f"Skill inactif : {skill.name} ({days} jours)")

    if daily_score < 30 and player.streak == 0:
        alerts.append("BURNOUT DETECTE : fondations et streak a zero. Recupere-toi.")
    elif daily_score < 50 and player.fatigue > 50:
        alerts.append("Risque burnout : fatigue elevee + fondations faibles.")

    work_map = ltg_core.has_work_this_week()
    for ltg_id, has_work in work_map.items():
        if not has_work:
            goal = LongTermGoal.query.get(ltg_id)
            alerts.append(f"Incoherence : \"{goal.title}\" - aucune seance cette semaine.")
            break  # le C ne signale qu'une seule incohérence de ce type

    return alerts
