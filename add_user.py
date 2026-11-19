import sqlite3
from werkzeug.security import generate_password_hash

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"✅ Utilisateur {username} ajouté avec succès !")
    except sqlite3.IntegrityError:
        print(f"⚠️ L'utilisateur {username} existe déjà.")
    conn.close()

if __name__ == "__main__":
    add_user("wissal", "123456")