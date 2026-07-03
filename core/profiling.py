"""Port de profiling_system.c."""
from models import Skill, Player
from core.queries import get_skill_quests_this_week

IRREGULAR = "IRREGULIER"
SYSTEMS = "DOMINANCE SYSTEMES"
BALANCED = "EQUILIBRE"


def generate_profile() -> dict:
    player = Player.get()
    skills = Skill.query.all()

    # régularité basée sur le streak
    if player.streak >= 7:
        regularity_score = 3
    elif player.streak >= 3:
        regularity_score = 2
    else:
        regularity_score = 1

    # skill dominant = plus de complétions cette semaine
    dominant_skill = None
    max_count = 0
    for s in skills:
        count = get_skill_quests_this_week(s.id)
        if count > max_count:
            max_count = count
            dominant_skill = s.name

    # stagnation : un seul skill actif alors qu'il y en a plusieurs
    active_skills = sum(1 for s in skills if get_skill_quests_this_week(s.id) > 0)
    stagnation_detected = active_skills == 1 and len(skills) > 1

    if regularity_score == 1:
        profile_type = IRREGULAR
    elif active_skills <= 1:
        profile_type = SYSTEMS
    else:
        profile_type = BALANCED

    return {
        "type": profile_type,
        "dominant_skill": dominant_skill,
        "regularity_score": regularity_score,
        "fatigue_level": player.fatigue,
        "stagnation_detected": stagnation_detected,
    }


REGULARITY_LABELS = {3: "EXCELLENTE", 2: "BONNE", 1: "FAIBLE"}
