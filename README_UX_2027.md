# PlexAI Verify Enterprise UX 2027

Cette version refond le Film Inspector avec une présentation plus visuelle et professionnelle.

## Nouveautés

- hero visuel avec affiche, titre, année et score de confiance ;
- Movie Health Score ;
- cartes techniques vidéo, audio et sous-titres ;
- galerie de quatre captures ;
- jauges explicatives pour chaque preuve ;
- diagnostic ISO/FFprobe mis en évidence ;
- actions simplifiées et sécurisées ;
- historique conservé ;
- aucun renommage automatique sous 95 %.

## Lancement

```powershell
py -m pip install -r requirements.txt
py main.py
```

## Important

L'affiche et les captures apparaissent uniquement si elles sont déjà présentes dans la base ou dans `data/frames/<id film>/`.
La récupération automatique des affiches TMDB sera ajoutée lors du prochain module de métadonnées enrichies.
