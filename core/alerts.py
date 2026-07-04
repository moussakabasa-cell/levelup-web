"""
Alertes dashboard.

- "Parcours inactif" : s'applique à TOUS les parcours (avec ou sans
  deadline), signal de dérive générique.
- "Incohérence" : uniquement les parcours AVEC deadline non complétés
  (l'ancienne alerte LTG) — pas de sens pour un parcours perpétuel.
"""
from models import Parcours, Foundation, Player
from core import daily_core, profiling, parcours as parcours_core
from core.queries import get_days_since_parcours_worked


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
        alerts.append(f"Stagnation detectee sur {profile['dominant_parcours']}")

    for p in Parcours.query.all():
        days = get_days_since_parcours_worked(p.id)
        if days >= 7:
            alerts.append(f"Parcours inactif : {p.title} ({days} jours)")

    if daily_score < 30 and player.streak == 0:
        alerts.append("BURNOUT DETECTE : fondations et streak a zero. Recupere-toi.")
    elif daily_score < 50 and player.fatigue > 50:
        alerts.append("Risque burnout : fatigue elevee + fondations faibles.")

    work_map = parcours_core.has_work_this_week()
    for parcours_id, has_work in work_map.items():
        if not has_work:
            p = Parcours.query.get(parcours_id)
            alerts.append(f"Incoherence : \"{p.title}\" - aucune seance cette semaine.")
            break

    return alerts
