"""
Modèles SQLAlchemy — schéma UNIFIÉ (v2) suite au retour d'expérience de Moks.

Changement structurel majeur vs v1 :
    Skill + SkillMilestone + LongTermGoal + LtgSubObjective
    -> fusionnés en Parcours + Jalon (un seul système à jalons,
       avec une deadline optionnelle : null = compétence infinie type
       "skill" d'origine, remplie = projet borné type "LTG" d'origine)

    Quest.skill_id -> Quest.jalon_id (une quête pointe vers UN jalon
    précis, pas vers tout un skill — plus de granularité, plus de sens)

    "Parcours" plutôt que "Objectif" : le mot "objectif" suggère une fin,
    alors que le modèle couvre aussi des compétences sans fin (anglais,
    spiritualité...). "Parcours" reste neutre, avec ou sans deadline.

Tables LEGACY (résidu pré-pivot Phase 9, toujours non utilisées) :
    Rules, XpHistory, Synergy, Goal
"""
from datetime import date
from extensions import db


# ============================================================
#   OBJECTIF + JALON (fusion Skill/LTG)
# ============================================================

class Parcours(db.Model):
    __tablename__ = "parcours"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Text)          # YYYY-MM-DD, NULL = pas de deadline (compétence infinie)
    category = db.Column(db.Text)          # ACADEMIQUE/PROJET/PERSO/HUMAIN, optionnelle
    status = db.Column(db.Integer, default=4)   # voir constantes ci-dessous, pertinent seulement si deadline non-null

    jalons = db.relationship(
        "Jalon", backref="parcours", cascade="all, delete-orphan",
        order_by="Jalon.id",
    )

    CATEGORIES = [
        "ACADEMIQUE", "PROJET", "PERSO", "HUMAIN",
        "SANTE", "SPIRITUEL", "FINANCIER", "SOCIAL",
    ]

    # Statuts (mêmes valeurs que l'ancien LtgStatus, gardées pour compat)
    EN_AVANCE = 0
    DANS_LES_TEMPS = 1
    EN_RETARD = 2
    COMPLETE = 3
    INCONNU = 4

    STATUS_LABELS = {
        EN_AVANCE: "EN AVANCE",
        DANS_LES_TEMPS: "DANS LES TEMPS",
        EN_RETARD: "EN RETARD",
        COMPLETE: "COMPLETE",
        INCONNU: "EN COURS",
    }

    def is_perpetual(self) -> bool:
        """True si pas de deadline — équivalent d'un ancien 'skill'."""
        return not self.deadline

    def jalon_count(self):
        return len(self.jalons)

    def checked_jalon_count(self):
        return sum(1 for j in self.jalons if j.checked)


class Jalon(db.Model):
    __tablename__ = "jalons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parcours_id = db.Column(db.Integer, db.ForeignKey("parcours.id"), nullable=False)
    title = db.Column(db.Text, nullable=False)
    checked = db.Column(db.Integer, default=0)
    checked_date = db.Column(db.Text, default="")

    quests = db.relationship("Quest", backref="jalon")


# ============================================================
#   QUÊTES
# ============================================================

class Quest(db.Model):
    __tablename__ = "quests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    jalon_id = db.Column(db.Integer, db.ForeignKey("jalons.id"))   # optionnel
    type = db.Column(db.Text)          # DAILY / PONCTUELLE
    status = db.Column(db.Integer, default=0)   # 0=AVAILABLE, 1=COMPLETED
    last_completed = db.Column(db.Text, default="NEVER")
    description = db.Column(db.Text)              # optionnelle, tous types
    location = db.Column(db.Text)                 # optionnelle, surtout PONCTUELLE
    deadline = db.Column(db.Text)                  # YYYY-MM-DD, optionnelle, surtout PONCTUELLE

    TYPES = ["DAILY", "PONCTUELLE"]
    STATUS_AVAILABLE = 0
    STATUS_COMPLETED = 1


