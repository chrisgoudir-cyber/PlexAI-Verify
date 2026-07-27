# PlexAI Verify Enterprise — Sprint 2

## Film Inspector

Cette version ajoute une fiche film complète accessible par double-clic depuis la bibliothèque ou le Centre des problèmes.

Fonctions ajoutées :

- poster local ou emplacement réservé ;
- titre, année, titre original et proposition de renommage ;
- diagnostic spécifique des ISO et erreurs FFprobe ;
- informations vidéo, audio, HDR et sous-titres ;
- images extraites et Video DNA ;
- onglet explicatif « Pourquoi ce titre ? » ;
- niveaux de preuve séparés : nom, année, FFprobe, images, Video DNA et TMDB ;
- historique du film ;
- correction unitaire uniquement si elle est sûre ;
- possibilité d’ignorer une proposition sans modifier le fichier.

## Sécurité

Le seuil de correction automatique reste fixé à 95 %. Une correction est également bloquée en cas de conflit de nom, de fichier source absent, de déplacement de dossier ou de changement d’extension.

## Lancement

```powershell
py -m pip install -r requirements.txt
py main.py
```
