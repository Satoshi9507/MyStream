import sys
import psycopg2
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QScrollArea, QGridLayout, QFrame, QCheckBox, QMenu,
                             QWidgetAction, QSlider) 
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# =================================================================
# 1. CONFIGURATION DE LA BASE DE DONNÉES
# =================================================================
DB_CONFIG = {
    "database": "streambdd",
    "user": "ramalingame",
    "password": "", 
    "host": "localhost"
}

# =================================================================
# 2. CHARGEMENT ASYNCHRONE DES IMAGES
# =================================================================
class ImageLoader(QThread):
    finished = pyqtSignal(QPixmap)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            res = requests.get(self.url, timeout=3)
            pixmap = QPixmap()
            pixmap.loadFromData(res.content)
            self.finished.emit(pixmap)
        except: self.finished.emit(QPixmap())

# =================================================================
# 3. COMPOSANT VISUEL : CARTE DE FILM
# =================================================================
class MovieCard(QFrame):
    def __init__(self, id_movie, title, poster_path, rating, parent):
        super().__init__()
        self.id_movie = id_movie
        self.parent = parent 
        self.setFixedSize(200, 330)
        self.setStyleSheet("""
            QFrame { background-color: #1a1a1a; border-radius: 10px; padding: 5px; }
            QFrame:hover { border: 2px solid #E50914; background-color: #222; }
            QLabel { color: white; background: transparent; }
        """)
        layout = QVBoxLayout(self)
        self.poster_label = QLabel("⌛")
        self.poster_label.setFixedSize(180, 240)
        self.poster_label.setScaledContents(True)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.poster_label)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        layout.addWidget(self.title_label)

        self.rate_label = QLabel(f"⭐ {rating:.1f}" if rating else "⭐ N/A")
        self.rate_label.setStyleSheet("color: #f1c40f; font-weight: bold;")
        layout.addWidget(self.rate_label)

        if poster_path and poster_path not in ["NULL", ""]:
            url = f"https://image.tmdb.org/t/p/w342{poster_path}"
            self.loader = ImageLoader(url)
            self.loader.finished.connect(lambda p: self.poster_label.setPixmap(p))
            self.loader.start()
            
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda e: self.parent.show_movie_details(self.id_movie)