class QuestCompletion(db.Model):
    """Source de vérité pour les analytics — jalon_id dénormalisé au
    moment de la complétion (pas de FK stricte : garde l'historique même
    si le jalon est supprimé ensuite)."""
    __tablename__ = "quest_completions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quest_id = db.Column(db.Integer)
    jalon_id = db.Column(db.Integer)
    completed_date = db.Column(db.Text)   # YYYY-MM-DD


# ============================================================
#   PLAYER (état global, ligne unique id=1)
# ============================================================

class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(db.Integer, primary_key=True)   # toujours 1
    level = db.Column(db.Integer, default=1)                 # legacy
    current_xp = db.Column(db.Integer, default=0)            # legacy
    total_xp = db.Column(db.Integer, default=0)              # legacy
    completed_quests = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    fatigue = db.Column(db.Integer, default=0)
    momentum = db.Column(db.Integer, default=0)

    @staticmethod
    def get():
        player = Player.query.get(1)
        if player is None:
            player = Player(
                id=1, level=1, current_xp=0, total_xp=0,
                completed_quests=0, streak=0, fatigue=0, momentum=0,
            )
            db.session.add(player)
            db.session.commit()
        return player


# ============================================================
#   TIME SYSTEM (ligne unique id=1)
# ============================================================

class TimeSystem(db.Model):
    __tablename__ = "time_system"

    id = db.Column(db.Integer, primary_key=True)   # toujours 1
    current_day = db.Column(db.Integer, default=1)
    current_week = db.Column(db.Integer, default=1)
    current_month = db.Column(db.Integer, default=1)
    total_days_played = db.Column(db.Integer, default=0)

    @staticmethod
    def get():
        ts = TimeSystem.query.get(1)
        if ts is None:
            ts = TimeSystem(
                id=1, current_day=1, current_week=1,
                current_month=1, total_days_played=0,
            )
            db.session.add(ts)
            db.session.commit()
        return ts


# ============================================================
#   DAILY CORE (fondations)
# ============================================================

class Foundation(db.Model):
    __tablename__ = "foundations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    type = db.Column(db.Text)
    weight = db.Column(db.Integer)
    status = db.Column(db.Integer, default=0)
    last_done = db.Column(db.Text, default="")

    TYPES = ["SANTE", "MENTAL", "SPIRITUEL", "TRAVAIL", "SOCIAL"]
    PENDING = 0
    DONE = 1
    SKIPPED = 2


# ============================================================
#   LEGACY — non utilisé par le moteur, gardé pour compat schéma
# ============================================================

class Rules(db.Model):
    __tablename__ = "rules"
    id = db.Column(db.Integer, primary_key=True)
    streak_bonus_3 = db.Column(db.Integer)
    streak_bonus_6 = db.Column(db.Integer)
    streak_bonus_10 = db.Column(db.Integer)
    fatigue_penalty_20 = db.Column(db.Integer)
    fatigue_penalty_50 = db.Column(db.Integer)
    fatigue_penalty_100 = db.Column(db.Integer)
    momentum_bonus_20 = db.Column(db.Integer)
    momentum_bonus_50 = db.Column(db.Integer)
    momentum_bonus_100 = db.Column(db.Integer)
    player_xp_ratio = db.Column(db.Float)


class XpHistory(db.Model):
    __tablename__ = "xp_history"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_id = db.Column(db.Integer)
    quest_id = db.Column(db.Integer)
    xp_amount = db.Column(db.Integer)
    timestamp = db.Column(db.Text)


class Synergy(db.Model):
    __tablename__ = "synergies"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_skill_id = db.Column(db.Integer)
    target_skill_id = db.Column(db.Integer)
    bonus_ratio = db.Column(db.Float)
    description = db.Column(db.Text)


class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    quest_ids = db.Column(db.Text)
    quest_count = db.Column(db.Integer)
    xp_bonus = db.Column(db.Integer)
    status = db.Column(db.Integer)


def today_str() -> str:
    return date.today().isoformat()
