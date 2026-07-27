# Migration v10/v13

1. Copier le scan et FFprobe vers `modules/library` et `modules/analysis`.
2. Copier le Centre d'acquisition v13 vers `modules/acquisition`.
3. Raccorder les résultats à la table `movies`.
4. Transformer les anciennes fenêtres en pages intégrées.
5. Brancher les vrais workers sur la maintenance automatique.

Règles : historique obligatoire, annulation des renommages, aucune suppression automatique.
