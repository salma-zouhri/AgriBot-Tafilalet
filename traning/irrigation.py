import pandas as pd
import joblib
import os

# Charger le modèle d'irrigation
try:
    model = joblib.load(os.path.join(os.path.dirname(__file__), 'model', 'irrigation_model.pkl'))
    print("✅ Modèle d'irrigation chargé avec succès")
except Exception as e:
    print(f"❌ Erreur lors du chargement du modèle d'irrigation : {e}")
    model = None

def get_irrigation_recommendation(temperature, humidity, soil_moisture, last_irrigation):
    if not model:
        return {
            "status": "Erreur",
            "message": "Le modèle d'irrigation n'a pas pu être chargé.",
            "recommendation": "Veuillez contacter le support."
        }

    try:
        # Convertir l'humidité du sol en valeur numérique
        soil_moisture_map = {'Sec': 0, 'Optimal': 1, 'Humide': 2}
        soil_moisture_encoded = soil_moisture_map.get(soil_moisture, 1)
        
        # Créer un DataFrame avec les données d'entrée
        input_data = pd.DataFrame({
            'temperature': [temperature],
            'humidity': [humidity],
            'soil_moisture': [soil_moisture_encoded],
            'last_irrigation': [last_irrigation]
        })

        # Faire la prédiction
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0].max()

        # Générer une recommandation basée sur la prédiction
        if prediction == 1:  # Besoin d'irrigation
            if probability > 0.8:
                recommendation = "Irrigation immédiate recommandée (20-25 mm). Pensez à pailler pour conserver l'humidité."
                urgency = "high"
            else:
                recommendation = "Irrigation recommandée dans les prochaines 24 heures (15-20 mm)."
                urgency = "medium"
        else:
            if soil_moisture == "Humide":
                recommendation = "Évitez d'irriguer pendant au moins 3-4 jours. Vérifiez le drainage de votre sol."
                urgency = "low"
            else:
                recommendation = "Aucune irrigation nécessaire pour le moment. Vérifiez à nouveau dans 2-3 jours."
                urgency = "low"

        return {
            "status": "success",
            "prediction": int(prediction),
            "probability": float(probability),
            "recommendation": recommendation,
            "urgency": urgency,
            "message": "Recommandation générée avec succès"
        }

    except Exception as e:
        print(f"❌ Erreur lors de la prédiction d'irrigation : {e}")
        return {
            "status": "error",
            "message": "Une erreur s'est produite lors de la génération de la recommandation."
        }