import csv
import ast

csv_path = "archive/movies_metadata.csv"
sql_genre = "insert_genres.sql"
sql_movie_genre = "insert_movie_genre.sql"

genres_uniques = {} 
liens = []          

try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                m_id = row['id'].strip()
                if not m_id.isdigit(): continue # Cohérence avec ton script principal
                
                genres_data = ast.literal_eval(row['genres'])
                
                for g in genres_data:
                    id_g = g['id']
                    nom_g = g['name'].replace("'", "''")
                    
                    genres_uniques[id_g] = nom_g
                    liens.append((m_id, id_g))
            except:
                continue

    # Écriture : Table de référence
    with open(sql_genre, 'w', encoding='utf-8') as f:
        for id_g, nom_g in genres_uniques.items():
            # Utilise id_genre et name (vérifie bien tes colonnes SQL)
            f.write(f"INSERT INTO genre (id_genre, name) VALUES ({id_g}, '{nom_g}') ON CONFLICT DO NOTHING;\n")

    # Écriture : Table de liaison (LA CORRECTION EST ICI)
    with open(sql_movie_genre, 'w', encoding='utf-8') as f:
        for m_id, id_g in liens:
            # On change 'movie_id' en 'id_movie' et 'genre_id' en 'id_genre' pour la cohérence
            f.write(f"INSERT INTO movie_genre (id_movie, id_genre) VALUES ({m_id}, {id_g}) ON CONFLICT DO NOTHING;\n")

    print(f":-) Terminé ! {len(genres_uniques)} genres et {len(liens)} liens générés.")

except FileNotFoundError:
    print(":-( Fichier CSV introuvable.")