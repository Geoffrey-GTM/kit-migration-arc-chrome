# Politique de sécurité

## Versions prises en charge

Seule la dernière version publiée reçoit des correctifs de sécurité.

| Version | Prise en charge |
|---|---|
| 1.x (dernière) | ✅ |
| Versions antérieures | ❌ |

## Signaler une vulnérabilité

**N'ouvre pas d'issue publique.** Utilise le signalement privé de GitHub : onglet **Security**, puis **Report a vulnerability** ([lien direct](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/security/advisories/new)).

Indique :

- la version concernée ;
- les étapes pour reproduire le problème ;
- l'impact que tu envisages.

Tu recevras un accusé de réception dès que possible. Le correctif sera publié dans une nouvelle version, avec mention du signalement si tu le souhaites.

## Périmètre

Le script manipule des données de navigation sensibles. Sont notamment concernés :

- toute lecture ou écriture en dehors des fichiers prévus :
  - côté Arc : `StorableSidebar.json`, `History`, les manifestes d'extensions ;
  - côté Chrome, en écriture : `Bookmarks`, `History`, les caches listés dans `HISTORY_CACHES` ;
  - côté Chrome, en lecture seule : `Local State`, `Preferences`, `AccountBookmarks` (copiés : `EncryptedBookmarks*`, dans les sauvegardes) ;
- toute fuite de données hors de la machine (le script ne doit établir aucune connexion réseau) ;
- toute perte de données Chrome sans sauvegarde préalable ;
- toute exécution de code arbitraire à partir du contenu des fichiers Arc (titres, adresses, noms d'espaces).

## Bonnes pratiques pour les utilisateurs

- Télécharge le kit uniquement depuis [ce dépôt](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome).
- Tu peux retirer l'« Accès complet au disque » à Terminal une fois la migration terminée.
- Supprime le dossier `resultat-migration/` quand tout te convient : il contient une copie de ton historique et de tes favoris.
