"""
Export/backup — bouton caché, pas dans la nav principale. Accessible via
/backup pour télécharger un JSON avec toutes les données personnelles.
Protège d'un crash Railway, d'une migration ratée, d'un compte suspendu.
"""
from datetime import date
from flask import Blueprint, jsonify, Response
import json

from models import (
    Parcours, Jalon, Quest, QuestCompletion, Player, TimeSystem,
    Foundation, FoundationValidation, DailySnapshot,
)

bp = Blueprint("backup", __name__, url_prefix="/backup")


def _obj_to_dict(obj, columns):
    return {c: getattr(obj, c) for c in columns}


@bp.route("/")
def export_all():
    data = {
        "exported_at": date.today().isoformat(),
        "parcours": [
            _obj_to_dict(p, ["id", "title", "description", "deadline", "category", "status"])
            for p in Parcours.query.all()
        ],
        "jalons": [
            _obj_to_dict(j, ["id", "parcours_id", "title", "checked", "checked_date",
                             "completion_threshold", "last_alert_at_count"])
            for j in Jalon.query.all()
        ],
        "quests": [
            _obj_to_dict(q, ["id", "title", "jalon_id", "type", "status", "last_completed",
                             "description", "location", "deadline"])
            for q in Quest.query.all()
        ],
        "quest_completions": [
            _obj_to_dict(qc, ["id", "quest_id", "jalon_id", "completed_date"])
            for qc in QuestCompletion.query.all()
        ],
        "player": [
            _obj_to_dict(p, ["id", "streak", "fatigue", "momentum", "completed_quests"])
            for p in Player.query.all()
        ],
        "time_system": [
            _obj_to_dict(t, ["id", "current_day", "current_week", "current_month", "total_days_played"])
            for t in TimeSystem.query.all()
        ],
        "foundations": [
            _obj_to_dict(f, ["id", "title", "type", "weight", "status", "last_done"])
            for f in Foundation.query.all()
        ],
        "foundation_validations": [
            _obj_to_dict(fv, ["id", "foundation_id", "date"])
            for fv in FoundationValidation.query.all()
        ],
        "daily_snapshots": [
            _obj_to_dict(s, ["id", "date", "fatigue", "momentum", "streak",
                             "daily_core_score", "life_score_global", "discipline_score"])
            for s in DailySnapshot.query.all()
        ],
    }

    filename = f"levelup-backup-{date.today().isoformat()}.json"
    body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(
        body,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
