#!/bin/bash
# Diagnostic en lecture seule : pour chaque profil Chrome, montre les favoris enregistrés
# sur ce Mac (ce que le script écrit) et ceux du compte Google (que Chrome affiche en plus).
# Rien n'est modifié ; Arc et Chrome peuvent rester ouverts.
# Résultat aussi enregistré dans resultat-migration/diagnostic.txt
# Usage : bash diagnostic-favoris.sh
exec bash "$(cd "$(dirname "$0")" && pwd)/migrer-arc-vers-chrome.sh" --diagnostic "$@"
