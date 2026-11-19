# AgriBot Tafilalet

## Présentation

AgriBot Tafilalet est une application web Flask conçue pour aider les producteurs de pommes dans l’analyse des maladies des feuilles et l’orientation de l’irrigation. L’application propose une interface accessible depuis un navigateur avec gestion des comptes utilisateurs, chatbot d’assistance agricole, analyse d’images, recommandations d’irrigation et historique des activités.

## Fonctionnalités

### Classification des maladies des feuilles de pommier

Les utilisateurs peuvent envoyer une image `.jpg`, `.jpeg` ou `.png` d’une feuille de pommier. L’application prétraite l’image, la transmet à un réseau neuronal convolutif (CNN) TensorFlow/Keras et renvoie l’une des quatre classes suivantes :

- `Apple_scab`
- `Black_rot`
- `Cedar_apple_rust`
- `Healthy`

La réponse contient la classe prédite, une valeur de confiance et les informations correspondantes issues du fichier JSON des maladies : description, symptômes, causes, prévention et recommandation.

L’endpoint de prédiction enregistre également l’image envoyée dans `static/uploads/` et peut enregistrer l’analyse dans l’historique de l’utilisateur authentifié.

### Chatbot agricole basé sur des règles

Le chatbot n’est pas un système d’IA générative. Il utilise un ensemble fixe de règles fondées sur des mots-clés, implémentées dans Flask. Selon les mots présents dans le message de l’utilisateur, il renvoie des réponses prédéfinies concernant les salutations, l’analyse des maladies, l’irrigation, l’aide ou les remerciements. Les messages ne correspondant à aucune règle reçoivent une réponse prédéfinie de secours.

### Recommandation d’irrigation

L’endpoint `/irrigation` accepte quatre paramètres :

- l’humidité du sol : `Sec`, `Optimal` ou `Humide` ;
- la température en degrés Celsius ;
- l’humidité de l’air en pourcentage ;
- le nombre de jours écoulés depuis la dernière irrigation.

L’application valide les données et calcule un score d’irrigation à l’aide de règles fixes portant sur l’humidité du sol, la température, l’humidité de l’air et le temps écoulé. Le score détermine le niveau d’urgence, la quantité d’irrigation suggérée, le délai avant la prochaine vérification et des conseils supplémentaires. La route Flask actuelle utilise cette fonction de calcul heuristique ; elle n’appelle pas le modèle d’irrigation chargé au démarrage.

### Comptes, réinitialisation du mot de passe et historique

L’application propose :

- l’inscription et la connexion des utilisateurs ;
- le hachage des mots de passe avec Werkzeug ;
- la déconnexion et l’accès basé sur les sessions ;
- des liens de réinitialisation du mot de passe valables une heure ;
- l’envoi facultatif de courriels de réinitialisation via Gmail SMTP à l’aide de variables d’environnement ;
- un historique par utilisateur des connexions, messages du chatbot, analyses d’images et demandes d’irrigation ;
- la consultation et l’effacement de l’historique pour l’utilisateur authentifié.

Les comptes et l’historique sont stockés dans une base de données SQLite locale nommée `users.db`.

## Technologies

- Python
- Flask
- Flask-CORS
- TensorFlow / Keras
- NumPy
- Pillow, utilisé par le code de traitement des images
- Joblib, utilisé pour charger le fichier du modèle d’irrigation
- SQLite
- Hachage des mots de passe avec Werkzeug
- Modules de la bibliothèque standard Python pour les journaux, les sessions, les courriels et la validation

Le fichier actuel `requirements.txt` déclare Flask, Flask-CORS, Joblib, TensorFlow, NumPy, Werkzeug, Flask-Mail et PyJWT. Le code source importe également `python-dotenv` et Pillow. Les scripts d’entraînement importent en plus pandas et scikit-learn. Ces déclarations de dépendances doivent être vérifiées avant toute installation propre.

## Installation

1. Utiliser un environnement Python compatible.
2. Créer et activer un environnement virtuel, par exemple :

   ```bash
   python -m venv venv
   ```

   Sous Windows :

   ```powershell
   venv\\Scripts\\activate
   ```

3. Installer les dépendances déclarées par le projet :

   ```bash
   pip install -r requirements.txt
   ```

4. Avant de lancer l’application dans un environnement propre, s’assurer que les paquets supplémentaires importés par le code source (`python-dotenv` et Pillow) sont disponibles. Les scripts d’entraînement nécessitent également pandas et scikit-learn s’ils doivent être utilisés.

5. Fournir séparément les fichiers de modèles et de données nécessaires. Ils sont volontairement exclus de la publication GitHub par `.gitignore` et ne sont pas fournis dans cette préparation du dépôt :

   - `model/leaf_disease_cnn.h5`
   - `model/irrigation_model.pkl`
   - `data/disease_info.json`

## Configuration

Créer un fichier `.env` local pour les valeurs propres à l’environnement. Ne pas le versionner. L’application lit les variables suivantes :

- `SECRET_KEY` pour les sessions Flask ;
- `GMAIL_USER` pour l’envoi des courriels de réinitialisation ;
- `GMAIL_APP_PASSWORD` pour le mot de passe d’application Gmail utilisé par SMTP ;
- `PORT` pour remplacer le port par défaut.

L’application utilise par défaut le port `5000`, écoute sur `0.0.0.0` et démarre avec le mode debug Flask activé dans le code source actuel. Cette configuration doit être revue avant un déploiement en production.

## Lancement

Depuis la racine du projet, exécuter :

```bash
python app.py
```

Au démarrage, l’application initialise `users.db` si nécessaire, charge le modèle d’irrigation lorsque son fichier est disponible et charge le CNN ainsi que les informations sur les maladies lors de l’importation du module de prédiction. Ouvrir ensuite l’adresse de l’application dans un navigateur.

## Périmètre de publication

Cette préparation du dépôt ne publie pas les modèles locaux, les datasets, les bases de données SQLite, les images envoyées, les secrets, les environnements virtuels ni les fichiers d’archive. La propriété, les licences des sources, les conditions de redistribution et les éventuelles implications liées à la vie privée doivent être vérifiées séparément avant toute distribution.

Le fichier `data/disease_info.json` est le seul fichier du dossier `data/` actuellement autorisé à être suivi par Git. Son contenu et ses droits de redistribution doivent être vérifiés avant publication.

## État du projet

AgriBot Tafilalet est une application Flask spécifique à ce projet. Ce README décrit le comportement actuellement implémenté dans le code source et ne revendique aucune métrique de performance ni fonctionnalité absente du projet.
