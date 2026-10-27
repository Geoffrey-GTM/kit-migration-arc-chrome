# Instructions pour Claude

Ce dépôt contient un kit qui migre les espaces Arc vers Google Chrome sur Mac : favoris, onglets épinglés, onglets ouverts, historique et extensions. On te demandera surtout de **faire la migration** pour quelqu'un, parfois de **modifier le kit**.

Parle en français, tutoie, fais des phrases courtes : la personne n'est pas forcément technique.

## Faire la migration

Suis ces étapes dans l'ordre. Ne lance jamais la migration réelle avant l'étape 5.

### 1. Vérifier où tu tournes (sans poser de question)

- `uname` doit répondre `Darwin` et `~/Library/Application Support/Arc/StorableSidebar.json` doit exister. Sinon, tu n'es pas sur le Mac de la personne (session dans le cloud, Linux, Windows) : arrête-toi, explique que la migration doit tourner sur son Mac, avec Claude Code lancé depuis Terminal ou depuis l'app Claude en mode local, et donne-lui les commandes du README.
- `python3 --version` doit répondre. Sinon : `xcode-select --install`.
- Si une commande échoue sur `~/Library/Application Support/Google/Chrome` avec « Operation not permitted », l'app qui exécute tes commandes (Terminal, iTerm, l'app Claude…) n'a pas l'accès complet au disque. Explique le réglage : Réglages Système › Confidentialité et sécurité › Accès complet au disque, activer l'app, puis la quitter et la rouvrir.

### 2. Faire l'état des lieux (lecture seule, navigateurs ouverts acceptés)

```bash
bash migrer-arc-vers-chrome.sh --plan --mode espaces
bash diagnostic-favoris.sh
```

`--plan` liste les espaces Arc, les profils Chrome, la correspondance prévue et les favoris du compte Google, sans rien modifier dans Chrome. Résume en quelques lignes : espaces trouvés, profils Chrome, espaces sans profil du même nom, profils qui affichent des favoris de leur compte Google.

### 3. Poser les pré-questions

Pose-les en une seule fois, avec ton outil de questions à choix si tu en as un, sinon dans le chat, en t'appuyant sur l'état des lieux :

1. **Organisation** : un profil Chrome par espace Arc (à recommander si les profils existent déjà), ou tout dans un seul profil (lequel ?).
2. **Ce qui existe déjà dans Chrome** : ajouter le contenu d'Arc à côté (par défaut), ou repartir de zéro avec `--remplacer`, qui efface les favoris et l'historique des profils ciblés après les avoir sauvegardés.
3. **Rangement des onglets** (un profil par espace) : à plat dans la barre de favoris (par défaut), ou dans deux dossiers avec `--dossiers`.
4. **Espaces à exclure ou à rediriger** : liste les espaces trouvés ; pour chacun, migrer, ignorer, ou envoyer vers un profil Chrome qui porte un autre nom.

Ensuite, seulement si c'est utile :

- **Un espace n'a pas de profil Chrome du même nom** : la personne crée le profil dans Chrome, ou tu le rediriges vers un profil existant, ou tu l'ignores.
- **Des profils ont des favoris dans le compte Google** : explique qu'ils resteront affichés et que le kit n'y touche pas (README, « Des favoris qui ne viennent pas d'Arc ? »). La personne choisira, après la migration, de les masquer ou non.
- **Extensions** : ouvrir Chrome à la fin sur les pages des extensions à réinstaller, oui ou non.

### 4. Préparer

- Écris les exclusions et redirections dans `correspondance.local.txt`, une règle par ligne : `Espace Arc = ignorer` ou `Espace Arc = Profil Chrome`. Ce fichier personnel n'est jamais versionné. N'écris aucun nom d'espace ou de profil dans `correspondance.txt`, qui est suivi par Git.
- Demande à la personne de quitter Arc et Chrome avec Cmd+Q. Ne les ferme pas toi-même. Vérifie avec `pgrep -x Arc; pgrep -x "Google Chrome"` : aucune ligne affichée veut dire qu'ils sont fermés.
- Relance `--plan` avec les options choisies et montre le plan final.

### 5. Confirmer, puis lancer

Récapitule : profils Chrome touchés, ce qui sera effacé si `--remplacer`, où seront les sauvegardes (`resultat-migration/sauvegardes-chrome`). Attends un « oui » explicite, puis lance par exemple :

```bash
bash migrer-arc-vers-chrome.sh --mode espaces --remplacer --oui
```

- Ajoute `--dossiers` si la personne l'a choisi ; en mode unique, `--mode unique --profil "Nom du profil"`.
- Mets `NO_OPEN=1` devant la commande si la personne ne veut pas qu'on ouvre Chrome sur les extensions.
- Sans `--oui`, le script ne peut pas recevoir de confirmation quand il est lancé sans terminal : il s'arrête sans rien modifier.

### 6. Après la migration

- Résume `resultat-migration/resume.txt` : favoris ajoutés, historique, extensions, avertissements.
- Relance `bash diagnostic-favoris.sh` et explique ce qui vient encore du compte Google, s'il y en a.
- Rappelle ce qui reste à faire à la main : mots de passe (LISEZMOI.txt, étape 6), extensions à réinstaller, affichage de la barre de favoris (Cmd+Maj+B).
- En cas de problème, propose le retour en arrière décrit dans LISEZMOI.txt (« Revenir en arrière »).

### Ce que tu ne fais jamais

- Lancer `--remplacer` sans un accord explicite donné après le récapitulatif.
- Modifier à la main les fichiers d'Arc ou de Chrome, ou supprimer les favoris du compte Google à la place de la personne.
- Ouvrir, lire, copier ou déplacer un export de mots de passe (fichier `.csv`).
- Conseiller « Supprimer les données » sur chrome.google.com/sync : ça efface aussi les mots de passe et tout le reste du compte Google.
- Versionner, envoyer ou publier `resultat-migration/`, `correspondance.local.txt` ou toute donnée personnelle : noms d'espaces, de profils ou de clients, adresses de sites, historique.

## Modifier le kit

- Suis CONTRIBUTING.md : bibliothèque standard Python uniquement, compatible Python 3.9 ; lanceur compatible bash 3.2 ; commits au format Conventional Commits ; une ligne dans la section « Non publié » du CHANGELOG.
- Avant de proposer un commit :

  ```bash
  python3 -m unittest discover -s tests -v
  ruff check . && ruff format --check .
  shellcheck *.sh scripts/*.sh
  ```

- Les tests utilisent uniquement des données factices (`tests/fixtures.py`). Ne lance jamais le script sur les vrais navigateurs pour tester une modification.
- Toute nouvelle option doit apparaître dans `USAGE` (`migrer_arc_chrome.py`), le README, LISEZMOI.txt, ce fichier et le CHANGELOG.
