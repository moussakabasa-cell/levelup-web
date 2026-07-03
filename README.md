# LevelUp — version Python/Flask

Port du moteur C (`levelup/src/*.c`) vers Flask, un seul projet Python
déployable sur Railway et accessible depuis ton téléphone.

## 1. Lancer en local

```bash
pip install -r requirements.txt

# Récupère tes vraies données : copie ton skills.db actuel à la racine
cp /chemin/vers/ton/skills.db .

python app.py
# -> http://localhost:5000
```

Au premier lancement, `db.create_all()` ne crée que les tables manquantes —
si tu copies ton `skills.db` existant, tes skills/quêtes/LTG/fondations/
jalons sont réutilisés tels quels (même schéma, vérifié colonne par colonne).

## 2. Déployer sur Railway

1. Push ce dossier sur un repo GitHub.
2. Sur Railway : New Project → Deploy from GitHub repo.
3. Railway détecte `railway.toml` / `Procfile` automatiquement (Nixpacks).
4. Variables d'environnement à définir dans Railway :
   - `SECRET_KEY` (obligatoire en prod)
   - `TZ` = `Europe/Paris` (déjà la valeur par défaut)
   - `DATABASE_URL` — laisse vide pour rester sur SQLite (fichier local,
     **non persistant** entre déploiements sur Railway sans volume), ou
     ajoute le plugin Postgres Railway pour une vraie persistance.
5. Pour importer tes données existantes : le plus simple est de committer
   ton `skills.db` dans le repo une seule fois (retire-le du `.gitignore`
   pour ce commit), ou d'exposer une route d'admin temporaire pour uploader
   le fichier — dis-moi si tu veux que je l'ajoute.

**Important — SQLite sur Railway** : le filesystem est éphémère par défaut
(perdu à chaque redeploy). Pour un tracker que tu utilises au quotidien sur
plusieurs mois, **passe sur Postgres** (plugin gratuit Railway) dès que
possible. Le code ne change pas — seule `DATABASE_URL` change.

## 3. Ce qui a été porté à l'identique

- Score fondations : `(poids_done/poids_total)*100`, validé si ≥80
- Impact fondations sur player : ≥80 → momentum+10/fatigue-5 ; <50 → fatigue+5/momentum-5
- New day : reset fondations + fatigue×0.7, momentum×0.8 (décroissance, pas un reset à zéro)
- Discipline score 7j : jours distincts avec ≥1 quête complétée, /7×100
- Life score : académique 30% + projet 25% + perso 15% + humain 10% + fondations 20%
- Les 7 alertes du dashboard (fatigue, streak, fondations, stagnation, skill inactif, burnout, incohérence LTG)
- Statuts LTG (y compris le comportement "tous sous-objectifs cochés → toujours COMPLETE")
- Récompenses quête complétée : streak+1, momentum+10, fatigue+4
- Recommandations : top 3 quêtes disponibles (version simple, celle qui matche ton schéma)

## 4. Écarts volontaires par rapport au C

- **Reset quotidien** : passé d'un check-au-lancement (`main.c`) à un job
  planifié à minuit (`scheduler.py`, APScheduler). Plus fiable pour une app
  web que tu n'ouvres pas à heure fixe.
- **Session (`session.c`)** : abandonnée (stateless par nature en web).
  Les stats "aujourd'hui/cette semaine" viennent directement de
  `quest_completions`.
- **Event system** : remplacé par `flash()` Flask.
- **XP/niveaux joueur** (résidu dans `player.c`/`skill.c`) : pas porté,
  conforme au pivot Phase 9 déjà acté — plus rien ne les appelait dans ton
  code actuel.
- **Bug corrigé** : dans `dashboard.c`, l'alerte de cohérence LTG comparait
  `status != 2` en commentant `/* 2 = COMPLETE */`, mais dans l'enum réel
  `LTG_COMPLETE` vaut 3 (`EN_AVANCE=0, DANS_LES_TEMPS=1, EN_RETARD=2,
  COMPLETE=3`). Le C excluait donc par erreur les LTG "EN RETARD" au lieu
  des LTG "COMPLETE". Corrigé pour matcher l'intention du commentaire.
- **recommendation.c** : deux versions existaient dans tes fichiers (une
  simple, une avec scoring difficulty/skill_ids qui ne correspond plus à
  ton schéma `Quest` actuel). Porté la version simple, confirmée par toi.

## 5. Ce qui reste à faire (pas encore branché)

- Import/upload de ton `skills.db` existant depuis l'interface (actuellement
  manuel via `cp` ou commit Git)
- Auth basique si tu veux protéger l'accès (actuellement l'app est ouverte
  à quiconque a l'URL Railway)
- `--workers 1` dans le Procfile est volontaire : APScheduler tourne en
  process, plusieurs workers gunicorn dupliqueraient le reset quotidien.
