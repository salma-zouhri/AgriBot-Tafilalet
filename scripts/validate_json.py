"""
Script pour valider et tester le fichier disease_info.json
"""

import json
import os
from pathlib import Path

def validate_disease_info_json(file_path="data/disease_info.json"):
    """
    Valide la structure et le contenu du fichier disease_info.json
    """
    print(f"Validation du fichier: {file_path}")
    print("=" * 50)
    
    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        print(f"❌ Fichier introuvable: {file_path}")
        return False
    
    try:
        # Charger le JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ Fichier JSON valide")
        
        # Vérifier les maladies attendues
        expected_diseases = [
            "apple_scab",
            "fire_blight", 
            "powdery_mildew",
            "black_rot",
            "cedar_apple_rust",
            "healthy"
        ]
        
        missing_diseases = []
        for disease in expected_diseases:
            if disease not in data:
                missing_diseases.append(disease)
        
        if missing_diseases:
            print(f"⚠️  Maladies manquantes: {', '.join(missing_diseases)}")
        else:
            print("✅ Toutes les maladies sont présentes")
        
        # Valider la structure de chaque maladie
        required_fields = ["nom", "description", "symptomes", "traitement", "prevention"]
        
        print("\nValidation de la structure:")
        for disease_key, disease_data in data.items():
            if disease_key == "metadata":
                continue
                
            print(f"\n📋 {disease_key}:")
            
            for field in required_fields:
                if field in disease_data:
                    if isinstance(disease_data[field], list):
                        print(f"  ✅ {field}: {len(disease_data[field])} éléments")
                    else:
                        print(f"  ✅ {field}: {disease_data[field][:50]}...")
                else:
                    print(f"  ❌ {field}: MANQUANT")
        
        # Statistiques générales
        print(f"\n📊 Statistiques:")
        total_diseases = len([k for k in data.keys() if k != "metadata"])
        print(f"  • Nombre de maladies: {total_diseases}")
        
        if "metadata" in data:
            metadata = data["metadata"]
            print(f"  • Version: {metadata.get('version', 'Non définie')}")
            print(f"  • Dernière MAJ: {metadata.get('derniere_mise_a_jour', 'Non définie')}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_disease_lookup(file_path="data/disease_info.json", disease_key="apple_scab"):
    """
    Test de recherche d'une maladie spécifique
    """
    print(f"\n🔍 Test de recherche: {disease_key}")
    print("-" * 30)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if disease_key in data:
            disease = data[disease_key]
            print(f"✅ Maladie trouvée: {disease['nom']}")
            print(f"📝 Description: {disease['description'][:100]}...")
            print(f"🔬 Type: {disease.get('type', 'Non spécifié')}")
            print(f"🌡️ Période critique: {disease.get('periode_critique', 'Non spécifiée')}")
            return True
        else:
            print(f"❌ Maladie '{disease_key}' introuvable")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def create_sample_json_if_missing(file_path="data/disease_info.json"):
    """
    Crée un fichier JSON d'exemple si il n'existe pas
    """
    if os.path.exists(file_path):
        print(f"✅ Le fichier {file_path} existe déjà")
        return
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Contenu minimal pour test
    sample_data = {
        "apple_scab": {
            "nom": "Tavelure du pommier",
            "description": "Maladie fongique causée par Venturia inaequalis",
            "symptomes": ["Taches sombres sur les feuilles", "Déformation des fruits"],
            "traitement": ["Fongicides", "Élimination des feuilles infectées"],
            "prevention": ["Variétés résistantes", "Taille régulière"]
        },
        "healthy": {
            "nom": "Pommier sain",
            "description": "État de santé normal du pommier",
            "symptomes": ["Feuillage vert", "Croissance normale"],
            "traitement": ["Maintenance préventive"],
            "prevention": ["Soins appropriés", "Surveillance"]
        }
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Fichier d'exemple créé: {file_path}")
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")

def main():
    """
    Fonction principale
    """
    print("🍎 Validation du fichier des maladies des pommiers")
    print("=" * 60)
    
    file_path = "data/disease_info.json"
    
    # Créer le fichier s'il n'existe pas
    create_sample_json_if_missing(file_path)
    
    # Valider le fichier
    if validate_disease_info_json(file_path):
        print("\n✅ Validation réussie!")
        
        # Tests de recherche
        test_diseases = ["apple_scab", "fire_blight", "healthy"]
        for disease in test_diseases:
            test_disease_lookup(file_path, disease)
    else:
        print("\n❌ Échec de la validation")
    
    print(f"\n📁 Pour utiliser ce fichier, copiez le contenu JSON fourni dans:")
    print(f"   {os.path.abspath(file_path)}")

if __name__ == "__main__":
    main()