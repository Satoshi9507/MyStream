--- Suppression des tables si elles existent
DROP TABLE IF EXISTS rating, movie_keywords, keyword_list, crew, cast_member, movie_genre, genre, movie_database CASCADE;

--- Table principale : MOVIE_DATABASE
CREATE TABLE movie_database (
    id_movie SERIAL PRIMARY KEY, 
    title TEXT NOT NULL,
    original_title TEXT,
    imdb_id TEXT, 
    release_date DATE, 
    runtime INTEGER, 
    budget INTEGER, 
    revenue BIGINT, 
    popularity FLOAT, 
    vote_average FLOAT, 
    vote_count INTEGER,
    adult BOOLEAN, 
    original_language VARCHAR(10),
    homepage TEXT,
    poster_path TEXT, 
    video TEXT, 
    production_companies TEXT, 
    production_countries TEXT, 
    spoken_languages TEXT, 
    overview TEXT 
);

--- Table : GENRE
CREATE TABLE genre (
    id_genre SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

--- Table de liaison : MOVIE_GENRE
CREATE TABLE movie_genre (
    id_movie INTEGER REFERENCES movie_database(id_movie) ON DELETE CASCADE,
    id_genre INTEGER REFERENCES genre(id_genre) ON DELETE CASCADE,
    PRIMARY KEY (id_movie, id_genre)
);

--- Table : KEYWORD_LIST (Nouvelle table pour les noms de mots-clés uniques)
CREATE TABLE keyword_list (
    id_keyword INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

--- Table de liaison : MOVIE_KEYWORDS (Remplace l'ancienne table keywords)
CREATE TABLE movie_keywords (
    id_movie INTEGER REFERENCES movie_database(id_movie) ON DELETE CASCADE,
    id_keyword INTEGER REFERENCES keyword_list(id_keyword) ON DELETE CASCADE,
    PRIMARY KEY (id_movie, id_keyword)
);

--- Table : CAST_MEMBER
CREATE TABLE cast_member (
    cast_id SERIAL PRIMARY KEY,
    id_movie INTEGER REFERENCES movie_database(id_movie) ON DELETE CASCADE,
    character TEXT,
    name TEXT,
    gender INTEGER,
    "order" INTEGER,
    profile_path TEXT, 
    credit_id TEXT
);

--- Table : CREW
CREATE TABLE crew (
    credit_id TEXT PRIMARY KEY, 
    id_movie INTEGER REFERENCES movie_database(id_movie) ON DELETE CASCADE, 
    department TEXT, 
    job TEXT,
    name TEXT,
    gender INTEGER,
    profile_path TEXT,
    id_crew INTEGER 
);

--- Table : RATING
CREATE TABLE rating (
    user_id INTEGER, 
    movie_id INTEGER REFERENCES movie_database(id_movie) ON DELETE CASCADE,
    rate FLOAT,
    PRIMARY KEY (user_id, movie_id)
);  

