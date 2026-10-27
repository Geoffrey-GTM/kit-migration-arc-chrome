#!/bin/bash
# Repart de zéro : vide les favoris et l'historique de chaque profil Chrome associé à un espace Arc
# (sauf les espaces marqués « ignorer » dans correspondance.txt), puis y remet uniquement le contenu
# d'Arc : favoris, onglets (à plat dans la barre), historique.
# Sauvegarde automatique avant effacement dans resultat-migration/sauvegardes-chrome.
# Les favoris du compte Google ne sont pas touchés : le script les signale.
# Usage : bash remplacer-tous-les-espaces.sh   (Arc et Chrome fermés avec Cmd+Q)
exec bash "$(cd "$(dirname "$0")" && pwd)/migrer-arc-vers-chrome.sh" --mode espaces --remplacer "$@"
