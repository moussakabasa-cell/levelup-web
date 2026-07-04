"""Profil joueur — dominant = parcours avec le plus de complétions cette semaine."""
from models import Parcours, Player
from core.queries import get_parcours_quests_this_week

IRREGULAR = "IRREGULIER"
SYSTEMS = "DOMINANCE SYSTEMES"
BALANCED = "EQUILIBRE"


def generate_profile() -> dict:
    player = Player.get()
    items = Parcours.query.all()

    if player.streak >= 7:
        regularity_score = 3
    elif player.streak >= 3:
        regularity_score = 2
    else:
        regularity_score = 1

    dominant = None
    max_count = 0
    for p in items:
        count = get_parcours_quests_this_week(p.id)
        if count > max_count:
            max_count = count
            dominant = p.title

    active = sum(1 for p in items if get_parcours_quests_this_week(p.id) > 0)
    stagnation_detected = active == 1 and len(items) > 1

    if regularity_score == 1:
        profile_type = IRREGULAR
    elif active <= 1:
        profile_type = SYSTEMS
    else:
        profile_type = BALANCED

    return {
        "type": profile_type,
        "dominant_parcours": dominant,
        "regularity_score": regularity_score,
        "fatigue_level": player.fatigue,
        "stagnation_detected": stagnation_detected,
    }


REGULARITY_LABELS = {3: "EXCELLENTE", 2: "BONNE", 1: "FAIBLE"}
