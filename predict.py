import tensorflow as tf
import numpy as np
import json
import os
import traceback
import logging
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from PIL import Image


# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des chemins
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'leaf_disease_cnn.h5')
JSON_PATH = os.path.join(os.path.dirname(__file__), 'data', 'disease_info.json')

def load_components():
    """Charge le modèle et les données JSON avec gestion robuste des erreurs"""
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        logger.info(f"Modèle chargé depuis {MODEL_PATH}")
        
        # Validation de la forme d'entrée
        if len(model.input_shape) != 4:
            logger.error(f"Forme d'entrée inattendue: {model.input_shape}")
            return None, None
        
        TARGET_SIZE = model.input_shape[1:3]
        logger.info(f"=== Architecture du modèle ===")
        model.summary()
        logger.info(f"Taille d'image requise: {TARGET_SIZE}")
        
        return model, TARGET_SIZE
    except Exception as e:
        logger.error(f"Erreur de chargement du modèle: {str(e)}")
        return None, None

# Initialisation
model, TARGET_SIZE = load_components()
if model is None:
    logger.error("Le modèle n'a pas pu être chargé. Vérifiez le fichier et le chemin.")
    exit(1)

   
# Chargement des informations sur les maladies
disease_info = {}
if not os.path.exists(JSON_PATH):
    logger.error(f"Le fichier JSON {JSON_PATH} n'existe pas.")
else:
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            disease_info = json.load(f)
        logger.info(f"JSON chargé depuis {JSON_PATH}")
        logger.info(f"Clés disponibles: {list(disease_info.keys())}")
    except Exception as e:
        logger.error(f"Erreur de chargement JSON: {str(e)}")

# Validation des classes
class_names = ['Apple_scab', 'Black_rot', 'Cedar_apple_rust', 'Healthy']
missing_classes = [cls for cls in class_names if cls not in disease_info]
if missing_classes:
    logger.warning(f"Classes manquantes dans disease_info.json: {missing_classes}")



def predict_disease(img_path):
    """Prédit la maladie à partir d'une image avec gestion d'erreur complète"""
    if not model:
        return error_response("Modèle non chargé")

    if not os.path.exists(img_path):
        return error_response("Image introuvable", {"path": img_path})

    try:
        # Vérification du format de l'image
        img = Image.open(img_path)
        if img.format not in ['JPEG', 'PNG']:
            return error_response("Format d'image non supporté", {"format": img.format})
        img.close()

        # Chargement et prétraitement
        img = load_img(img_path, target_size=TARGET_SIZE)
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        logger.info(f"Shape: {img_array.shape}, Dtype: {img_array.dtype}")
        logger.info(f"Valeurs: min={np.min(img_array)}, max={np.max(img_array)}")

        # Prédiction
        prediction = model.predict(img_array)
        logger.info(f"Prédictions brutes: {prediction}")

        predicted_idx = np.argmax(prediction)
        if predicted_idx >= len(class_names):
            return error_response("Index de prédiction invalide", {"index": predicted_idx})

        predicted_class = class_names[predicted_idx]
        confidence = float(np.max(prediction))
        disease_data = disease_info.get(predicted_class, {})

        return {
            "status": "success",
            "classe": predicted_class,
            "confiance": round(confidence * 100, 2),
            "image": os.path.basename(img_path),
            "nom": disease_data.get("nom", predicted_class),
            "description": disease_data.get("description", "Non disponible"),
            "symptomes": disease_data.get("symptomes", "Non disponible"),
            "causes": disease_data.get("causes", "Non disponible"),
            "prevention": disease_data.get("prevention", "Non disponible"),
            "recommandation": disease_data.get("recommandation", "Non disponible")
        }

    except Exception as e:
        logger.error(f"ERREUR: {str(e)}\n{traceback.format_exc()}")
        return error_response("Échec de l'analyse", {
            "type": type(e).__name__,
            "details": str(e),
            "traceback": traceback.format_exc()
        })


def error_response(message, details=None):
    """Génère une réponse d'erreur standardisée"""
    return {
        "status": "error",
        "message": message,
        "details": details,
        "classe": "Erreur",
        "confiance": 0.0,
        "nom": "Erreur",
        "description": message,
        "symptomes": "Non disponible",
        "causes": "Non disponible",
        "prevention": "Non disponible",
        "recommandation": "Contactez l'administrateur"
    }