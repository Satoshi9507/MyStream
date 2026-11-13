import csv
import ast

csv_path = "archive/credits.csv"

def clean(val):
    """Escape SQL text or return NULL for empty."""
    if val is None or val == "":
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

try:
    with open(csv_path, 'r', encoding='utf-8') as f_in, \
         open("insert_cast.sql", "w", encoding="utf-8") as f_cast, \
         open("insert_crew.sql", "w", encoding="utf-8") as f_crew:

        reader = csv.DictReader(f_in)
        # normaliser les noms de colonnes (supprimer espaces accidentels)
        if reader.fieldnames:
            reader.fieldnames = [n.strip() for n in reader.fieldnames]

        lignes = 0
        for row in reader:
            try:
                id_movie = row.get("id")

                # ---------------- CAST ----------------
                cast_field = row.get("cast")
                if cast_field:
                    try:
                        cast_list = ast.literal_eval(cast_field)
                    except Exception as e:
                        print(f"Erreur parse cast id={id_movie}: {e}")
                        cast_list = []

                    for c in cast_list:
                        character = c.get("character")
                        name = c.get("name")
                        gender = c.get("gender")
                        order_ = c.get("order")
                        profile_path = c.get("profile_path")
                        credit_id = c.get("credit_id")

                        f_cast.write(
                            "INSERT INTO cast_member (id_movie, character, name, gender, \"order\", profile_path, credit_id) VALUES ("
                            f"{id_movie}, {clean(character)}, {clean(name)}, {gender if gender is not None else 'NULL'}, "
                            f"{order_ if order_ is not None else 'NULL'}, {clean(profile_path)}, {clean(credit_id)}"
                            ");\n"
                        )

                # ---------------- CREW ----------------
                crew_field = row.get("crew")
                if crew_field:
                    try:
                        crew_list = ast.literal_eval(crew_field)
                    except Exception as e:
                        print(f"Erreur parse crew id={id_movie}: {e}")
                        crew_list = []

                    for c in crew_list:
                        credit_id = c.get("credit_id")
                        department = c.get("department")
                        job = c.get("job")
                        name = c.get("name")
                        gender = c.get("gender")
                        profile_path = c.get("profile_path")
                        id_crew = c.get("id")

                        f_crew.write(
                            "INSERT INTO crew (credit_id, id_movie, department, job, name, gender, profile_path, id_crew) VALUES ("
                            f"{clean(credit_id)}, {id_movie}, {clean(department)}, {clean(job)}, {clean(name)}, "
                            f"{gender if gender is not None else 'NULL'}, {clean(profile_path)}, "
                            f"{id_crew if id_crew is not None else 'NULL'}"
                            ");\n"
                        )

                lignes += 1

            except Exception as e:
                # Affiche l'erreur et continue (ne masque pas les exceptions)
                print(f"Erreur ligne {lignes+1} id={row.get('id')}: {e}")
                continue

    print(f":-) Terminé ! {lignes} films traités.")

except FileNotFoundError:
    print(":-( ERREUR :Fichier credits.csv introuvable")
