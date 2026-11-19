# Créez recreate_db.py
import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Activer foreign keys
cursor.execute("PRAGMA foreign_keys = ON;")

# Table users AVEC created_at
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        reset_token TEXT,
        reset_token_expiry INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Table history
cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
''')

conn.commit()
conn.close()

print("✅ Base de données recréée avec succès!")
print("📝 Structure correcte:")
print("   - Table 'users' avec colonne 'created_at'")
print("   - Table 'history' avec colonne 'created_at'")
print("\n⚠️ Vous devez maintenant créer un nouveau compte utilisateur")