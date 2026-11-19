from flask import Flask, request, jsonify, send_from_directory, render_template, session, redirect, url_for
from flask_cors import CORS
import os
import sqlite3
import logging
import time
import smtplib
import ssl
import secrets
from datetime import datetime, timedelta
from email.message import EmailMessage
from joblib import load
from werkzeug.security import generate_password_hash, check_password_hash

from predict import predict_disease
from dotenv import load_dotenv

load_dotenv()  # Charge les variables du fichier .env

# === Debug / Constantes ===
DEV = True  # passe à False en production

def init_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        # Activer foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Table users
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

# Configuration initiale
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')  # obligatoire pour gérer la session

# Autoriser les cookies (sessions) dans CORS
CORS(app, supports_credentials=True)

# Configuration de l'application
app.config.update({
    'UPLOAD_FOLDER': 'static/uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg'},
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-123')
})

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chargement des modèles
def load_models():
    models = {
        'irrigation': None,
        'disease': None
    }
    
    try:
        if os.path.exists('model/irrigation_model.pkl'):
            models['irrigation'] = load('model/irrigation_model.pkl')
            logger.info("✅ Modèle d'irrigation chargé avec succès")
        else:
            logger.warning("⚠ Fichier irrigation_model.pkl introuvable, utilisation de la logique heuristique")
    except Exception as e:
        logger.error(f"❌ Erreur de chargement du modèle d'irrigation: {str(e)}")
    
    return models

models = load_models()

