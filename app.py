import secrets
from flask import Flask, request, Response
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    def check_auth(username, password):
        return (
            secrets.compare_digest(username, app.config["APP_USERNAME"])
            and secrets.compare_digest(password, app.config["APP_PASSWORD"])
        )

    @app.before_request
    def require_auth():
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Accès restreint.", 401,
                {"WWW-Authenticate": 'Basic realm="LevelUp"'},
            )

    db.init_app(app)

    from routes.dashboard import bp as dashboard_bp
    from routes.quests import bp as quests_bp
    from routes.parcours import bp as parcours_bp
    from routes.daily_core import bp as daily_core_bp
    from routes.analytics import bp as analytics_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(quests_bp)
    app.register_blueprint(parcours_bp)
    app.register_blueprint(daily_core_bp)
    app.register_blueprint(analytics_bp)

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
