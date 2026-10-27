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
  - côté Chrome : `Bookmarks`, `History`, les caches listés dans `HISTORY_CACHES` ;
- toute fuite de données hors de la machine (le script ne doit établir aucune connexion réseau) ;
- toute perte de données Chrome sans sauvegarde préalable ;
- toute exécution de code arbitraire à partir du contenu des fichiers Arc (titres, adresses, noms d'espaces).

## Bonnes pratiques pour les utilisateurs

- Télécharge le kit uniquement depuis la page [Releases](https://github.com/Geoffrey-GTM/kit-migration-arc-chrome/releases) de ce dépôt.
- Tu peux retirer l'« Accès complet au disque » à Terminal une fois la migration terminée.
- Supprime le dossier `resultat-migration/` quand tout te convient : il contient une copie de ton historique et de tes favoris.
