import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
import os

# Paramètres
IMG_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 30
DATA_DIR = 'data/data_split'

# Vérifier structure des dossiers
if not os.path.exists(DATA_DIR):
    raise ValueError("Le dossier data/apple/ n'existe pas.")

# Data augmentation + normalisation
datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

# Générateurs
train_generator = datagen.flow_from_directory(
    DATA_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)
val_generator = datagen.flow_from_directory(
    DATA_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

# Création du modèle CNN
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
    MaxPooling2D(2,2),
    
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    
    Conv2D(128, (3,3), activation='relu'),
    MaxPooling2D(2,2),

    Flatten(),
    Dropout(0.5),
    Dense(128, activation='relu'),
    Dense(4, activation='softmax')  # 4 classes
])

# Compilation
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Sauvegarder le meilleur modèle
checkpoint = ModelCheckpoint('model/plant_disease_model.h5', monitor='val_accuracy', save_best_only=True)

# Entraînement
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    callbacks=[checkpoint]
)

# Évaluer sur la validation
val_loss, val_acc = model.evaluate(val_generator)
print(f"✅ Validation accuracy: {val_acc*100:.2f}%")

# Afficher les classes
print("✅ Classes détectées :", train_generator.class_indices)