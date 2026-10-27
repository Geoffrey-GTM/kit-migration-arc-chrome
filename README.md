# Kit de migration Arc → Google Chrome

[![Dernière version](https://img.shields.io/github/v/release/Geoffrey-GTM/kit-migration-arc-chrome?label=version)](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/releases/latest)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)
![Plateforme : macOS](https://img.shields.io/badge/plateforme-macOS-lightgrey.svg)

Ce kit transfère tes espaces Arc vers Google Chrome sur Mac, en une seule commande. Il reprend les favoris, les onglets épinglés et leurs dossiers, l'historique de navigation et les extensions.

- **Tu choisis l'organisation :** un profil Chrome par espace Arc (par exemple un profil par client), où tout arrive à plat dans la barre de favoris, ou tout dans un seul profil.
- **Aucune perte possible :**
  - Arc n'est jamais modifié.
  - Les fichiers de Chrome sont sauvegardés avant toute écriture.
  - Si la fusion de l'historique échoue, l'historique Chrome est restauré automatiquement.
- **Rejouable :** relancer le script ne crée pas de doublons.
- **100 % local :** le script n'envoie aucune donnée. Il n'utilise que Python 3, sans dépendance à installer.

## Sommaire

- [Ce qui est migré](#ce-qui-est-migré)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Options](#options)
- [Des favoris qui ne viennent pas d'Arc ?](#des-favoris-qui-ne-viennent-pas-darc-)
- [Sécurité et confidentialité](#sécurité-et-confidentialité)
- [Limites](#limites)
- [Fonctionnement](#fonctionnement)
- [Développement](#développement)
- [Contribuer](#contribuer)
- [Licence](#licence)

## Ce qui est migré

| Dans Arc | Dans Chrome, mode « un profil par espace » | Dans Chrome, mode « un seul profil » |
|---|---|---|
| Favoris (icônes du haut) | directement dans la barre de favoris | dossier « Arc – favoris » |
| Onglets épinglés et dossiers | directement dans la barre, avec leurs dossiers | dossier « Arc – *nom de l'espace* » |
| Onglets ouverts | directement dans la barre | sous-dossier « Onglets ouverts » |
| Historique | historique du profil | historique du profil |
| Extensions du Chrome Web Store | pages du Web Store ouvertes pour réinstaller | idem |
| Mots de passe | à transférer à la main ([LISEZMOI.txt](LISEZMOI.txt), étape 6) | idem |

Avec l'option `--dossiers`, les onglets épinglés et ouverts sont plutôt rangés dans deux dossiers « Arc – onglets épinglés » et « Arc – onglets ouverts », comme en version 1.0.

## Prérequis

- macOS, avec Arc et Google Chrome installés. Chrome doit avoir été ouvert au moins une fois.
- Python 3. Il est déjà présent si les outils de ligne de commande d'Apple sont installés ; sinon, lance `xcode-select --install`.
- L'**Accès complet au disque** pour Terminal : Réglages Système › Confidentialité et sécurité › Accès complet au disque. Sans lui, macOS empêche le script de lire les dossiers de Chrome.

## Installation

1. Télécharge `Kit-migration-Arc-Chrome-vX.Y.Z.zip` depuis la page [Releases](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/releases/latest).
2. Décompresse-le dans ton dossier **Téléchargements**. Tu obtiens un dossier `Kit-migration-Arc-Chrome`.

Pas de fichier `.zip` dans la release ? Utilise **Code › Download ZIP** sur cette page, puis renomme le dossier décompressé `kit-migration-arc-chrome-main` en `Kit-migration-Arc-Chrome`.

## Utilisation

1. **Mode « un profil par espace » uniquement :** crée dans Chrome un profil par espace Arc, avec exactement le même nom. Les majuscules n'ont pas d'importance.
2. Quitte **Arc** et **Chrome** avec Cmd+Q. Fermer la fenêtre ne suffit pas.
3. Dans Terminal, lance :

   ```bash
   bash ~/Downloads/Kit-migration-Arc-Chrome/migrer-arc-vers-chrome.sh
   ```

Le script déroule alors ces étapes :

1. Il liste tes espaces Arc et tes profils Chrome.
2. Il te demande l'organisation voulue.
3. Il signale les profils qui affichent aussi des favoris de ton compte Google (voir [plus bas](#des-favoris-qui-ne-viennent-pas-darc-)).
4. Il affiche ce qu'il va faire et attend ta confirmation avant de modifier quoi que ce soit.
5. Il propose d'ouvrir les pages du Chrome Web Store des extensions à réinstaller.

Le mode d'emploi pas à pas, avec les mots de passe, le dépannage et le retour en arrière, se trouve dans [LISEZMOI.txt](LISEZMOI.txt).

### Les trois commandes

| Commande | Ce qu'elle fait |
|---|---|
| `bash migrer-arc-vers-chrome.sh` | Migration guidée. Ajoute le contenu d'Arc à Chrome sans rien effacer. |
| `bash remplacer-tous-les-espaces.sh` | Repart de zéro : vide les favoris et l'historique de chaque profil Chrome lié à un espace Arc, puis y remet uniquement le contenu d'Arc. Sauvegarde faite avant. |
| `bash diagnostic-favoris.sh` | Lecture seule : montre, profil par profil, les favoris enregistrés sur ce Mac et ceux du compte Google. Arc et Chrome peuvent rester ouverts. |

Les trois se lancent depuis le dossier du kit, par exemple `bash ~/Downloads/Kit-migration-Arc-Chrome/diagnostic-favoris.sh`.

### Exclure ou rediriger des espaces

Le fichier [`correspondance.txt`](correspondance.txt) est facultatif. Mets-y une règle par ligne :

```text
Ancien client = ignorer        # cet espace n'est pas migré
Clients = Travail              # l'espace « Clients » va dans le profil Chrome « Travail »
```

## Options

```text
--mode espaces       un profil Chrome par espace Arc
--mode unique        tous les espaces dans un seul profil Chrome
--profil "Nom"       profil Chrome qui reçoit tout (mode unique)
--remplacer          vide l'historique et les favoris des profils Chrome ciblés avant d'y mettre le contenu d'Arc
--dossiers           range les onglets dans « Arc – onglets épinglés / ouverts » au lieu de les mettre à plat
--forcer             refait une migration déjà faite
--oui                répond oui à toutes les questions
--diagnostic         montre d'où viennent les favoris de chaque profil, sans rien modifier
--version / --aide
```

## Des favoris qui ne viennent pas d'Arc ?

Si un profil Chrome est connecté à un compte Google, Chrome affiche dans la barre **deux sources** :

- les favoris enregistrés **sur ce Mac** (fichier `Bookmarks`) : c'est là que le kit écrit, et ce que `--remplacer` vide ;
- les favoris enregistrés **dans le compte Google** (fichier `AccountBookmarks`) : le kit n'y touche jamais. Effacés du Mac, ils seraient retéléchargés depuis Google.

Le kit les signale avant de lancer la migration, et `bash diagnostic-favoris.sh` les liste. Pour ne garder que le contenu d'Arc, dans chaque profil concerné :

- **les masquer sans les perdre :** Paramètres › Vous et Google › Synchronisation › décocher « Favoris » ;
- **ou les supprimer pour de bon :** gestionnaire de favoris (Cmd+Option+B) › section « Dans votre compte Google » › tout sélectionner › Supprimer. C'est irréversible, et vaut pour tous tes appareils.

> ⚠️ N'utilise pas « Supprimer les données » sur [chrome.google.com/sync](https://chrome.google.com/sync) : ce bouton efface aussi tes mots de passe et tout le reste du compte.

## Sécurité et confidentialité

- **Ce que le script lit :**
  - les fichiers d'Arc, dans `~/Library/Application Support/Arc` : la barre latérale, l'historique et le manifeste des extensions ;
  - dans Chrome, en lecture seule : `Local State` (la liste des profils), `AccountBookmarks` (les favoris du compte Google, pour les signaler) et `Preferences` (seulement pour savoir si un compte Google est connecté, avec `--diagnostic`).
- **Ce qu'il écrit :** uniquement `Bookmarks` et `History` dans les profils Chrome ciblés. Avant d'écrire, il copie ces fichiers, et les copies chiffrées `EncryptedBookmarks*` quand Chrome en crée, dans `resultat-migration/`. En mode `--remplacer`, il déplace aussi quelques caches que Chrome recrée tout seul (sites fréquents, raccourcis de la barre d'adresse).
- **Ce qu'il ne touche jamais :** les mots de passe, les cookies, les données de paiement et les favoris du compte Google.
- **Réseau :** le script n'établit aucune connexion. Il ouvre seulement les pages du Chrome Web Store, dans Chrome et si tu l'acceptes.
- **Le dossier `resultat-migration/`** contient une copie de ton historique et de tes favoris Chrome (les sauvegardes). Supprime-le quand tout te convient, et ne le partage pas.

Pour signaler une faille, suis la procédure de [SECURITY.md](SECURITY.md).

## Limites

- Le kit fonctionne uniquement sur Mac : la version Windows d'Arc n'est pas prise en charge.
- Ne sont pas repris :
  - les sessions ouvertes (cookies) ;
  - les mots de passe, à transférer à la main ;
  - les notes, les Easels et les Boosts d'Arc ;
  - les extensions installées hors du Chrome Web Store.
- L'historique est rangé par **profil** Arc. Si plusieurs espaces partagent le même profil Arc, chaque profil Chrome correspondant reçoit tout cet historique.
- Les favoris repris sont ceux de ce Mac. Les onglets épinglés, eux, sont toujours repris.
- Un outil de sécurité d'entreprise peut bloquer l'accès aux fichiers de Chrome. Dans ce cas, seuls les favoris passent, importés à la main avec les fichiers HTML de secours.

## Fonctionnement

| Étape | Source (Arc) | Destination (Chrome) | Méthode |
|---|---|---|---|
| Espaces et onglets | `StorableSidebar.json` | `<profil>/Bookmarks` | ajout à plat à la barre de favoris (en dossiers avec `--dossiers`), nouveaux identifiants et GUID, somme de contrôle retirée (Chrome la recalcule) |
| Historique | `User Data/<profil>/History` (SQLite) | `<profil>/History` (SQLite) | fusion dans une transaction, sans dupliquer les visites déjà présentes, puis contrôle d'intégrité |
| Extensions | `User Data/<profil>/Extensions/*/manifest.json` | — | comparaison avec les extensions du profil Chrome |
| Diagnostic | — | `<profil>/Bookmarks` et `<profil>/AccountBookmarks` | lecture seule, résumé dans `resultat-migration/diagnostic.txt` |

Un fichier `resultat-migration/.etat-migration.json` garde la trace de ce qui a déjà été fait. C'est ce qui permet de relancer le script sans créer de doublons.

## Développement

Le code n'utilise que la bibliothèque standard. Il doit rester compatible avec Python 3.9, la version fournie par les outils de ligne de commande d'Apple, et avec bash 3.2, celui de macOS.

```bash
python3 -m unittest discover -s tests -v   # tests (des données factices, jamais tes vrais navigateurs)
ruff check . && ruff format --check .      # style Python
shellcheck *.sh scripts/*.sh
bash scripts/construire-archive.sh         # archive de release dans dist/
```

```text
.
├── migrer-arc-vers-chrome.sh   lanceur : vérifications (macOS, navigateurs fermés, Python)
├── migrer_arc_chrome.py        logique de migration
├── remplacer-tous-les-espaces.sh  raccourci : --mode espaces --remplacer
├── diagnostic-favoris.sh       raccourci : --diagnostic
├── correspondance.txt          modèle d'exclusions et de redirections
├── LISEZMOI.txt                mode d'emploi pour l'utilisateur final
├── tests/                      tests unitaires et de bout en bout, données factices
└── scripts/                    construction de l'archive de release
```

## Contribuer

Les signalements de bugs et les propositions sont bienvenus : voir [CONTRIBUTING.md](CONTRIBUTING.md) et le [code de conduite](CODE_OF_CONDUCT.md). Les évolutions de chaque version sont listées dans le [CHANGELOG](CHANGELOG.md).

## Licence

Distribué sous licence [MIT](LICENSE).

*Projet indépendant, sans lien avec The Browser Company ni Google. Arc et Google Chrome sont des marques de leurs propriétaires respectifs.*
