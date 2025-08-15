#!/usr/bin/env python3
"""
Test script pour la détection automatique des colonnes.
Ce script démontre comment éviter le hard-coding des noms de colonnes.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from groundwater_estimation import DataLoader

def test_column_detection():
    """Test de la détection automatique des colonnes."""
    
    # Chemin vers votre base de données#
    # Utilisation d'un chemin relatif au projet
    project_root = os.path.dirname(os.path.dirname(__file__))
    database_path = os.path.join(project_root, "data", "sample_data", "sample_data.xlsx")
    
    print(f"Recherche de la base de données à: {database_path}")
    
    try:
        # Créer le loader
        loader = DataLoader(database_path)
        
        print("=== Test de détection automatique des colonnes ===\n")
        
        # Afficher les informations sur les colonnes détectées
        loader.print_column_info()
        
        # Obtenir le mapping des colonnes
        column_mapping = loader.get_column_mapping()
        
        print(f"\n=== Utilisation du mapping des colonnes ===")
        print("Au lieu de hard-coder 'Jour', 'Nappe', etc., utilisez:")
        print(f"  Date column: {column_mapping.get('date', 'Non détectée')}")
        print(f"  Water level column: {column_mapping.get('water_level', 'Non détectée')}")
        
        # Exemple d'utilisation dynamique
        print(f"\n=== Exemple d'utilisation dynamique ===")
        
        # Charger les données
        df = loader.load_data()
        
        # Utiliser les colonnes détectées au lieu de noms hard-codés
        date_col = column_mapping.get('date')
        water_level_col = column_mapping.get('water_level')
        
        if date_col and water_level_col:
            print(f"  Colonne de date détectée: {date_col}")
            print(f"  Colonne de niveau d'eau détectée: {water_level_col}")
            
            # Exemple: calculer la moyenne du niveau d'eau
            if water_level_col in df.columns:
                mean_level = df[water_level_col].mean()
                print(f"  Niveau d'eau moyen: {mean_level:.2f}")
            
            # Exemple: compter les dates uniques
            if date_col in df.columns:
                unique_dates = df[date_col].nunique()
                print(f"  Nombre de dates uniques: {unique_dates}")
        else:
            print("  ⚠️  Certaines colonnes essentielles n'ont pas été détectées")
            print(f"  Colonnes disponibles: {list(df.columns)}")
        
    except FileNotFoundError:
        print(f"❌ Base de données non trouvée: {database_path}")
        print("Veuillez modifier le chemin dans le script")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_column_detection() 