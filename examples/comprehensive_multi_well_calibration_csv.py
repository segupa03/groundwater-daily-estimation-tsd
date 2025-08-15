#!/usr/bin/env python3
"""
Test complet pour la calibration multi-puits avec données CSV.

Ce test valide :
1. Chargement de données CSV multi-puits
2. Calibration avec plusieurs paires de puits
3. Validation des métriques de performance
4. Gestion des erreurs et cas limites
5. Comparaison des résultats entre différents modes
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from groundwater_estimation import (
    DataLoader, LocalRegionalDecomposition, PerformanceMetrics
)
from groundwater_estimation.core.data_loader import CSVLoader


class TestMultiWellCalibration:
    """Tests complets pour la calibration multi-puits."""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Génère des données CSV d'exemple pour les tests."""
        # Créer des données simulées pour 5 puits sur 6 mois
        start_date = datetime(2022, 5, 1)
        end_date = datetime(2022, 10, 31)
        date_range = pd.date_range(start_date, end_date, freq='D')
        
        # Puits de référence avec données quotidiennes
        reference_wells = ['REF_001', 'REF_002']
        # Puits d'observation avec données bi-hebdomadaires
        observation_wells = ['OBS_001', 'OBS_002', 'OBS_003']
        
        data = []
        
        # Générer données pour les puits de référence (quotidiennes)
        for well in reference_wells:
            for date in date_range:
                # Niveau d'eau simulé avec tendance et saisonnalité
                days_from_start = (date - start_date).days
                trend = -0.01 * days_from_start  # Tendance décroissante
                seasonal = 2 * np.sin(2 * np.pi * days_from_start / 365)
                noise = np.random.normal(0, 0.5)
                water_level = -15 + trend + seasonal + noise
                
                data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Well_ID': well,
                    'Water_Level': round(water_level, 2),
                    'TreatmentUnit': 1,
                    'Type': 'Reference'
                })
        
        # Générer données pour les puits d'observation (bi-hebdomadaires)
        for well in observation_wells:
            # Sélectionner une date sur deux pour simuler des mesures bi-hebdomadaires
            observation_dates = date_range[::14]
            
            for date in observation_dates:
                days_from_start = (date - start_date).days
                trend = -0.01 * days_from_start
                seasonal = 2 * np.sin(2 * np.pi * days_from_start / 365)
                # Ajouter une variation locale spécifique au puits
                local_variation = np.random.normal(0, 1)
                noise = np.random.normal(0, 0.8)
                water_level = -18 + trend + seasonal + local_variation + noise
                
                data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Well_ID': well,
                    'Water_Level': round(water_level, 2),
                    'TreatmentUnit': 1,
                    'Type': 'Observation'
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Sauvegarder temporairement
        csv_path = "tests/temp_multi_well_data.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        yield csv_path
        
        # Nettoyer après les tests
        if os.path.exists(csv_path):
            os.remove(csv_path)
    
    @pytest.fixture
    def data_loader(self, sample_csv_data):
        """Chargeur de données pour les tests."""
        return DataLoader(sample_csv_data)
    
    @pytest.fixture
    def decomposition(self, data_loader):
        """Instance de décomposition pour les tests."""
        return LocalRegionalDecomposition(data_loader)
    
    @pytest.fixture
    def performance_metrics(self):
        """Instance de métriques de performance pour les tests."""
        return PerformanceMetrics()
    
    def test_data_loading_multi_well(self, data_loader):
        """Test du chargement de données multi-puits."""
        # Vérifier que les données sont chargées
        assert data_loader.data is not None
        assert len(data_loader.data) > 0
        
        # Vérifier la structure des données
        expected_columns = ['Date', 'Well_ID', 'Water_Level', 'TreatmentUnit', 'Type']
        for col in expected_columns:
            assert col in data_loader.data.columns
        
        # Vérifier qu'il y a plusieurs puits
        unique_wells = data_loader.data['Well_ID'].unique()
        assert len(unique_wells) >= 5  # Au moins 5 puits
        
        # Vérifier qu'il y a des puits de référence et d'observation
        well_types = data_loader.data['Type'].unique()
        assert 'Reference' in well_types
        assert 'Observation' in well_types
        
        print(f"✅ Données chargées : {len(data_loader.data)} enregistrements")
        print(f"✅ Puits uniques : {len(unique_wells)}")
        print(f"✅ Types de puits : {list(well_types)}")
    
    def test_calibration_mode_single_pair(self, decomposition, performance_metrics):
        """Test de calibration avec une seule paire de puits."""
        # Tester avec une paire de puits
        results = decomposition.estimate_daily_values(
            target_well="OBS_001",
            reference_well="REF_001",
            treatment_unit=1,
            year=2022,
            mode="calibration"
        )
        
        # Vérifier la structure des résultats
        assert 'observed' in results
        assert 'estimated' in results
        assert 'dates' in results
        assert 'decomposition' in results
        
        # Vérifier que les données ne sont pas vides
        assert len(results['observed']) > 0
        assert len(results['estimated']) > 0
        assert len(results['dates']) > 0
        
        # Calculer les métriques de performance
        metrics = performance_metrics.calculate_all_metrics(
            results['observed'], 
            results['estimated']
        )
        
        # Vérifier que les métriques sont calculées
        expected_metrics = ['rmse', 'r2', 'nash_sutcliffe', 'mape', 'bias']
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
        
        print(f"✅ Calibration réussie pour OBS_001/REF_001")
        print(f"✅ Métriques : RMSE={metrics['rmse']:.3f}, R²={metrics['r2']:.3f}")
    
    def test_calibration_mode_multiple_pairs(self, decomposition, performance_metrics):
        """Test de calibration avec plusieurs paires de puits."""
        # Définir les paires à tester
        well_pairs = [
            ("OBS_001", "REF_001"),
            ("OBS_002", "REF_001"),
            ("OBS_003", "REF_002"),
        ]
        
        all_results = {}
        
        for target_well, reference_well in well_pairs:
            try:
                results = decomposition.estimate_daily_values(
                    target_well=target_well,
                    reference_well=reference_well,
                    treatment_unit=1,
                    year=2022,
                    mode="calibration"
                )
                
                # Calculer les métriques
                metrics = performance_metrics.calculate_all_metrics(
                    results['observed'], 
                    results['estimated']
                )
                
                all_results[f"{target_well}_vs_{reference_well}"] = {
                    'results': results,
                    'metrics': metrics
                }
                
                print(f"✅ {target_well} vs {reference_well}: R²={metrics['r2']:.3f}")
                
            except Exception as e:
                print(f"❌ Erreur pour {target_well} vs {reference_well}: {e}")
                raise
        
        # Vérifier que tous les tests ont réussi
        assert len(all_results) == len(well_pairs)
        
        # Analyser la cohérence des résultats
        r2_values = [result['metrics']['r2'] for result in all_results.values()]
        print(f"✅ R² moyen : {np.mean(r2_values):.3f}")
        print(f"✅ R² min : {np.min(r2_values):.3f}")
        print(f"✅ R² max : {np.max(r2_values):.3f}")
    
    def test_estimation_mode_consistency(self, decomposition):
        """Test de cohérence entre les modes calibration et estimation."""
        # Tester en mode calibration
        cal_results = decomposition.estimate_daily_values(
            target_well="OBS_001",
            reference_well="REF_001",
            treatment_unit=1,
            year=2022,
            mode="calibration"
        )
        
        # Tester en mode estimation
        est_results = decomposition.estimate_daily_values(
            target_well="OBS_001",
            reference_well="REF_001",
            treatment_unit=1,
            year=2022,
            mode="estimation"
        )
        
        # Vérifier que les résultats sont cohérents
        assert len(cal_results['estimated']) == len(est_results['estimated'])
        assert len(cal_results['dates']) == len(est_results['dates'])
        
        # Les estimations devraient être identiques (même données)
        np.testing.assert_array_almost_equal(
            cal_results['estimated'], 
            est_results['estimated'], 
            decimal=10
        )
        
        print("✅ Cohérence entre modes calibration et estimation vérifiée")
    
    def test_error_handling_invalid_wells(self, decomposition):
        """Test de gestion des erreurs avec des puits invalides."""
        # Tester avec un puits cible inexistant
        with pytest.raises(Exception):
            decomposition.estimate_daily_values(
                target_well="PUITS_INEXISTANT",
                reference_well="REF_001",
                treatment_unit=1,
                year=2022
            )
        
        # Tester avec un puits de référence inexistant
        with pytest.raises(Exception):
            decomposition.estimate_daily_values(
                target_well="OBS_001",
                reference_well="REF_INEXISTANT",
                treatment_unit=1,
                year=2022
            )
        
        print("✅ Gestion des erreurs pour puits invalides vérifiée")
    
    def test_performance_benchmark(self, decomposition, performance_metrics):
        """Test de performance et benchmark."""
        import time
        
        # Mesurer le temps d'exécution pour plusieurs paires
        well_pairs = [
            ("OBS_001", "REF_001"),
            ("OBS_002", "REF_001"),
            ("OBS_003", "REF_002"),
        ]
        
        execution_times = []
        
        for target_well, reference_well in well_pairs:
            start_time = time.time()
            
            results = decomposition.estimate_daily_values(
                target_well=target_well,
                reference_well=reference_well,
                treatment_unit=1,
                year=2022,
                mode="calibration"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            print(f"⏱️  {target_well} vs {reference_well}: {execution_time:.3f}s")
        
        # Vérifier que les temps d'exécution sont raisonnables
        avg_time = np.mean(execution_times)
        max_time = np.max(execution_times)
        
        assert avg_time < 5.0  # Moins de 5 secondes en moyenne
        assert max_time < 10.0  # Moins de 10 secondes au maximum
        
        print(f"✅ Performance : Temps moyen = {avg_time:.3f}s, Max = {max_time:.3f}s")
    
    def test_data_quality_validation(self, data_loader):
        """Test de validation de la qualité des données."""
        data = data_loader.data
        
        # Vérifier qu'il n'y a pas de valeurs manquantes dans les colonnes critiques
        critical_columns = ['Date', 'Well_ID', 'Water_Level']
        for col in critical_columns:
            missing_count = data[col].isnull().sum()
            assert missing_count == 0, f"Valeurs manquantes dans {col}: {missing_count}"
        
        # Vérifier que les dates sont valides
        data['Date'] = pd.to_datetime(data['Date'])
        assert data['Date'].dt.year.min() >= 2020
        assert data['Date'].dt.year.max() <= 2030
        
        # Vérifier que les niveaux d'eau sont dans une plage raisonnable
        water_levels = data['Water_Level']
        assert water_levels.min() > -100  # Pas de valeurs extrêmement négatives
        assert water_levels.max() < 100   # Pas de valeurs extrêmement positives
        
        print("✅ Validation de la qualité des données réussie")
        print(f"✅ Plage de dates : {data['Date'].min()} à {data['Date'].max()}")
        print(f"✅ Plage de niveaux d'eau : {water_levels.min():.2f} à {water_levels.max():.2f}")


def test_integration_workflow():
    """Test d'intégration du workflow complet."""
    print("\n🧪 TEST D'INTÉGRATION COMPLET")
    print("=" * 50)
    
    # Ce test sera exécuté séparément pour valider le workflow complet
    # Il peut être utilisé pour des tests d'intégration plus longs
    
    assert True  # Placeholder pour le moment
    print("✅ Test d'intégration configuré")


if __name__ == "__main__":
    # Exécuter les tests si le script est lancé directement
    pytest.main([__file__, "-v", "--tb=short"]) 