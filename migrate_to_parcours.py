"""
Migration Postgres vers le schéma final Parcours + Jalon.

Ce script détecte automatiquement où en est ta base et fait ce qu'il faut :

  CAS A — tu n'as encore rien migré (tables skills/quests/long_term_goals
          d'origine encore présentes sous leur nom) :
          migration complète v1 -> Parcours/Jalon en une fois.
          (Ce script REMPLACE le migrate_unify_objectifs.py donné avant —
          ne lance pas l'ancien, lance uniquement celui-ci.)

  CAS B — tu avais déjà lancé l'ancien migrate_unify_objectifs.py (table
          `objectifs` déjà créée et peuplée) :
          simple renommage objectifs->parcours, jalons.objectif_id->parcours_id,
          aucune donnée retouchée.

  CAS C — déjà entièrement migré (table `parcours` existe) :
          ne fait rien, te le signale.

Dans tous les cas, rien n'est perdu : les anciennes tables (skills,
quests d'origine, etc.) sont renommées en _legacy_*, jamais supprimées.

Usage (depuis le dossier levelup, en local) :
    python migrate_to_parcours.py "postgresql://postgres:xxx@xxx.proxy.rlwy.net:xxxx/railway"
"""
import os
import sys
import psycopg2


LEGACY_RENAMES = [
    ("skills", "_legacy_skills"),
    ("skill_milestones", "_legacy_skill_milestones"),
    ("long_term_goals", "_legacy_long_term_goals"),
    ("ltg_sub_objectives", "_legacy_ltg_sub_objectives"),
    ("quests", "_legacy_quests"),
    ("quest_completions", "_legacy_quest_completions"),
]


def table_exists(cur, name):
    cur.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
        (name,),
    )
    return cur.fetchone()[0]


def column_exists(cur, table, column):
    cur.execute(
        "SELECT EXISTS (SELECT FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s)",
        (table, column),
    )
    return cur.fetchone()[0]


def migrate_full_v1(cur, postgres_url):
    """CAS A : migration complète depuis skills/LTG d'origine."""
    for old, new in LEGACY_RENAMES:
        if table_exists(cur, old):
            cur.execute(f"ALTER TABLE {old} RENAME TO {new};")
            print(f"[renommé] {old} -> {new}")
        else:
            print(f"[absent] {old} n'existe pas, rien à renommer")

    os.environ["DATABASE_URL"] = postgres_url
    from app import create_app
    app = create_app()
    print("[ok] nouvelles tables créées (parcours, jalons, quests, quest_completions)")

    with app.app_context():
        from extensions import db
        from models import Parcours, Jalon, Quest, QuestCompletion

        skill_to_parcours = {}
        ltg_to_parcours = {}

        cur.execute("SELECT id, name, category FROM _legacy_skills;")
        for old_id, name, category in cur.fetchall():
            p = Parcours(title=name, deadline=None, category=category, status=Parcours.INCONNU)
            db.session.add(p)
            db.session.flush()
            skill_to_parcours[old_id] = p.id
        db.session.commit()
        print(f"[ok] {len(skill_to_parcours)} skills -> parcours sans deadline")

        cur.execute("SELECT skill_id, title, checked, checked_date FROM _legacy_skill_milestones;")
        count = 0
        for skill_id, title, checked, checked_date in cur.fetchall():
            if skill_id not in skill_to_parcours:
                continue
            db.session.add(Jalon(
                parcours_id=skill_to_parcours[skill_id], title=title,
                checked=checked or 0, checked_date=checked_date or "",
            ))
            count += 1
        db.session.commit()
        print(f"[ok] {count} jalons migrés depuis skill_milestones")

        cur.execute("SELECT id, title, deadline, status FROM _legacy_long_term_goals;")
        count = 0
        for old_id, title, deadline, status in cur.fetchall():
            p = Parcours(title=title, deadline=deadline, category=None, status=status)
            db.session.add(p)
            db.session.flush()
            ltg_to_parcours[old_id] = p.id
            count += 1
        db.session.commit()
        print(f"[ok] {count} objectifs long terme -> parcours avec deadline")

        cur.execute("SELECT ltg_id, title, checked, checked_date FROM _legacy_ltg_sub_objectives;")
        count = 0
        for ltg_id, title, checked, checked_date in cur.fetchall():
            if ltg_id not in ltg_to_parcours:
                continue
            db.session.add(Jalon(
                parcours_id=ltg_to_parcours[ltg_id], title=title,
                checked=checked or 0, checked_date=checked_date or "",
            ))
            count += 1
        db.session.commit()
        print(f"[ok] {count} jalons migrés depuis ltg_sub_objectives")

        cur.execute("SELECT id, title, type, status, last_completed FROM _legacy_quests;")
        quest_id_map = {}
        count = 0
        for old_id, title, qtype, status, last_completed in cur.fetchall():
            q = Quest(title=title, jalon_id=None, type=qtype, status=status, last_completed=last_completed)
            db.session.add(q)
            db.session.flush()
            quest_id_map[old_id] = q.id
            count += 1
        db.session.commit()
        print(f"[ok] {count} quêtes migrées (lien skill abandonné, sans correspondance jalon fiable)")

        cur.execute("SELECT quest_id, completed_date FROM _legacy_quest_completions;")
        count = 0
        for old_quest_id, completed_date in cur.fetchall():
            new_quest_id = quest_id_map.get(old_quest_id, old_quest_id)
            db.session.add(QuestCompletion(quest_id=new_quest_id, jalon_id=None, completed_date=completed_date))
            count += 1
        db.session.commit()
        print(f"[ok] {count} complétions historiques migrées")


