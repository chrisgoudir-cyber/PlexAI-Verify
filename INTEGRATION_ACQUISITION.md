# Raccordement à PlexAI Verify v10

## 1. Copier les fichiers

Copier :
- `core/acquisition/`
- `app/acquisition_dialog.py`

## 2. Ajouter un bouton dans la fenêtre principale

```python
self.acquisition_button = QPushButton("🎬 ACQUISITION")
self.acquisition_button.clicked.connect(self.open_acquisition_center)
```

## 3. Ouvrir la boîte de dialogue

```python
from app.acquisition_dialog import AcquisitionDialog
from core.acquisition.models import MissingMovie

def open_acquisition_center(self):
    missing = [
        MissingMovie(
            title=item.title,
            year=item.year,
            collection=item.collection_name,
            external_id=item.tmdb_id,
        )
        for item in self.application_api.collections.list_missing_movies()
    ]
    dialog = AcquisitionDialog(missing, self)
    dialog.exec()
```

## 4. Source des collections

Le service `collections.list_missing_movies()` doit fournir :
- titre
- année
- nom de collection
- identifiant externe facultatif

## 5. Important

Cette archive est un module autonome à intégrer à la v10, car l'archive source complète de la v10
n'était pas disponible dans l'environnement de génération.
