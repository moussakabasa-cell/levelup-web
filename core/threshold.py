"""Alerte "prêt à cocher" — jalons non cochés dont le palier de rappel
est actif (une nouvelle complétion a franchi un multiple du seuil,
et le jalon n'a pas encore été coché depuis)."""
from models import Jalon, QuestCompletion, DEFAULT_COMPLETION_THRESHOLD


def get_pending_threshold_jalons() -> list:
    """Renvoie la liste des jalons non cochés dont last_alert_at_count > 0
    ET dont le nombre de complétions est encore >= last_alert_at_count
    (autrement dit, l'utilisateur n'a rien fait depuis la dernière
    émission — ni cocher, ni décocher, ni supprimer le jalon)."""
    result = []
    for j in Jalon.query.filter_by(checked=0).all():
        if not j.last_alert_at_count or j.last_alert_at_count == 0:
            continue
        completions = QuestCompletion.query.filter_by(jalon_id=j.id).count()
        if completions >= j.last_alert_at_count:
            result.append({
                "jalon": j,
                "count": completions,
                "threshold": j.completion_threshold or DEFAULT_COMPLETION_THRESHOLD,
            })
    return result
