"""
Migration additive : ajoute description/location/deadline à la table quests.
Aucune donnée existante touchée — juste 3 nouvelles colonnes vides (NULL)
pour tes quêtes déjà en base.

Usage :
    python add_quest_fields.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"
"""
import sys
import psycopg2


COLUMNS = [
    ("description", "TEXT"),
    ("location", "TEXT"),
    ("deadline", "TEXT"),
]


def column_exists(cur, table, column):
    cur.execute(
        "SELECT EXISTS (SELECT FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s)",
        (table, column),
    )
    return cur.fetchone()[0]


def migrate(postgres_url: str):
    conn = psycopg2.connect(postgres_url)
    cur = conn.cursor()

    for col, coltype in COLUMNS:
        if column_exists(cur, "quests", col):
            print(f"[déjà fait] quests.{col} existe déjà")
        else:
            cur.execute(f"ALTER TABLE quests ADD COLUMN {col} {coltype};")
            print(f"[ok] quests.{col} ajoutée")

    conn.commit()
    cur.close()
    conn.close()
    print("\nMigration terminée.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_quest_fields.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)
    migrate(sys.argv[1])
