# Contribuer

Merci de ton intérêt pour le kit ! Toutes les contributions sont bienvenues : signaler un bug, proposer une idée, améliorer la doc ou le code.

En participant, tu acceptes de respecter le [code de conduite](CODE_OF_CONDUCT.md).

## Signaler un bug ou proposer une idée

Ouvre une [issue](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/issues/new/choose) avec le modèle qui convient.

Pour un bug, indique :

- la version du kit (`bash migrer-arc-vers-chrome.sh --version`) ;
- ta version de macOS ;
- le message affiché dans Terminal.

> ⚠️ **Ne publie aucune donnée personnelle.** Ça vaut pour les adresses de sites, les noms de clients ou d'espaces, les captures de ton historique, et surtout les fichiers du dossier `resultat-migration/` : ils contiennent une copie de ton historique.

Pour une faille de sécurité, n'ouvre pas d'issue publique : suis [SECURITY.md](SECURITY.md).

## Développer

```bash
git clone https://github.com/Geoffrey-GTM/kit-migration-arc-chrome.git
cd kit-migration-arc-chrome
python3 -m unittest discover -s tests -v
```

Les tests utilisent des données **factices**, créées par `tests/fixtures.py`. Ils ne touchent jamais à tes vrais navigateurs. Le test du lanceur bash ne s'exécute que sur macOS.

### Règles du projet

- **Aucune dépendance externe :** bibliothèque standard Python uniquement, compatible **Python 3.9**. C'est la version fournie par les outils de ligne de commande d'Apple.
- **Lanceur compatible avec bash 3.2,** la version installée par défaut sur macOS. Vérifie-le avec `shellcheck *.sh scripts/*.sh`.
- **Style Python :** `ruff format .` puis `ruff check .`. La configuration est dans `pyproject.toml`.
- **Messages en français,** tutoiement, phrases courtes. L'utilisateur final n'est pas forcément technique.
- **Ne jamais écrire dans les fichiers d'Arc.**
- **Toujours sauvegarder un fichier Chrome avant de le modifier** (fonction `backup`). Écrire de façon atomique (`write_json`) ou dans une transaction SQLite.
- **Toute modification de Chrome doit pouvoir être relancée sans doublon.**
- **Ajoute un test** pour chaque correctif ou nouvelle fonction.

### Commits et pull requests

1. Crée une branche à partir de `main`, par exemple `fix/favoris-sans-titre`.
2. Écris des messages de commit au format [Conventional Commits](https://www.conventionalcommits.org/fr/) :
   - `feat:` pour une nouvelle fonction ;
   - `fix:` pour un correctif ;
   - `docs:`, `test:`, `ci:` et `chore:` pour le reste.
3. Ajoute une ligne dans la section « Non publié » du [CHANGELOG](CHANGELOG.md).
4. Avant d'ouvrir la pull request, vérifie que les tests, Ruff et ShellCheck passent (commandes de la section « Développement » du README).
5. Si ta modification touche la lecture d'Arc ou l'écriture dans Chrome, teste-la aussi sur un vrai Mac et précise-le dans la PR.

## Publier une version (mainteneur)

1. Mets à jour `__version__` dans `migrer_arc_chrome.py` et `version` dans `pyproject.toml`.
2. Dans le CHANGELOG, transforme la section « Non publié » en `[X.Y.Z] - AAAA-MM-JJ`, puis mets à jour les liens en bas du fichier.
3. Lance les tests, puis `bash scripts/construire-archive.sh` : l'archive `dist/Kit-migration-Arc-Chrome-vX.Y.Z.zip` est créée.
4. Sur GitHub, ouvre **Releases › Draft a new release**, crée le tag `vX.Y.Z`, reprends les notes du CHANGELOG, joins l'archive, puis clique sur **Publish release**.
