# Journal des modifications

Ce fichier liste toutes les évolutions notables du projet.

Il suit le format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les numéros de version respectent le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

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

[Non publié]: https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/releases/tag/v1.0.0
