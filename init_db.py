import sqlite3

# Connexion à la base (elle sera créée si elle n'existe pas)
conn = sqlite3.connect('users.db')

# Création du curseur
cursor = conn.cursor()

# Création de la table des utilisateurs
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# Sauvegarder les modifications et fermer la connexion
conn.commit()
conn.close()

print("✅ Base de données initialisée avec succès.")