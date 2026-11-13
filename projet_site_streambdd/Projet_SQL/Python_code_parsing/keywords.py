import csv
import ast

movie_csv = "archive/movies_metadata.csv"
keywords_csv = "archive/keywords.csv"

f_list = open("insert_keyword_list.sql", 'w', encoding='utf-8')
f_link = open("insert_movie_keywords.sql", 'w', encoding='utf-8')

valid_movie_ids = set()
unique_keywords = {} 

print("Étape 1 : Chargement des IDs valides...")
with open(movie_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        m_id = row.get('id')
        if m_id and m_id.isdigit():
            valid_movie_ids.add(m_id)

print("Étape 2 : Extraction et liaison...")
with open(keywords_csv, 'r', encoding='utf-8') as f_in:
    reader_k = csv.DictReader(f_in)
    
    for row in reader_k:
        m_id = row.get('id')
        
        if m_id in valid_movie_ids:
            try:
                kw_data = ast.literal_eval(row['keywords'])
                for kw in kw_data:
                    kw_id = kw['id']
                    kw_name = kw['name'].replace("'", "''")
                    
                    unique_keywords[kw_id] = kw_name
                    
                    # Correction : on enlève les guillemets simples pour les IDs INTEGER
                    f_link.write(f"INSERT INTO movie_keywords (id_movie, id_keyword) VALUES ({m_id}, {kw_id}) ON CONFLICT DO NOTHING;\n")
            except:
                continue

print("Étape 3 : Finalisation...")
for kid, kname in unique_keywords.items():
    # Correction : kid est un nombre, kname est un texte (garde les guillemets pour kname)
    f_list.write(f"INSERT INTO keyword_list (id_keyword, name) VALUES ({kid}, '{kname}') ON CONFLICT DO NOTHING;\n")

f_list.close()
f_link.close()
print(":-) Terminé !")