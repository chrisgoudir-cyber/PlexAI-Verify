# PlexAI Verify Enterprise — Sprint 1

Ce sprint consolide le moteur de sécurité et de traçabilité.

## Ajouts réels

- seuil automatique centralisé à 95 % ;
- trois niveaux de confiance : sûr, à vérifier, ambigu ;
- historique général des actions ;
- détail de chaque renommage appliqué, bloqué ou en erreur ;
- enregistrement des annulations ;
- opérations de renommage toujours réversibles ;
- migrations SQLite automatiques, sans effacer la base existante.

## Utilisation

1. Lancer `py main.py`.
2. Ouvrir **Corrections**.
3. Vérifier la colonne **Niveau**.
4. Appliquer uniquement les éléments cochés.
5. Consulter **Historique général** pour la traçabilité.

Aucun média n’est supprimé par ce sprint.
