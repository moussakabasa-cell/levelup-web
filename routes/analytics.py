from flask import Blueprint, render_template
from core import analytics

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.route("/")
def index():
    heatmap = analytics.heatmap_completions(days=90)
    jalons = analytics.jalons_timeline()
    snapshots = analytics.snapshot_series(days=30)
    foundation_rates = analytics.foundation_validation_rates(days=30)
    categories = analytics.quests_by_category(days=30)

    return render_template(
        "analytics.html", active="analytics",
        heatmap=heatmap, jalons=jalons, snapshots=snapshots,
        foundation_rates=foundation_rates, categories=categories,
    )
