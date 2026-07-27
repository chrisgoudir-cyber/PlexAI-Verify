# Migrations SQLite

Chaque changement de schéma devra recevoir un fichier numéroté et idempotent, par exemple :

`0001_add_movie_health_score.sql`

Ne jamais supprimer une colonne contenant des données utilisateur sans sauvegarde et procédure
de retour arrière.
