# Professional Foundation 2027.1.0

Cette livraison transforme le projet actuel en base de développement durable sans casser le
Validation Engine existant.

## Démarrage recommandé sous Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_dev.ps1
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

## Initialiser le dépôt Git

```powershell
powershell -ExecutionPolicy Bypass -File scripts\init_git.ps1
```

## Avant une mise à jour

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup_data.ps1
```

Le logiciel reste autonome. Radarr est un connecteur optionnel.
