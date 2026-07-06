"""
Nettoyage des tables legacy accumulées lors des migrations successives.
On drop les tables préfixées _legacy_* qui ne servent plus à rien
(elles ont été conservées jusqu'ici par sécurité, au cas où une migration
aurait raté). Vu que les migrations ont toutes réussi et que tu utilises
l'app depuis, on peut nettoyer.

Ne touche PAS aux tables actives (parcours, jalons, quests, etc.) ni aux
tables présentes dans le schéma d'origine mais jamais utilisées (rules,
xp_history, synergies, goals — celles-là restent, elles font partie
du schéma initial et pourraient être utiles un jour).

Usage :
    python cleanup_legacy_tables.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"
"""
import sys
import psycopg2


LEGACY_TABLES_TO_DROP = [
    "_legacy_skills",
    "_legacy_skill_milestones",
    "_legacy_long_term_goals",
    "_legacy_ltg_sub_objectives",
    "_legacy_quests",
    "_legacy_quest_completions",
    "_legacy_quests_v1",
    "_legacy_quest_completions_v1",
]


def table_exists(cur, name):
    cur.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
        (name,),
    )
    return cur.fetchone()[0]


def row_count(cur, name):
    cur.execute(f"SELECT COUNT(*) FROM {name};")
    return cur.fetchone()[0]


def cleanup(postgres_url: str):
    conn = psycopg2.connect(postgres_url)
    cur = conn.cursor()

    print("Inventaire avant nettoyage :")
    to_drop = []
    for t in LEGACY_TABLES_TO_DROP:
        if table_exists(cur, t):
            n = row_count(cur, t)
            print(f"  {t:<40} {n} lignes")
            to_drop.append(t)
        else:
            print(f"  {t:<40} (absente)")

    if not to_drop:
        print("\nRien à nettoyer, la base est déjà propre.")
        return

    print(f"\nSuppression de {len(to_drop)} tables...")
    for t in to_drop:
        cur.execute(f"DROP TABLE {t};")
        print(f"  [drop] {t}")
    conn.commit()

    cur.close()
    conn.close()
    print("\nNettoyage terminé. Fais un backup avant si tu veux garder une trace de ce qui a été supprimé.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cleanup_legacy_tables.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)
    cleanup(sys.argv[1])
