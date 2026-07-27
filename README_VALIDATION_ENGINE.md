# PlexAI Verify Enterprise — Validation Engine

Cette version ajoute un moteur de validation croisée qui compare :

- titre et année du fichier ;
- résultats IA ;
- données TMDB ;
- analyse FFprobe ;
- captures visuelles ;
- Video DNA.

## Sécurité

Une correction automatique exige désormais :

- un score croisé d'au moins 95 % ;
- aucune contradiction de titre ou d'année ;
- aucune erreur technique active ;
- une proposition de nom valide.

Un score élevé ne contourne jamais un conflit dur.
