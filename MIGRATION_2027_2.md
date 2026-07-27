# Migration vers 2027.2.0 — architecture `src/`

Cette version élimine l'erreur setuptools « Multiple top-level packages discovered ».

## Structure

```text
src/plexai_verify/
├── app/
├── core/
├── __init__.py
├── __main__.py
└── cli.py
```

Les dossiers `data`, `logs`, `cache`, `docs`, `installer` et `releases` ne sont plus analysés comme des paquets Python.

## Installation propre

1. Décompresser dans un nouveau dossier.
2. Ne pas recopier l'ancien `.venv`.
3. Lancer :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_dev.ps1
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

## Données personnelles

La base active reste dans `%LOCALAPPDATA%\PlexAI-Verify\plexai.db`.
Elle n'est donc pas perdue lors du changement de dossier du projet.

## Commandes

```powershell
scripts\test.ps1
scripts\build.ps1
scripts\build_exe.ps1
```
