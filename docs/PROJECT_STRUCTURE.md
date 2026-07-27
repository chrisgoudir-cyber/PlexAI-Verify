# Structure du projet

- `app/` : interface actuelle et services techniques historiques.
- `core/` : domaine, dépôts et services métier.
- `tests/` : tests automatiques.
- `scripts/` : installation, lancement, sauvegarde et Git.
- `installer/` : installateur Windows Inno Setup.
- `docs/` : documentation technique.

## Règle d'évolution

Les nouvelles fonctions métier doivent entrer dans `core/services` ou `core/domain`.
Les écrans PySide6 restent dans `app/`. Les connecteurs optionnels doivent être isolés dans
`app/plugins` ou dans un paquet dédié. Les fichiers médias ne doivent jamais être supprimés
automatiquement.
