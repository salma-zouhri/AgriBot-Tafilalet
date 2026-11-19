import os
import shutil
from sklearn.model_selection import train_test_split

# Dossier où sont les images originales
data_dir = 'data/apple'

# Dossier où on veut créer la séparation propre
output_dir = 'data_split'

# Liste des classes (noms des sous-dossiers)
classes = [
    'Apple___healthy', 
    'Apple___Apple_scab', 
    'Apple___Black_rot', 
    'Apple___Cedar_apple_rust'
]

data_dir = 'data/apple'


# 1. Récupérer tous les chemins d'images et leurs labels
image_paths = []
labels = []

for label in classes:
    class_dir = os.path.join(data_dir, label)
    for filename in os.listdir(class_dir):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            image_paths.append(os.path.join(class_dir, filename))
            labels.append(label)

print(f"Nombre total d'images : {len(image_paths)}")

# 2. Séparer en train+val (80%) et test (20%)
X_train_val, X_test, y_train_val, y_test = train_test_split(
    image_paths, labels, test_size=0.2, random_state=42, stratify=labels)

# 3. Séparer train (75% de train+val = 60% total) et val (25% de train+val = 20% total)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val)

print(f"Train: {len(X_train)} images")
print(f"Validation: {len(X_val)} images")
print(f"Test: {len(X_test)} images")

# 4. Fonction pour copier les fichiers dans le dossier de sortie
def copy_files(paths, labels, subset):
    for path, label in zip(paths, labels):
        dest_dir = os.path.join(output_dir, subset, label)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy(path, dest_dir)

# 5. Copier les images dans les dossiers train, val, test
copy_files(X_train, y_train, 'train')
copy_files(X_val, y_val, 'val')
copy_files(X_test, y_test, 'test')

print("Séparation et copie terminées avec succès !")