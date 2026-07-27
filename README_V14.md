# PlexAI Verify v14.0 — X Pro intégré

Cette version fusionne le moteur complet de la v10 avec le Centre d’acquisition v13.

## Nouveautés

- entrée **Acquisition** dans la barre latérale moderne ;
- Wishlist SQLite ;
- envoi vers Radarr avec confirmation ;
- test de connexion Radarr ;
- recherche Web configurable ;
- historique des demandes ;
- toutes les fonctions v10 sont conservées : scan, FFprobe, images, Ollama, Video DNA, audit, corrections et annulation.

## Installation

```powershell
py -m pip install -r requirements.txt
py main.py
```

## Configuration Radarr

1. Copier `acquisition_config.example.json` sous le nom `acquisition_config.json`.
2. Renseigner l’URL, la clé API, le dossier racine et le profil qualité.
3. Passer `enabled` à `true`.
4. Ouvrir **Acquisition**, puis cliquer sur **Tester Radarr**.

La liste contient actuellement trois films de démonstration. La prochaine étape sera son alimentation automatique par le moteur Collections.