def send_reset_email(to_email, reset_link):
    sender = os.environ.get('GMAIL_USER')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')

    if not sender or not app_password:
        logger.error("GMAIL_USER ou GMAIL_APP_PASSWORD manquant dans les variables d'environnement.")
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Réinitialisation de mot de passe - AgriBot Tafilalet'
    msg['From'] = f'AgriBot Tafilalet <{sender}>'
    msg['To'] = to_email
    msg.set_content(f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe.
Cliquez sur ce lien pour définir un nouveau mot de passe (valide 1h) :
{reset_link}

Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

— AgriBot Tafilalet
""")
    msg.add_alternative(f"""
<html>
  <body>
    <p>Bonjour,</p>
    <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
    <p>
      <a href="{reset_link}">Cliquez ici pour définir un nouveau mot de passe</a><br>
      <small>(le lien est valide 1 heure)</small>
    </p>
    <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
    <p>— AgriBot Tafilalet</p>
  </body>
</html>
""", subtype='html')

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(msg)
        logger.info(f"Email de reset envoyé à {to_email}")
        return True
    except Exception as e:
        logger.error(f"Erreur envoi email reset: {e}", exc_info=True)
        return False

# Fonctions utilitaires
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"img_{timestamp}_{secrets.token_hex(4)}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        if os.path.getsize(filepath) == 0:
            raise ValueError("Fichier vide ou corrompu")
        logger.info(f"Fichier sauvegardé: {filepath}")
        return filename
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
        raise

def add_history(user_id, action):
    if user_id is None:
        logger.warning("add_history appelé sans user_id, entrée ignorée.")
        return
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (user_id, action) VALUES (?, ?)",
            (user_id, action)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Erreur add_history: {e}", exc_info=True)
    finally:
        conn.close()

# Routes
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        logger.error("Aucune image reçue dans la requête")
        return jsonify({'status': 'error', 'message': 'Aucune image reçue'}), 400

    file = request.files['image']
    if file.filename == '':
        logger.error("Aucun fichier sélectionné")
        return jsonify({'status': 'error', 'message': 'Aucun fichier sélectionné'}), 400

    if not allowed_file(file.filename):
        logger.error(f"Type de fichier non supporté: {file.filename}")
        return jsonify({'status': 'error', 'message': 'Type de fichier non supporté'}), 400

    try:
        filename = save_uploaded_file(file)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            result = predict_disease(filepath)
        except TypeError:
            from PIL import Image
            img = Image.open(filepath)
            result = predict_disease(img)

        if not isinstance(result, dict):
            raise ValueError("predict_disease doit renvoyer un dict.")

        result['image'] = filename
        logger.info(f"Résultat de prédiction: {result.get('nom', 'Inconnu')}")
        try:
            add_history(session.get('user_id'), f"Analyse image: {filename} -> {result.get('nom', 'Inconnu')}")
        except Exception:
            logger.exception("Impossible d'ajouter l'entrée d'historique (predict)")

        return jsonify(result)
    except Exception as e:
        logger.exception("Erreur dans /predict")
        if DEV:
            return jsonify({'status': 'error', 'message': 'Erreur de traitement', 'details': str(e)}), 500
        return jsonify({'status': 'error', 'message': 'Erreur de traitement'}), 500

@app.route('/irrigation', methods=['POST'])
def irrigation_recommendation():
    try:
        data = request.get_json()
        required = ['soil_moisture', 'temperature', 'humidity', 'last_irrigation']
        
        if not data or not all(field in data for field in required):
            logger.error("Données manquantes dans la requête d'irrigation")
            return jsonify({'status': 'error', 'message': 'Données manquantes'}), 400
        
        soil_moisture = data['soil_moisture']
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        last_irrigation = int(data['last_irrigation'])
        
        if soil_moisture not in ['Sec', 'Optimal', 'Humide']:
            raise ValueError("Valeur de soil_moisture invalide")
        if not (0 <= temperature <= 50):
            raise ValueError("Température invalide (0-50°C)")
        if not (0 <= humidity <= 100):
            raise ValueError("Humidité invalide (0-100%)")
        if not (0 <= last_irrigation <= 30):
            raise ValueError("Dernière irrigation invalide (0-30 jours)")
        
        params = {
            'soil_moisture': soil_moisture,
            'temperature': temperature,
            'humidity': humidity,
            'last_irrigation': last_irrigation
        }
        
        recommendation = generate_irrigation_recommendation(**params)
        try:
            add_history(
                session.get('user_id'), 
                f"Irrigation: Sol {params['soil_moisture']}, {params['temperature']}°C, {params['humidity']}%"
            )
        except Exception as e:
            logger.error(f"Erreur add_history irrigation: {e}")
        
        return jsonify(recommendation)
    except ValueError as e:
        logger.error(f"Données invalides dans /irrigation: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Données invalides', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur dans /irrigation: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Erreur de traitement', 'details': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message vide'}), 400

        response = generate_simple_response(message)
        try:
            add_history(session.get('user_id'), f"Chat: {message[:50]}")
        except Exception as e:
            logger.error(f"Erreur add_history chat: {e}")

        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route principale pour afficher la page d'historique
@app.route('/history', methods=['GET'])
def history_page():
    logger.info(f"Session: {session} at {datetime.now()}")
    if 'user_id' not in session:
        logger.info("Redirection vers /login car user_id absent")
        return redirect(url_for('show_login'))
    user_id = session['user_id']
    logger.info(f"Accès à /history pour user_id: {user_id}")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, created_at
        FROM history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 100
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    logger.info(f"Données historiques: {rows}")
    if not os.path.exists('templates/history.html'):
        logger.error("Fichier history.html manquant dans templates/")
        return "Erreur: Fichier history.html manquant.", 404
    return render_template('history.html', history=rows)

# Route API pour les données d'historique en JSON
@app.route('/history/data', methods=['GET'])
def history_data():
    logger.info(f"Accès à /history/data, session: {session} at {datetime.now()}")
    if 'user_id' not in session:
        return jsonify({
            'error': 'Non authentifié',
            'history': []
        }), 401
    user_id = session['user_id']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, created_at
        FROM history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 100
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        'history': [{"action": row[0], "created_at": row[1]} for row in rows]
    })

# Route pour effacer l'historique
@app.route('/history/clear', methods=['POST'])
def clear_history():
    if 'user_id' not in session:
        return redirect(url_for('show_login'))
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE user_id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect(url_for('history_page'))

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Erreur lors de l'accès au fichier {filename}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Fichier introuvable'}), 404

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('chatbot.html')
    else:
        return redirect(url_for('show_login'))

# Fonctions de logique
def generate_simple_response(message):
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['bonjour', 'salut', 'hello', 'hi']):
        return "Bonjour ! Je suis AgriBot Tafilalet. Je peux vous aider avec l'analyse des maladies des pommiers et les recommandations d'irrigation. Comment puis-je vous aider ?"
    
    elif any(word in message_lower for word in ['maladie', 'diagnostic', 'analyse', 'photo', 'image']):
        return "Pour diagnostiquer une maladie, veuillez utiliser l'option 'Détection de maladie' et télécharger une photo claire de la feuille affectée."
    
    elif any(word in message_lower for word in ['irrigation', 'arrosage', 'eau', 'humidité']):
        return "Pour une recommandation d'irrigation personnalisée, utilisez l'option 'Recommandation d'irrigation' et renseignez les conditions de votre culture."
    
    elif any(word in message_lower for word in ['aide', 'help', 'comment', 'utiliser']):
        return "Je peux vous aider de deux façons principales :\n1. 📸 Analyser des photos de feuilles pour détecter les maladies\n2. 💧 Donner des conseils d'irrigation personnalisés\n\nUtilisez les boutons du menu pour accéder à ces fonctionnalités !"
    
    elif any(word in message_lower for word in ['merci', 'thanks']):
        return "De rien ! N'hésitez pas si vous avez d'autres questions sur vos pommiers. 🌱"
    
    else:
        return "Je suis spécialisé dans l'aide aux agriculteurs pour les pommiers. Vous pouvez me demander de diagnostiquer des maladies via des photos ou obtenir des conseils d'irrigation."

def generate_irrigation_recommendation(soil_moisture, temperature, humidity, last_irrigation):
    if models['irrigation'] is not None:
        logger.info("Utilisation du modèle d'irrigation chargé")
        pass
    
    irrigation_score = 0
    urgency = "low"
    
    if soil_moisture == "Sec":
        irrigation_score += 40
        soil_status = "Votre sol est sec"
    elif soil_moisture == "Optimal":
        irrigation_score += 10
        soil_status = "Votre sol est en état optimal"
    else:
        irrigation_score -= 20
        soil_status = "Votre sol est suffisamment humide"
    
    if temperature > 30:
        irrigation_score += 20
    elif temperature > 25:
        irrigation_score += 10
    elif temperature < 15:
        irrigation_score -= 10
    
    if humidity < 30:
        irrigation_score += 15
    elif humidity < 50:
        irrigation_score += 5
    elif humidity > 80:
        irrigation_score -= 10
    
    if last_irrigation > 7:
        irrigation_score += 30
    elif last_irrigation > 4:
        irrigation_score += 15
    elif last_irrigation > 2:
        irrigation_score += 5
    elif last_irrigation == 0:
        irrigation_score -= 20
    
    if irrigation_score >= 50:
        urgency = "high"
        recommendation = "Irrigation immédiate recommandée (20-25 mm)."
        irrigation_amount = "20-25 mm"
        next_check = "12-24 heures"
    elif irrigation_score >= 25:
        urgency = "medium"
        recommendation = "Irrigation modérée dans les 24-48h (15-20 mm)."
        irrigation_amount = "15-20 mm"
        next_check = "1-2 jours"
    elif irrigation_score >= 5:
        urgency = "low"
        recommendation = "Irrigation légère possible (10-15 mm)."
        irrigation_amount = "10-15 mm"
        next_check = "2-3 jours"
    else:
        urgency = "none"
        recommendation = "Aucune irrigation nécessaire."
        irrigation_amount = "0 mm"
        next_check = "3-4 jours"
    
    conseils = []
    if temperature > 30 and humidity < 40:
        conseils.append("Température élevée et air sec - surveillez vos plantes.")
    if last_irrigation > 7:
        conseils.append("Attention: dernière irrigation très ancienne.")
    if soil_moisture == "Humide" and irrigation_score > 0:
        conseils.append("Sol humide mais conditions sèches - surveillance recommandée.")
    
    return {
        "soil_status": soil_status,
        "recommandation": recommendation,
        "urgency": urgency,
        "irrigation_amount": irrigation_amount,
        "next_check": next_check,
        "score": irrigation_score,
        "conseils": conseils,
        "environmental_summary": {
            "temperature": temperature,
            "humidity": humidity,
            "soil_moisture": soil_moisture,
            "last_irrigation": last_irrigation
        }
    }

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['username'] = username

        try:
            add_history(user[0], "Connexion réussie")
        except Exception:
            logger.exception("Impossible d'ajouter l'historique de connexion")

        return redirect(url_for('index'))
    else:
        if user:
            try:
                add_history(user[0], "Échec de connexion (mauvais mot de passe)")
            except Exception:
                logger.exception("Impossible d'ajouter l'historique d'échec de connexion")
        return "Identifiants incorrects", 401

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        return "Champs manquants", 400

    password_hash = generate_password_hash(password)

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
        conn.commit()
        conn.close()
        return redirect(url_for('show_login'))
    except sqlite3.IntegrityError:
        return "Nom d'utilisateur ou email déjà utilisé", 409

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')

    email = request.form.get('email', '').strip()
    if not email:
        return "Email requis", 400

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return render_template('forgot_password_sent.html')

    token = secrets.token_urlsafe(32)
    expiry_ts = int(time.time()) + 3600

    cursor.execute(
        "UPDATE users SET reset_token=?, reset_token_expiry=? WHERE id=?",
        (token, expiry_ts, user[0])
    )
    conn.commit()
    conn.close()

    reset_link = url_for('reset_password', token=token, _external=True)
    ok = send_reset_email(email, reset_link)

    if not ok:
        logger.warning(f"⚠ Email non envoyé, lien de debug: {reset_link}")
        return render_template('forgot_password_sent.html', debug_link=reset_link)

    return render_template('forgot_password_sent.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, reset_token_expiry FROM users WHERE reset_token = ?", (token,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Lien invalide ou déjà utilisé.", 400

    user_id, expiry_ts = row[0], row[1]
    now_ts = int(time.time())
    if expiry_ts is None or now_ts > int(expiry_ts):
        conn.close()
        return "Lien expiré. Recommencez la procédure.", 400

    if request.method == 'GET':
        conn.close()
        return render_template('reset_password.html', token=token)

    new_password = request.form.get('password', '')
    if len(new_password) < 8:
        conn.close()
        return "Mot de passe trop court (min 8).", 400

    password_hash = generate_password_hash(new_password)
    cursor.execute("""
        UPDATE users
        SET password_hash=?, reset_token=NULL, reset_token_expiry=NULL
        WHERE id=?
    """, (password_hash, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('show_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_login'))

# Démarrage de l'application
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
