from flask import Blueprint, render_template
from core import analytics

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.route("/")
def index():
    heatmap = analytics.heatmap_completions(days=90)
    jalons = analytics.jalons_timeline()
    snapshots = analytics.snapshot_series(days=30)

    return render_template(
        "analytics.html", active="analytics",
        heatmap=heatmap, jalons=jalons, snapshots=snapshots,
    )