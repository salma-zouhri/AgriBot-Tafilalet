# AgriBot Tafilalet

## Présentation

AgriBot Tafilalet est une application web Flask destinée à aider les producteurs de pommes dans l’analyse des maladies des feuilles et la recommandation d’irrigation.

Le dépôt contient :

- le code source de l’application Flask ;
- le modèle CNN `model/leaf_disease_cnn.h5` ;
- le modèle d’irrigation `model/irrigation_model.pkl` ;
- le dataset d’irrigation `data/smart_irrigation.csv` ;
- les informations descriptives sur les maladies dans `data/disease_info.json`.

Les images d’entraînement et de test PlantVillage situées dans `data/data_split/` ne sont pas incluses dans le dépôt.

## Fonctionnalités

### Classification des maladies des feuilles de pommier

L’utilisateur peut envoyer une image `.jpg`, `.jpeg` ou `.png` d’une feuille de pommier. L’application la prétraite puis utilise un réseau neuronal convolutif (CNN) TensorFlow/Keras pour produire une prédiction parmi quatre classes :

- `Apple_scab` ;
- `Black_rot` ;
- `Cedar_apple_rust` ;
- `Healthy`.

La réponse contient la classe prédite, une valeur de confiance ainsi que les informations correspondantes de `data/disease_info.json` : description, symptômes, causes, prévention et recommandation. L’image envoyée est enregistrée dans `static/uploads/`, qui reste exclu du dépôt.

### Chatbot agricole basé sur des règles

Le chatbot n’est pas une IA générative. Il applique des règles fixes fondées sur des mots-clés et renvoie des réponses prédéfinies concernant les salutations, l’analyse des maladies, l’irrigation, l’aide et les remerciements. Un message de secours est utilisé lorsqu’aucune règle ne correspond.

### Recommandation d’irrigation

L’endpoint `/irrigation` valide quatre paramètres :

- l’humidité du sol : `Sec`, `Optimal` ou `Humide` ;
- la température en degrés Celsius ;
- l’humidité de l’air en pourcentage ;
- le nombre de jours depuis la dernière irrigation.

La route Flask calcule ensuite un score heuristique à partir de ces valeurs. Ce score détermine le niveau d’urgence, la quantité d’irrigation suggérée, le délai avant la prochaine vérification et les conseils complémentaires.

Le fichier `model/irrigation_model.pkl` est présent dans le dépôt, mais le code actuel de l’endpoint `/irrigation` utilise la logique heuristique et n’appelle pas ce modèle pour produire sa recommandation.

### Gestion des comptes et historique utilisateur

L’application propose :

- l’inscription et la connexion des utilisateurs ;
- le hachage des mots de passe avec Werkzeug ;
- la gestion des sessions et la déconnexion ;
- la réinitialisation du mot de passe avec un lien valable une heure ;
- l’envoi facultatif de courriels de réinitialisation via Gmail SMTP ;
- l’enregistrement de l’historique des connexions, messages du chatbot, analyses d’images et demandes d’irrigation ;
- la consultation et l’effacement de l’historique de l’utilisateur authentifié.

Les comptes et l’historique sont stockés dans la base de données SQLite locale `users.db`, qui n’est pas publiée.

## Technologies

- Python ;
- Flask ;
- Flask-CORS ;
- TensorFlow / Keras pour la classification CNN ;
- NumPy ;
- Pillow pour le traitement des images ;
- Joblib pour le chargement du modèle d’irrigation ;
- SQLite pour les comptes et l’historique ;
- Werkzeug pour le hachage des mots de passe ;
- `python-dotenv` pour le chargement du fichier `.env` ;
- modules de la bibliothèque standard Python pour les sessions, journaux, courriels et validations.

Le fichier `requirements.txt` déclare également Flask-Mail et PyJWT. Les scripts d’entraînement utilisent en outre pandas et scikit-learn. Ces dépendances doivent être vérifiées dans l’environnement utilisé.

## Architecture du projet

```text
.
├── app.py                         # Application Flask, routes et logique métier
├── predict.py                     # Chargement du CNN et prédiction des maladies
├── model/
│   ├── leaf_disease_cnn.h5        # Modèle CNN publié
│   └── irrigation_model.pkl       # Modèle d’irrigation publié, non utilisé par la route actuelle
├── data/
│   ├── disease_info.json          # Informations sur les maladies publiées
│   └── smart_irrigation.csv       # Dataset d’irrigation publié
├── templates/                     # Pages HTML de l’application
├── static/                        # Ressources statiques et dossier local d’uploads
├── scripts/                       # Scripts utilitaires
├── traning/                       # Scripts d’entraînement et de préparation des modèles
├── requirements.txt               # Dépendances déclarées
└── README.md
```

Le dossier `data/data_split/`, qui contient les images PlantVillage d’entraînement, de validation et de test, n’est pas inclus dans le dépôt.

## Installation

### Cloner le dépôt

Depuis un terminal, exécuter :

```bash
git clone https://github.com/salma-zouhri/AgriBot-Tafilalet.git
cd AgriBot-Tafilalet
```

### Créer et activer un environnement virtuel sous Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Installer les dépendances

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

```powershell
pip install python-dotenv Pillow
```

Le code source importe également `python-dotenv` et Pillow, qui ne figurent pas dans le `requirements.txt` actuel. Dans un environnement propre, vérifier qu’ils sont disponibles avant le lancement. Les scripts d’entraînement nécessitent aussi pandas et scikit-learn s’ils sont utilisés.

## Configuration

Créer à la racine du projet un fichier local `.env`. Ne pas le publier. Les variables utilisées par l’application sont :

```dotenv
SECRET_KEY=remplacer_par_une_valeur_secrete
GMAIL_USER=adresse Gmail utilisée pour les courriels
GMAIL_APP_PASSWORD=mot_de_passe_d_application_Gmail
PORT=5000
```

`SECRET_KEY` sert aux sessions Flask. `GMAIL_USER` et `GMAIL_APP_PASSWORD` sont utilisés pour l’envoi des courriels de réinitialisation. `PORT` permet de remplacer le port par défaut `5000`.

L’application écoute sur `0.0.0.0` et le code source actuel active le mode debug Flask. Cette configuration doit être revue avant tout déploiement en production. Le projet n’est pas présenté comme déployé en production.

## Lancement

Depuis la racine du dépôt et avec l’environnement virtuel activé, exécuter :

```powershell
python app.py
```

L’application initialise `users.db` si nécessaire et utilise le port `5000` par défaut, sauf si `PORT` est défini dans l’environnement. Ouvrir ensuite l’adresse locale de l’application dans un navigateur.

## Périmètre de publication

Les modèles `model/leaf_disease_cnn.h5` et `model/irrigation_model.pkl`, le dataset `data/smart_irrigation.csv` et le fichier `data/disease_info.json` font partie du contenu publié du dépôt.

Les éléments suivants restent exclus de la publication :

- les images PlantVillage d’entraînement, de validation et de test de `data/data_split/` ;
- les images envoyées dans `static/uploads/` ;
- le fichier `.env` et les autres secrets ;
- les bases de données SQLite et leurs sauvegardes ;
- les environnements virtuels, caches Python et fichiers de sauvegarde.

Les droits d’utilisation et de redistribution du dataset d’irrigation, des informations sur les maladies et des modèles publiés doivent être vérifiés séparément. Ce README ne revendique aucune métrique de performance et ne présente pas l’application comme déployée en production.
