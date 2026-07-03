import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    # Railway fournit DATABASE_URL pour Postgres si tu ajoutes le plugin.
    # Sinon on retombe sur SQLite (le même fichier skills.db que le C).
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'skills.db')}",
    )
    # Railway/Heroku donnent parfois "postgres://" — SQLAlchemy veut "postgresql://"
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fuseau horaire pour le reset quotidien (minuit local, pas minuit UTC)
    TIMEZONE = os.environ.get("TZ", "Europe/Paris")
