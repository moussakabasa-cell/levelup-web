"""
Modèles SQLAlchemy — schéma identique à skills.db (vérifié colonne par colonne
sur ta base réelle, pas sur la doc).

Tables ACTIVES (utilisées par le moteur C actuel, portées avec la logique) :
    Skill, SkillMilestone, Quest, QuestCompletion, Player, TimeSystem,
    LongTermGoal, LtgSubObjective, Foundation

Tables LEGACY (présentes dans skills.db, plus utilisées par le moteur
depuis le pivot Phase 9 — reliquats du système XP/niveaux/synergies) :
    Rules, XpHistory, Synergy, Goal
Elles sont modélisées pour que ta DB existante s'importe sans erreur,
mais aucune route/logique n'écrit dedans.
"""
from datetime import date
from extensions import db


# ============================================================
#   ACTIF — SKILLS & JALONS
# ============================================================

class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    level = db.Column(db.Integer)      # legacy, plus utilisé (résidu pré-pivot)
    xp = db.Column(db.Integer)         # legacy, plus utilisé (résidu pré-pivot)
    category = db.Column(db.Text)      # ACADEMIQUE / PROJET / PERSO / HUMAIN

    milestones = db.relationship(
        "SkillMilestone", backref="skill", cascade="all, delete-orphan"
    )
    quests = db.relationship("Quest", backref="skill")

    CATEGORIES = ["ACADEMIQUE", "PROJET", "PERSO", "HUMAIN"]

    def milestone_count(self):
        return len(self.milestones)

    def checked_milestone_count(self):
        return sum(1 for m in self.milestones if m.checked)


class SkillMilestone(db.Model):
    __tablename__ = "skill_milestones"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    title = db.Column(db.Text)
    checked = db.Column(db.Integer, default=0)
    checked_date = db.Column(db.Text, default="")


# ============================================================
#   ACTIF — QUÊTES
# ============================================================

class Quest(db.Model):
    __tablename__ = "quests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    type = db.Column(db.Text)          # DAILY / PONCTUELLE
    status = db.Column(db.Integer, default=0)   # 0=AVAILABLE, 1=COMPLETED
    last_completed = db.Column(db.Text, default="NEVER")

    TYPES = ["DAILY", "PONCTUELLE"]
    STATUS_AVAILABLE = 0
    STATUS_COMPLETED = 1


class QuestCompletion(db.Model):
    """Source de vérité pour les analytics (quest_completions).
    C'est CETTE table, pas le champ quests.status, qui alimente
    discipline score, dérive, quêtes de la semaine, etc."""
    __tablename__ = "quest_completions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quest_id = db.Column(db.Integer)
    skill_id = db.Column(db.Integer)
    completed_date = db.Column(db.Text)   # YYYY-MM-DD


# ============================================================
#   ACTIF — PLAYER (état global, ligne unique id=1)
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
        """Équivalent load_player — retourne la ligne id=1, la crée si absente."""
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
#   ACTIF — TIME SYSTEM (ligne unique id=1)
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
#   ACTIF — OBJECTIFS LONG TERME
# ============================================================

class LongTermGoal(db.Model):
    __tablename__ = "long_term_goals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    skill_id = db.Column(db.Integer)       # colonne présente en DB, jamais peuplée par le C actuel
    target_level = db.Column(db.Integer)   # idem — résidu de schéma, pas utilisé
    deadline = db.Column(db.Text)          # YYYY-MM-DD
    status = db.Column(db.Integer)         # voir LtgStatus ci-dessous

    sub_objectives = db.relationship(
        "LtgSubObjective", backref="ltg", cascade="all, delete-orphan"
    )

    # Statuts — mêmes valeurs que l'enum C LtgStatus
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
        INCONNU: "INCONNU",
    }


class LtgSubObjective(db.Model):
    __tablename__ = "ltg_sub_objectives"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ltg_id = db.Column(db.Integer, db.ForeignKey("long_term_goals.id"))
    title = db.Column(db.Text)
    checked = db.Column(db.Integer, default=0)
    checked_date = db.Column(db.Text, default="")


# ============================================================
#   ACTIF — DAILY CORE (fondations)
# ============================================================

class Foundation(db.Model):
    __tablename__ = "foundations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    type = db.Column(db.Text)      # SANTE / MENTAL / SPIRITUEL / TRAVAIL / SOCIAL
    weight = db.Column(db.Integer)         # 1-10
    status = db.Column(db.Integer, default=0)  # 0=PENDING, 1=DONE, 2=SKIPPED
    last_done = db.Column(db.Text, default="")

    TYPES = ["SANTE", "MENTAL", "SPIRITUEL", "TRAVAIL", "SOCIAL"]
    PENDING = 0
    DONE = 1
    SKIPPED = 2


# ============================================================
#   LEGACY — présent dans le schéma, non utilisé par le moteur
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
    """Équivalent de strftime('%Y-%m-%d') utilisé partout côté C."""
    return date.today().isoformat()
