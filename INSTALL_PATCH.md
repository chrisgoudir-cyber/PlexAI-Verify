# Installation sur la branche feature/film-inspector-2

1. Sauvegarder ou committer les changements en cours.
2. Copier le contenu de ce dossier à la racine du dépôt PlexAI-Verify en acceptant le remplacement.
3. Exécuter :

```powershell
git status
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m plexai_verify
```

4. Après validation :

```powershell
git add .
git commit -m "Film Inspector 2.0"
git push
```