# =================================================================
# 4. FENÊTRE PRINCIPALE
# =================================================================
class StreamApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyStream BDD - Exploration de Films")
        self.resize(1300, 900)
        self.setStyleSheet("background-color: #141414;")
        
        self.db_year_min, self.db_year_max = 1900, 2025
        self.current_page = 0
        self.page_size = 40 
        self.conn = None

        self.init_ui()
        self.connect_db()

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        self.main_layout = QVBoxLayout(container)

        # --- BARRE DE RECHERCHE ET FILTRES ---
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un film ou mot-clé...")
        self.search_input.setStyleSheet("background: #333; color: white; padding: 10px; border-radius: 5px;")
        self.search_input.textChanged.connect(self.reset_pagination)
        
        # BOUTON GENRES
        self.btn_genre = QPushButton("GENRES ▼")
        self.btn_genre.setStyleSheet("background: #333; color: white; padding: 10px; border-radius: 5px;")
        self.genre_menu = QMenu(self)
        self.btn_genre.setMenu(self.genre_menu)
        self.genre_checkboxes = {}

        # BOUTON ANNÉES
        self.btn_year = QPushButton("ANNÉES ▼")
        self.btn_year.setStyleSheet("background: #333; color: white; padding: 10px; border-radius: 5px;")
        self.year_menu = QMenu(self)
        self.btn_year.setMenu(self.year_menu)

        # BOUTON RATING (NOUVEAU)
        self.btn_rate = QPushButton("NOTE ▼")
        self.btn_rate.setStyleSheet("background: #333; color: white; padding: 10px; border-radius: 5px;")
        self.rate_menu = QMenu(self)
        self.btn_rate.setMenu(self.rate_menu)

        btn_search = QPushButton("RECHERCHER")
        btn_search.setStyleSheet("background: #E50914; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_search.clicked.connect(self.update_display)

        top_bar.addWidget(self.search_input, 4)
        top_bar.addWidget(self.btn_genre, 1)
        top_bar.addWidget(self.btn_year, 1)
        top_bar.addWidget(self.btn_rate, 1) # Ajout du bouton note
        top_bar.addWidget(btn_search, 1)
        self.main_layout.addLayout(top_bar)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setStyleSheet("border: none;")
        self.grid_widget = QWidget(); self.grid_layout = QGridLayout(self.grid_widget)
        self.scroll.setWidget(self.grid_widget); self.main_layout.addWidget(self.scroll)

        # PAGINATION
        pagination_bar = QHBoxLayout()
        self.btn_prev = QPushButton("⬅ PRÉCÉDENT"); self.btn_next = QPushButton("SUIVANT ➡"); self.page_label = QLabel("Page 1")
        style_btn = "background: #444; color: white; padding: 8px 15px; border-radius: 5px;"
        self.btn_prev.setStyleSheet(style_btn); self.btn_next.setStyleSheet(style_btn); self.page_label.setStyleSheet("color: white; font-weight: bold;")
        self.btn_prev.clicked.connect(self.prev_page); self.btn_next.clicked.connect(self.next_page)
        pagination_bar.addStretch(); pagination_bar.addWidget(self.btn_prev); pagination_bar.addWidget(self.page_label); pagination_bar.addWidget(self.btn_next); pagination_bar.addStretch()
        self.main_layout.addLayout(pagination_bar)

    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.fetch_db_year_bounds()
            self.setup_genre_menu()
            self.setup_year_slider_menu()
            self.setup_rate_slider_menu() # Initialisation menu note
            self.update_display()
        except Exception as e: print(f"Erreur DB : {e}")

    # --- SETUP DES MENUS COULISSANTS ---
    
    def setup_year_slider_menu(self):
        container = QWidget(); layout = QVBoxLayout(container)
        self.label_year_range = QLabel(f"Période : {self.db_year_min} - {self.db_year_max}")
        self.label_year_range.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.label_year_range)
        self.slider_year_min = QSlider(Qt.Orientation.Horizontal)
        self.slider_year_min.setRange(self.db_year_min, self.db_year_max); self.slider_year_min.setValue(self.db_year_min)
        self.slider_year_min.valueChanged.connect(self.update_year_logic)
        self.slider_year_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_year_max.setRange(self.db_year_min, self.db_year_max); self.slider_year_max.setValue(self.db_year_max)
        self.slider_year_max.valueChanged.connect(self.update_year_logic)
        layout.addWidget(QLabel("De :", styleSheet="color:#aaa;")); layout.addWidget(self.slider_year_min)
        layout.addWidget(QLabel("À :", styleSheet="color:#aaa;")); layout.addWidget(self.slider_year_max)
        action = QWidgetAction(self.year_menu); action.setDefaultWidget(container); self.year_menu.addAction(action)

    def setup_rate_slider_menu(self):
        """ Crée le menu coulissant pour les notes de 0 à 10 """
        container = QWidget(); layout = QVBoxLayout(container)
        self.label_rate_range = QLabel("Note : 0.0 - 10.0")
        self.label_rate_range.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.label_rate_range)
        
        # PyQt Sliders travaillent avec des entiers, on multiplie par 10 pour simuler des décimales
        self.slider_rate_min = QSlider(Qt.Orientation.Horizontal)
        self.slider_rate_min.setRange(0, 100); self.slider_rate_min.setValue(0)
        self.slider_rate_min.valueChanged.connect(self.update_rate_logic)
        
        self.slider_rate_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_rate_max.setRange(0, 100); self.slider_rate_max.setValue(100)
        self.slider_rate_max.valueChanged.connect(self.update_rate_logic)
        
        layout.addWidget(QLabel("Minimum :", styleSheet="color:#aaa;")); layout.addWidget(self.slider_rate_min)
        layout.addWidget(QLabel("Maximum :", styleSheet="color:#aaa;")); layout.addWidget(self.slider_rate_max)
        action = QWidgetAction(self.rate_menu); action.setDefaultWidget(container); self.rate_menu.addAction(action)

    # --- LOGIQUE DES FILTRES ---

    def update_year_logic(self):
        if self.slider_year_min.value() > self.slider_year_max.value(): self.slider_year_min.setValue(self.slider_year_max.value())
        self.label_year_range.setText(f"Période : {self.slider_year_min.value()} - {self.slider_year_max.value()}")
        self.btn_year.setText(f"ANNÉES ({self.slider_year_min.value()}-{self.slider_year_max.value()}) ▼")
        self.reset_pagination()

    def update_rate_logic(self):
        """ Gère les décimales (ex: 75 -> 7.5) et la cohérence min/max """
        val_min = self.slider_rate_min.value() / 10.0
        val_max = self.slider_rate_max.value() / 10.0
        if val_min > val_max: 
            self.slider_rate_min.setValue(self.slider_rate_max.value())
            val_min = val_max
        self.label_rate_range.setText(f"Note : {val_min:.1f} - {val_max:.1f}")
        self.btn_rate.setText(f"NOTE ({val_min:.1f}-{val_max:.1f}) ▼")
        self.reset_pagination()

    def fetch_db_year_bounds(self):
        cur = self.conn.cursor()
        cur.execute("SELECT EXTRACT(YEAR FROM MIN(release_date))::int, EXTRACT(YEAR FROM MAX(release_date))::int FROM movie_database WHERE release_date IS NOT NULL")
        res = cur.fetchone()
        if res and res[0]: self.db_year_min, self.db_year_max = res[0], res[1]
        cur.close()

    def setup_genre_menu(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM genre ORDER BY name")
        scroll = QScrollArea(); scroll.setFixedSize(200, 300); scroll.setWidgetResizable(True); scroll.setStyleSheet("border:none;")
        container = QWidget(); layout = QVBoxLayout(container)
        for g, in cur.fetchall():
            cb = QCheckBox(g); cb.setStyleSheet("color: white;"); cb.stateChanged.connect(self.reset_pagination)
            layout.addWidget(cb); self.genre_checkboxes[g] = cb
        scroll.setWidget(container)
        action = QWidgetAction(self.genre_menu); action.setDefaultWidget(scroll); self.genre_menu.addAction(action)

    def reset_pagination(self): self.current_page = 0
    def next_page(self): self.current_page += 1; self.update_display()
    def prev_page(self): 
        if self.current_page > 0: self.current_page -= 1; self.update_display()

    # --- AFFICHAGE ---

    def update_display(self):
        self.page_label.setText(f"Page {self.current_page + 1}")
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)
        
        search = self.search_input.text()
        genres = [n for n, cb in self.genre_checkboxes.items() if cb.isChecked()]
        y_min, y_max = self.slider_year_min.value(), self.slider_year_max.value()
        r_min, r_max = self.slider_rate_min.value() / 10.0, self.slider_rate_max.value() / 10.0

        try:
            cur = self.conn.cursor()
            query = """
                SELECT DISTINCT m.id_movie, m.title, m.poster_path, m.vote_average, m.popularity
                FROM movie_database m
                LEFT JOIN movie_genre mg ON m.id_movie = mg.id_movie
                LEFT JOIN genre g ON mg.id_genre = g.id_genre
                LEFT JOIN movie_keywords mk ON m.id_movie = mk.id_movie
                LEFT JOIN keyword_list kl ON mk.id_keyword = kl.id_keyword
                WHERE (m.title ILIKE %s OR kl.name ILIKE %s)
                AND EXTRACT(YEAR FROM m.release_date)::int BETWEEN %s AND %s
                AND m.vote_average BETWEEN %s AND %s
            """
            params = [f'%{search}%', f'%{search}%', y_min, y_max, r_min, r_max]
            if genres:
                query += f" AND g.name IN ALL ({', '.join(['%s']*len(genres))})"
                params.extend(genres)
            query += " ORDER BY m.popularity DESC LIMIT %s OFFSET %s"
            params.extend([self.page_size, self.current_page * self.page_size])
            cur.execute(query, params)
            for idx, row in enumerate(cur.fetchall()):
                self.grid_layout.addWidget(MovieCard(row[0], row[1], row[2], row[3], self), idx // 4, idx % 4)
            cur.close()
        except Exception as e: print(f"SQL Error: {e}")

    def show_movie_details(self, id_movie):
        """ Affiche les infos détaillées incluant Cast et Crew """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT title, overview, vote_average, release_date, runtime, original_language FROM movie_database WHERE id_movie = %s", (id_movie,))
            m = cur.fetchone()
            cur.execute("SELECT g.name FROM genre g JOIN movie_genre mg ON g.id_genre = mg.id_genre WHERE mg.id_movie = %s", (id_movie,))
            gs = ", ".join(r[0] for r in cur.fetchall()) or "N/A"
            cur.execute("SELECT name, character FROM cast_member WHERE id_movie = %s ORDER BY \"order\" LIMIT 10", (id_movie,))
            cast_data = cur.fetchall()
            cur.execute("SELECT name, job FROM crew WHERE id_movie = %s AND job IN ('Director', 'Writer', 'Producer')", (id_movie,))
            crew_data = cur.fetchall()
            cur.close()

            detail = QWidget(); detail.setWindowTitle(f"Détails : {m[0]}"); detail.resize(500, 680); detail.setStyleSheet("background:#141414; color:white; font-family: Arial;")
            layout = QVBoxLayout(detail)
            title_lbl = QLabel(m[0]); title_lbl.setFont(QFont("Arial", 16, QFont.Weight.Bold)); title_lbl.setWordWrap(True); layout.addWidget(title_lbl)
            meta_lbl = QLabel(f"📅 {m[3].year if m[3] else 'N/A'}  |  ⭐ {m[2]:.1f}/10  |  ⏱ {m[4]} min  |  🌐 {m[5].upper() if m[5] else ''}"); meta_lbl.setStyleSheet("color: #bbb;"); layout.addWidget(meta_lbl)
            layout.addWidget(QLabel(f"<b>Genres :</b> {gs}", wordWrap=True))
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border:1px solid #333; margin-top:10px;")
            desc = QLabel(m[1] or "Pas de résumé disponible."); desc.setWordWrap(True); desc.setContentsMargins(10,10,10,10); scroll.setWidget(desc); layout.addWidget(scroll)

            cast_btn = QPushButton("CASTING ▼"); cast_btn.setStyleSheet("background:#222; color:white; padding:8px; border:none; text-align:left;"); layout.addWidget(cast_btn)
            cast_container = QWidget(); cast_layout = QVBoxLayout(cast_container); cast_container.setVisible(False)
            for actor, role in cast_data:
                lbl = QLabel(f"{actor} — {role}"); lbl.setStyleSheet("font-size:12px; color:#ddd;"); cast_layout.addWidget(lbl)
            layout.addWidget(cast_container); cast_btn.clicked.connect(lambda: cast_container.setVisible(not cast_container.isVisible()))

            crew_btn = QPushButton("ÉQUIPE TECHNIQUE ▼"); crew_btn.setStyleSheet("background:#222; color:white; padding:8px; border:none; text-align:left;"); layout.addWidget(crew_btn)
            crew_container = QWidget(); crew_layout = QVBoxLayout(crew_container); crew_container.setVisible(False)
            for name, job in crew_data:
                lbl = QLabel(f"{name} — {job}"); lbl.setStyleSheet("font-size:12px; color:#ddd;"); crew_layout.addWidget(lbl)
            layout.addWidget(crew_container); crew_btn.clicked.connect(lambda: crew_container.setVisible(not crew_container.isVisible()))

            btn_close = QPushButton("FERMER"); btn_close.setStyleSheet("background:#E50914; color:white; font-weight:bold; padding:8px; border-radius:5px;"); btn_close.clicked.connect(detail.close); layout.addWidget(btn_close)
            self.active_win = detail; detail.show()
        except Exception as e: print(f"Detail Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv); window = StreamApp(); window.show(); sys.exit(app.exec())