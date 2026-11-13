import csv

# Chemins vers tes fichiers
links_csv = "archive/links_small.csv"
ratings_csv = "archive/ratings_small.csv"
output_sql = "insert_ratings_final.sql"

id_map = {}

print("1. Lecture de links_small.csv pour la traduction...")
try:
    with open(links_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # On lie le movieId (MovieLens) au tmdbId (ta base de films)
            if row['movieId'] and row['tmdbId']:
                id_map[row['movieId']] = row['tmdbId']
    print(f"   -> {len(id_map)} correspondances trouvées.")

    print("2. Parsing de ratings_small.csv et génération du SQL...")
    with open(ratings_csv, 'r', encoding='utf-8') as f_in:
        reader_r = csv.DictReader(f_in)
        with open(output_sql, 'w', encoding='utf-8') as f_out:
            count = 0
            for row in reader_r:
                ml_id = row['movieId']
                # Si le film existe dans notre dictionnaire de traduction
                if ml_id in id_map:
                    tmdb_id = id_map[ml_id]
                    u_id = row['userId']
                    rate = row['rating']
                    
                    # On écrit l'INSERT avec le bon ID (celui de ta table movie_database)
                    sql = f"INSERT INTO rating (user_id, movie_id, rate) VALUES ({u_id}, {tmdb_id}, {rate}) ON CONFLICT DO NOTHING;\n"
                    f_out.write(sql)
                    count += 1
            
    print(f":-) Terminé ! : Fichier '{output_sql}' généré avec {count} lignes !")

except FileNotFoundError as e:
    print(f":-( ERREUR : Fichier introuvable. Vérifie le dossier archive. ({e})")
except Exception as e:
    print(f":-( Une erreur est survenue : {e}")