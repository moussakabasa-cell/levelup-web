"""Port de player_state.c + la partie player de xp_system.c (distribute_quest_rewards)."""
from extensions import db
from models import Player


def increase_streak(player: Player):
    player.streak += 1


def increase_momentum(player: Player, amount: int):
    player.momentum += amount


def increase_fatigue(player: Player, amount: int):
    player.fatigue += amount


def reduce_fatigue(player: Player, amount: int):
    player.fatigue = max(0, player.fatigue - amount)


def reset_momentum(player: Player):
    player.momentum = 0


def reset_streak(player: Player):
    """Équivalent check_streak_decay — remet le streak à 0."""
    player.streak = 0


def decay_stats(player: Player):
    """Décroissance naturelle (pas branchée par défaut dans le C, disponible si besoin)."""
    player.fatigue = max(0, player.fatigue - 5)
    player.momentum = max(0, player.momentum - 3)


def apply_quest_completion_rewards(player: Player):
    """
    Équivalent distribute_quest_rewards (xp_system.c) — sans la partie XP,
    déjà morte côté C (plus rien ne l'appelle depuis le pivot Phase 9).
    """
    player.completed_quests += 1
    increase_streak(player)
    increase_momentum(player, 10)
    increase_fatigue(player, 4)
    db.session.commit()
