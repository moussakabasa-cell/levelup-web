from flask import Flask
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from routes.dashboard import bp as dashboard_bp
    from routes.skills import bp as skills_bp
    from routes.quests import bp as quests_bp
    from routes.ltg import bp as ltg_bp
    from routes.daily_core import bp as daily_core_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(quests_bp)
    app.register_blueprint(ltg_bp)
    app.register_blueprint(daily_core_bp)

    with app.app_context():
        # Crée les tables manquantes seulement — ne touche pas aux données
        # existantes si tu importes ton skills.db actuel.
        db.create_all()

    from scheduler import init_scheduler
    init_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
