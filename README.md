# PlexAI Verify Enterprise 2027.2.0

## Architecture `src/` corrigée

Cette édition migre le moteur dans `src/plexai_verify/` et corrige définitivement la détection accidentelle de plusieurs paquets de premier niveau par setuptools.

Installation Windows :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_dev.ps1
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

Consulte `MIGRATION_2027_2.md` avant la première installation.

---

## Enterprise UX 2027

Voir `README_SPRINT2.md`.

# PlexAI Verify v10.0 — Mode Tout-en-un

La v10 ajoute le bouton demandé :

## TOUT VÉRIFIER ET CORRIGER

Une seule action exécute successivement :

1. scan de la bibliothèque ;
2. analyse FFprobe ;
3. extraction de 4 à 6 images réparties dans le film ;
4. création du Video DNA local ;
5. vérification par Ollama ;
6. contrôle du titre et de l’année ;
7. conservation du nom lorsqu’il est correct ;
8. renommage automatique uniquement lorsque :
   - le contenu est reconnu comme un film ;
   - l’IA signale clairement un mauvais nom ;
   - le titre et l’année sont reconnus ;
   - la confiance IA atteint au moins **95 %** ;
   - aucun fichier cible n’existe ;
   - l’extension ne change pas ;
   - le fichier reste dans le même dossier.

## Sécurité

Le mode Tout-en-un :

- ne supprime aucun fichier ;
- ne déplace aucun film ;
- ne corrige jamais une identification incertaine ;
- conserve les cas douteux dans le centre des problèmes ;
- inscrit chaque renommage dans l’historique ;
- permet d’annuler un renommage depuis la page Corrections.

## Résultat final

Le journal affiche notamment :

- `OK, nom conservé`
- `CORRIGÉ AUTOMATIQUEMENT`
- `CONTRÔLE MANUEL`
- `NON FILM / contrôle manuel`
- `RENOMMAGE BLOQUÉ`
- `ERREUR`

## Premier essai conseillé

Pour vérifier le fonctionnement sans risque :

1. utilise temporairement un petit dossier contenant 2 ou 3 copies de films ;
2. lance **TOUT VÉRIFIER ET CORRIGER** ;
3. vérifie le journal ;
4. ouvre **Corrections > Historique** ;
5. teste l’annulation d’un renommage.

Sur une bibliothèque de plus de 1 700 films, l’analyse IA complète peut prendre plusieurs jours avec le matériel indiqué. Le bouton permet d’arrêter proprement le traitement ; les résultats déjà enregistrés sont conservés.
