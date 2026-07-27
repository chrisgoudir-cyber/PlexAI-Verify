# PlexAI Verify v11 - Collections intelligentes

## Nouvelles fonctionnalités

### Analyse des collections
- Détection automatique des sagas et collections.
- Pourcentage de complétude.
- Films manquants.

### Tableau de bord
- Collections complètes
- Collections incomplètes
- Nombre de films manquants

### Wishlist
Chaque film manquant peut être ajouté à une liste de souhaits.

### Recherche
Un clic ouvre une recherche (configurable) sur :
- Radarr (API)
- Overseerr
- Jellyseerr
- Recherche Web
- Catalogue personnel

### Architecture proposée

core/
  collections/
    collection_detector.py
    collection_service.py
    wishlist.py
    providers/
       tmdb_provider.py
       local_provider.py
       radarr_provider.py

### Exemple

Mission Impossible

✓ MI
✓ MI2
✓ MI3
✓ Ghost Protocol
✗ Rogue Nation
✗ Fallout
✗ Dead Reckoning

Complétude : 57 %

Actions :
[Ajouter à Wishlist]
[Ouvrir dans Radarr]
[Rechercher]

### Version future

v11.1
- Affiches des films manquants

v11.2
- Statistiques par réalisateur

v11.3
- Synchronisation Radarr
