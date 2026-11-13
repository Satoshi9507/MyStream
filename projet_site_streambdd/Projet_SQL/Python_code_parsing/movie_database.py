import csv

csv_path = "archive/movies_metadata.csv"
sql_file = "insert_movies_total.sql"

def clean_txt(text):
    """Échappe les apostrophes pour SQL et gère les valeurs vides."""
    if not text or text.lower() == 'nan':
        return "NULL"
    return f"'{text.replace("'", "''")}'"

def clean_num(value, is_float=False):
    """Convertit en nombre ou retourne 0 si la donnée est invalide."""
    try:
        if not value or value.lower() == 'nan':
            return 0
        return float(value) if is_float else int(float(value))
    except (ValueError, TypeError):
        return 0

def clean_bool(value):
    """Convertit les textes 'True'/'False' en booléen SQL."""
    if str(value).lower() in ['true', '1', 't']:
        return "TRUE"
    return "FALSE"

try:
    with open(csv_path, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        with open(sql_file, 'w', encoding='utf-8') as f_out:
            count = 0
            for row in reader:
                try:
                    # Extraction et nettoyage systématique de CHAQUE champ
                    m_id = clean_num(row.get('id', 0))
                    if m_id == 0: continue # Sécurité : l'ID est obligatoire
                    
                    title = clean_txt(row.get('title'))
                    orig_title = clean_txt(row.get('original_title'))
                    imdb_id = clean_txt(row.get('imdb_id'))
                    
                    # Date : vérification sommaire du format YYYY-MM-DD
                    release = row.get('release_date', '')
                    release = f"'{release}'" if (release and len(release) == 10) else "NULL"
                    
                    runtime = clean_num(row.get('runtime'))
                    budget = clean_num(row.get('budget'))
                    revenue = clean_num(row.get('revenue'))
                    popularity = clean_num(row.get('popularity'), is_float=True)
                    vote_avg = clean_num(row.get('vote_average'), is_float=True)
                    vote_cnt = clean_num(row.get('vote_count'))
                    adult = clean_bool(row.get('adult'))
                    lang = clean_txt(row.get('original_language'))
                    homepage = clean_txt(row.get('homepage'))
                    poster = clean_txt(row.get('poster_path'))
                    video = clean_txt(row.get('video'))
                    
                    # Données JSON stockées en TEXT
                    prod_comp = clean_txt(row.get('production_companies'))
                    prod_count = clean_txt(row.get('production_countries'))
                    languages = clean_txt(row.get('spoken_languages'))
                    overview = clean_txt(row.get('overview'))

                    # Construction de la requête avec tous les champs
                    sql = f"""INSERT INTO movie_database (
                        id_movie, title, original_title, imdb_id, release_date, 
                        runtime, budget, revenue, popularity, vote_average, 
                        vote_count, adult, original_language, homepage, poster_path, 
                        video, production_companies, production_countries, spoken_languages, overview
                    ) VALUES (
                        {m_id}, {title}, {orig_title}, {imdb_id}, {release}, 
                        {runtime}, {budget}, {revenue}, {popularity}, {vote_avg}, 
                        {vote_cnt}, {adult}, {lang}, {homepage}, {poster}, 
                        {video}, {prod_comp}, {prod_count}, {languages}, {overview}
                    ) ON CONFLICT (id_movie) DO UPDATE SET 
                        title = EXCLUDED.title, popularity = EXCLUDED.popularity, 
                        vote_average = EXCLUDED.vote_average, overview = EXCLUDED.overview;"""

                    f_out.write(sql + "\n")
                    count += 1
                except Exception:
                    continue

    print(f"✅ Succès ! {count} films exportés avec toutes les colonnes dans {sql_file}")

except Exception as e:
    print(f"❌ Erreur critique : {e}")