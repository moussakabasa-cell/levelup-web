"""
Migration unique de skills.db (SQLite local) vers Postgres (Railway).

Usage (depuis le dossier levelup, en local, PAS sur Railway) :
    python migrate_to_postgres.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"

Le script :
1. lit chaque table de ton skills.db local
2. vide la table correspondante côté Postgres (elle est vide de toute façon,
   mais ça rend le script rejouable sans dupliquer si jamais tu le relances)
3. réinsère les lignes avec leurs IDs d'origine (pour garder les liens
   skill_id / quest_id / ltg_id intacts)
4. resynchronise les compteurs auto-increment Postgres pour que les
   prochains ajouts (depuis l'app web) partent bien après le dernier ID migré
"""
import sqlite3
import sys

import psycopg2

# Ordre important : tables parentes avant tables enfants (clés étrangères)
TABLES_IN_ORDER = [
    "skills",
    "quests",
    "player",
    "rules",
    "time_system",
    "xp_history",
    "synergies",
    "long_term_goals",
    "ltg_sub_objectives",
    "skill_milestones",
    "quest_completions",
    "goals",
    "foundations",
]


def migrate(sqlite_path: str, postgres_url: str):
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(postgres_url)
    pg_cur = pg_conn.cursor()

    for table in TABLES_IN_ORDER:
        try:
            rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError:
            print(f"[skip] table {table} absente du skills.db source")
            continue

        if not rows:
            print(f"[vide] {table} — rien à migrer")
            continue

        columns = rows[0].keys()
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        # on vide la table Postgres avant de réinsérer (idempotent si relancé)
        pg_cur.execute(f"DELETE FROM {table};")

        insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
        for row in rows:
            values = []
            for c in columns:
                v = row[c]
                # Convention du C : skill_id=0 veut dire "aucun skill".
                # Postgres a une vraie contrainte de clé étrangère (contrairement
                # à SQLite qui ne la vérifiait pas) -> il faut NULL, pas 0.
                if c == "skill_id" and v == 0:
                    v = None
                values.append(v)
            pg_cur.execute(insert_sql, tuple(values))

        # resynchronise le compteur auto-increment sur le max(id) migré
        if "id" in columns:
            pg_cur.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1), true);"
            )

        print(f"[ok]   {table} — {len(rows)} lignes migrées")

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()
    print("\nMigration terminée.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_postgres.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)

    migrate("skills.db", sys.argv[1])
