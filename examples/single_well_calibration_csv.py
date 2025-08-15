import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from sklearn.metrics import mean_squared_error, r2_score
from groundwater_estimation import DataLoader, LocalRegionalDecomposition, PerformanceMetrics

# Load data
path_to_database = "./data/sample_data/sample_data.csv"
#path_to_database = "S:/Seb-Académique/Doc/Donnees/St-Modeste/Final/UNITÉ.sqlite"
#path_to_database = "/media/sebastian/My Passport/Seb-Académique/Doc/Donnees/St-Modeste/Final/UNITÉ.sqlite"
loader = DataLoader(path_to_database)
decomposition = LocalRegionalDecomposition(loader)
metrics = PerformanceMetrics()

# For this test, we simulate a well_C as a reference well. The well_A values 
# is used as target well.

# Get well data
target_well = "well_A"
#target_well = "E"
reference_well = "well_B"
#reference_well = "G"
treatment_unit = 1
#treatment_unit = 4 #4
year = 2017
start_date = "2017-05-20"
end_date = "2017-10-18"

# Perform decomposition and estimation (mode detected automatically)
results = decomposition.estimate_daily_values(
    target_well=target_well,
    reference_well=reference_well,
    treatment_unit=treatment_unit,
    year=year,
    start_date=start_date
    #end_date=end_date
)
# Calculate performance metrics
print(results)

column_mapping = loader._detect_column_names(results)
col_nappe = column_mapping.get('water_level')
if col_nappe is None:
    raise ValueError("Impossible de détecter la colonne du niveau d'eau (nappe) dans les résultats.")
observed = results[col_nappe]
estimated = results['estimated']
performance = metrics.calculate_all_metrics(observed, estimated)

# Print performance metrics
for nom, valeur in performance.items():
    print(f"{nom}: {valeur:.2f}")
