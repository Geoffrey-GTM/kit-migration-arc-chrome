# Journal des modifications

Ce fichier liste toutes les évolutions notables du projet.

Il suit le format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les numéros de version respectent le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

## [1.1.0] - 2026-10-27

### Ajouté

- **Favoris du compte Google :** le script repère les favoris enregistrés dans le compte Google d'un profil (fichier `AccountBookmarks`), que Chrome affiche en plus de ceux du Mac. Il les signale avant la migration et en fin de migration, avec la marche à suivre pour les masquer ou les supprimer. Il n'y touche jamais.
- **Option `--diagnostic` et raccourci `diagnostic-favoris.sh` :** montrent, sans rien modifier, les favoris de chaque profil Chrome enregistrés sur ce Mac et dans le compte Google.
- **Raccourci `remplacer-tous-les-espaces.sh` :** repart de zéro (`--mode espaces --remplacer`).
- **Option `--dossiers` :** garde l'ancien rangement des onglets dans deux dossiers.
- **Sauvegarde des copies chiffrées :** les fichiers `EncryptedBookmarks*` que crée Chrome sont copiés avec `Bookmarks` avant toute écriture.
- **Tests de bout en bout** sur des données factices (`tests/`).
- **Migration guidée avec Claude :** un fichier `CLAUDE.md` fait faire à Claude Code un état des lieux, lui fait poser les questions utiles, préparer la configuration et lancer la migration seulement après accord.
- **Option `--plan` :** simulation qui affiche ce que le script ferait, sans rien modifier dans Chrome.
- **Fichier `correspondance.local.txt` :** règles personnelles, jamais versionnées, qui l'emportent sur `correspondance.txt`.

### Modifié

- En mode « un profil par espace », les onglets épinglés et ouverts arrivent **à plat dans la barre de favoris**, sans les dossiers « Arc – onglets épinglés » et « Arc – onglets ouverts ».
- Lancé sans terminal (par un autre programme), le script ne considère plus l'absence de réponse comme un « oui » : sans `--oui`, il s'arrête sans rien modifier.

### Retiré

- Le conseil d'utiliser « Supprimer les données » sur chrome.google.com/sync avant `--remplacer` : ce bouton efface aussi les mots de passe et tout le reste du compte Google.

### Corrigé

- Les commentaires en fin de ligne dans `correspondance.txt` (`Ancien client = ignorer   # …`), donnés en exemple dans le README, rendaient la règle inopérante.
- La documentation annonçait une intégration continue et des tests absents du dépôt. Les tests sont maintenant présents, et les commandes de vérification sont décrites dans le README.

## [1.0.0] - 2026-10-27

### Ajouté

- **Favoris et onglets :** les favoris, les onglets épinglés (avec leurs dossiers) et les onglets ouverts de chaque espace Arc sont repris dans la barre de favoris de Chrome.
- **Historique :** l'historique Arc est fusionné dans celui de Chrome. Les visites déjà présentes ne sont pas dupliquées. Une sauvegarde est faite avant, avec restauration automatique en cas d'erreur.
- **Extensions :** le script fait l'inventaire des extensions Arc, puis ouvre les pages du Chrome Web Store de celles qui manquent, profil par profil.
- **Deux organisations :** un profil Chrome par espace Arc, ou tout dans un seul profil Chrome.
- **Option `--remplacer` :** vide l'historique et les favoris des profils Chrome ciblés avant d'y mettre le contenu d'Arc.
- **Fichier `correspondance.txt` :** permet d'exclure un espace ou de l'envoyer vers un profil Chrome qui porte un autre nom.
- **Secours :** un fichier de favoris HTML par espace, et des instructions claires quand macOS bloque l'accès aux dossiers de Chrome.
- **Relance sans doublon :** le script garde la trace de ce qui a déjà été migré.
- **Qualité :** tests automatisés sur Linux et macOS, et intégration continue (ShellCheck, Ruff).
