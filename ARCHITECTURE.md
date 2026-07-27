# Architecture v8

La v8 introduit une séparation progressive sans casser l’application existante.

## Couches

- `core/domain` : objets métier sans dépendance Qt ou SQLite.
- `core/repositories` : accès aux données et traduction des lignes SQLite.
- `core/services` : règles métier du tableau de bord et de l’audit.
- `core/api` : façade interne unique consommée par l’interface et la CLI.
- `app` : interface Qt existante et adaptateurs historiques.
- `tests` : tests unitaires du domaine.

## Principe de migration

Les anciens modules restent opérationnels. Les fonctionnalités sont déplacées une par une derrière `ApplicationAPI`. La v8 migre déjà le calcul du tableau de bord et l’accès aux problèmes. Cette méthode évite une réécriture brutale et permet de tester chaque étape.
