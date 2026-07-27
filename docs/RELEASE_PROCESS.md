# Publication d'une version

1. Exécuter `scripts\\backup_data.ps1`.
2. Exécuter `scripts\\test.ps1`.
3. Mettre à jour `VERSION` et `CHANGELOG.md`.
4. Construire l'exécutable avec `scripts\\build.ps1`.
5. Tester l'installation sur un dossier vierge.
6. Créer un tag Git : `git tag v2027.1.0`.
7. Ne jamais inclure les clés API ni la base personnelle dans une archive publique.
