import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Charger les données
df = pd.read_csv('data/smart_irrigation.csv')
print("Colonnes du dataset :", df.columns)

# Garder seulement les colonnes utiles (corriger soilmiosture)
df = df[['temperature', 'pressure', 'altitude', 'soilmiosture', 'status']]

# Nettoyage de la colonne altitude
df['altitude'] = df['altitude'].astype(str).str.replace('-', '', regex=False).str.replace('nan', 'nan', regex=False)
df['altitude'] = pd.to_numeric(df['altitude'], errors='coerce')

# Supprimer les lignes avec valeurs manquantes
print(f"Nombre de lignes avant nettoyage : {len(df)}")
df.dropna(subset=['altitude'], inplace=True)
print(f"Nombre de lignes après nettoyage : {len(df)}")

# Nettoyer les valeurs aberrantes
df = df[(df['temperature'].between(20, 40)) & (df['pressure'].between(9000, 11000))]

# Convertir les colonnes numériques
df = df.astype({'temperature': float, 'pressure': float, 'soilmiosture': float})

# Supprimer les doublons
df = df.drop_duplicates()

# Séparer les entrées (X) et la cible (y)
X = df[['temperature', 'pressure', 'altitude', 'soilmiosture']]
y = df['status']

# Séparer les données en entraînement et test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Créer le modèle
model = RandomForestClassifier(n_estimators=100, random_state=42)
# Entraîner
model.fit(X_train, y_train)

# Prédiction sur test
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Modèle entraîné avec une précision de {accuracy*100:.2f}%")

# Sauvegarder le modèle
os.makedirs('model', exist_ok=True)
joblib.dump(model, 'model/irrigation_model.pkl')
print("Modèle sauvegardé dans model/irrigation_model.pkl")