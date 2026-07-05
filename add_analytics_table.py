"""
Migration additive : crée la table daily_snapshots (historique quotidien
pour les courbes d'analytics). Aucune donnée existante touchée.

Usage :
    python add_analytics_table.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"
"""
import os
import sys


def migrate(postgres_url: str):
    os.environ["DATABASE_URL"] = postgres_url
    from app import create_app
    create_app()  # db.create_all() ne crée que les tables manquantes
    print("[ok] table daily_snapshots créée (si elle n'existait pas déjà)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_analytics_table.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)
    migrate(sys.argv[1])
