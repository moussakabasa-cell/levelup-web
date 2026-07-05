"""
Migration additive : ajoute 2 colonnes à la table jalons pour le système
d'alerte "prêt à cocher" (seuil configurable + palier de la dernière
alerte émise). Aucune donnée existante touchée.

Usage :
    python add_threshold_columns.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"
"""
import sys
import psycopg2


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

    if column_exists(cur, "jalons", "completion_threshold"):
        print("[déjà fait] jalons.completion_threshold existe déjà")
    else:
        cur.execute("ALTER TABLE jalons ADD COLUMN completion_threshold INTEGER;")
        print("[ok] jalons.completion_threshold ajoutée")

    if column_exists(cur, "jalons", "last_alert_at_count"):
        print("[déjà fait] jalons.last_alert_at_count existe déjà")
    else:
        cur.execute("ALTER TABLE jalons ADD COLUMN last_alert_at_count INTEGER DEFAULT 0;")
        print("[ok] jalons.last_alert_at_count ajoutée")

    conn.commit()
    cur.close()
    conn.close()
    print("\nMigration terminée.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_threshold_columns.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)
    migrate(sys.argv[1])