def migrate_rename_only(cur):
    """CAS B : table `objectifs` déjà créée par l'ancien script, simple renommage."""
    cur.execute("ALTER TABLE objectifs RENAME TO parcours;")
    print("[ok] table objectifs -> parcours")

    if column_exists(cur, "jalons", "objectif_id"):
        cur.execute("ALTER TABLE jalons RENAME COLUMN objectif_id TO parcours_id;")
        print("[ok] colonne jalons.objectif_id -> jalons.parcours_id")


def migrate_quests_resume(cur, postgres_url):
    """CAS D : la migration a été interrompue en cours de route (connexion
    coupée pendant les quêtes/complétions) — parcours et jalons sont déjà
    committés, on reprend UNIQUEMENT la partie quêtes, sans re-toucher au
    reste (pas de doublons)."""
    os.environ["DATABASE_URL"] = postgres_url
    from app import create_app
    app = create_app()

    with app.app_context():
        from extensions import db
        from models import Quest, QuestCompletion

        cur.execute("SELECT id, title, type, status, last_completed FROM _legacy_quests;")
        quest_id_map = {}
        count = 0
        for old_id, title, qtype, status, last_completed in cur.fetchall():
            q = Quest(title=title, jalon_id=None, type=qtype, status=status, last_completed=last_completed)
            db.session.add(q)
            db.session.flush()
            quest_id_map[old_id] = q.id
            count += 1
        db.session.commit()
        print(f"[ok] {count} quêtes migrées (reprise)")

        cur.execute("SELECT quest_id, completed_date FROM _legacy_quest_completions;")
        count = 0
        for old_quest_id, completed_date in cur.fetchall():
            new_quest_id = quest_id_map.get(old_quest_id, old_quest_id)
            db.session.add(QuestCompletion(quest_id=new_quest_id, jalon_id=None, completed_date=completed_date))
            count += 1
        db.session.commit()
        print(f"[ok] {count} complétions historiques migrées (reprise)")


def migrate(postgres_url: str):
    conn = psycopg2.connect(postgres_url)
    cur = conn.cursor()

    has_parcours = table_exists(cur, "parcours")
    has_objectifs = table_exists(cur, "objectifs")
    has_skills = table_exists(cur, "skills")
    has_legacy_quests = table_exists(cur, "_legacy_quests")

    if has_parcours and has_legacy_quests:
        cur.execute("SELECT COUNT(*) FROM quests;")
        quests_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM _legacy_quests;")
        legacy_count = cur.fetchone()[0]

        if quests_count < legacy_count:
            print(f"État détecté : migration interrompue ({quests_count}/{legacy_count} quêtes migrées). Reprise...")
            migrate_quests_resume(cur, postgres_url)
        else:
            print("[déjà fait] parcours + quêtes déjà entièrement migrés — rien à faire.")
    elif has_parcours:
        print("[déjà fait] la table `parcours` existe déjà — rien à migrer.")
    elif has_objectifs:
        print("État détecté : migration intermédiaire déjà faite (table `objectifs` trouvée).")
        migrate_rename_only(cur)
        conn.commit()
    elif has_skills:
        print("État détecté : schéma d'origine (table `skills` trouvée). Migration complète en cours...")
        migrate_full_v1(cur, postgres_url)
    else:
        print("Aucun état reconnu (ni skills, ni objectifs, ni parcours). Vérifie manuellement.")

    cur.close()
    conn.close()
    print("\nMigration terminée.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_parcours.py <DATABASE_PUBLIC_URL>")
        sys.exit(1)
    migrate(sys.argv[1])
