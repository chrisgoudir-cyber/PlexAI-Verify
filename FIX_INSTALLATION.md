# Correctif d’installation 2027.1.1

Cette version corrige l’erreur Setuptools :

`Multiple top-level packages discovered in a flat-layout`

Le paquet déclare maintenant explicitement les modules Python autorisés :

- `app`
- `core`
- `modules`
- `main.py`
- `cli.py`

Les dossiers de données, caches, documentation, installateur et scripts ne sont plus interprétés comme des paquets Python.

## Installation Windows

Dans PowerShell, à la racine du projet :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_dev.ps1
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

## Installation manuelle

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python main.py
```
