# =============================================================================
# Single Well Calibration - CSV Data
# Equivalent R script base sur single_well_calibration_csv.py
# =============================================================================

# Installer reticulate, tcltk, ggplot2
# !!!!!!!!! JUSTE LA PREMI?RE FOIS !!!!!!!!!
install.packages("reticulate")
install.packages("ggplot2")

# Import packages de R
library(reticulate)
library(tcltk)
library(ggplot2)

# Utiliser l'environnement conda
reticulate::use_condaenv("tsd_env", required = TRUE)

# Installer le module avec pip
# !!!!!!!!! JUSTE LA PREMIERE FOIS !!!!!!!!! 
py_install("pip")

# Installer module via subprocess.
# !!!!!!!!! JUSTE LA PREMIERE FOIS !!!!!!!!! 
cat("Installation du module groundwater-estimation-tsd...\n")
system("python -m pip install git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git")

# Methode alternative. 
# !!!!!!!!! JUSTE LA PREMIERE FOIS !!!!!!!!! 
#py_run_string("import subprocess; subprocess.check_call(['pip', 'install', 'git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git'])")

# Importer le module groundwater_estimation
groundwater <- import("groundwater_estimation")
cat("Module Python import? dans R !")

# =============================================================================
# 1. CONFIGURATION DES DONNEES
# =============================================================================

# Ouvrir la boite de dialogue pour selectionner le fichier sample_data.csv
# Selection du fichier de donnees
cat("Selection du fichier de donnees...\n")
path_to_database <- tk_choose.files(
  caption = "???? Selectionnez votre fichier de donnees",
  multi = FALSE,
  filters = matrix(c("Fichiers CSV", "*.csv", 
                     "Fichiers SQLite", "*.sqlite", 
                     "Fichiers Excel", "*.xlsx",
                     "Tous les fichiers", "*.*"), 
                   ncol = 2, byrow = TRUE)
)

# =============================================================================
# 2. INITIALISATION DU MODULE
# =============================================================================

# Charger les classes necessaires
DataLoader <- groundwater$DataLoader
LocalRegionalDecomposition <- groundwater$LocalRegionalDecomposition
PerformanceMetrics <- groundwater$PerformanceMetrics

# Charger les donnees
cat("\nChargement des donnees...\n")
loader <- DataLoader(path_to_database)
decomposition <- LocalRegionalDecomposition(loader)
metrics <- PerformanceMetrics()

# Parametres du test
target_well <- "H"          # Puits cible (avec données limitées)
reference_well <- "C"       # Puits de référence (avec données journalières)
treatment_unit <- 10        # Unité de traitement (basin)
year <- 2013                # Année
start_date <- "2013-05-30"
end_date <- "2013-10-10"

cat("Configuration :\n")
cat("   - Puits cible :", target_well, "\n")
cat("   - Puits de reference :", reference_well, "\n")
cat("   - Unite de traitement :", treatment_unit, "\n")
cat("   - Annee :", year, "\n")
cat("   - Periode :", start_date, "jusqu'à", end_date, "\n")

# =============================================================================
# 3. ESTIMATION DES VALEURS JOURNALIERES
# =============================================================================

cat("\nEstimation en cours...\n")

# Effectuer la decomposition et l'estimation (mode detecte automatiquement)
results <- decomposition$estimate_daily_values(
  target_well = target_well,
  reference_well = reference_well,
  treatment_unit = treatment_unit,
  year = year,
  start_date = start_date,
  end_date = end_date  # Optionnel
)

cat("Estimation terminee\n")

# =============================================================================
# 4. CALCUL DES METRIQUES DE PERFORMANCE
# =============================================================================

cat("\nCalcul des metriques de performance...\n")

# Detecter les colonnes automatiquement
column_mapping <- loader$`_detect_column_names`(results)
col_nappe <- column_mapping$water_level

if (is.null(col_nappe)) {
  stop("Impossible de detecter la colonne du niveau d'eau (nappe) dans les resultats.")
}

# Extraire les valeurs observees et estimees
# Les resultats sont deja des objets R, pas besoin de py_to_r()
observed <- as.numeric(results[[col_nappe]])
estimated <- as.numeric(results$estimated)

# Verifier que les donnees sont valides
if (length(observed) == 0 || length(estimated) == 0) {
  stop("Erreur : Aucune donnee observee ou estimee trouvee.")
}

if (length(observed) != length(estimated)) {
  stop("Erreur : Le nombre de valeurs observees et estimees ne correspond pas.")
}

cat("???? Donnees extraites :\n")
cat("   - Valeurs observees :", length(observed), "\n")
cat("   - Valeurs estimees :", length(estimated), "\n")
cat("   - Type observees :", class(observed), "\n")
cat("   - Type estimees :", class(estimated), "\n")

# Calculer toutes les metriques de performance
# Convertir les vecteurs R en arrays numpy Python
# !!!!!!!!! JUSTE LA PREMIERE FOIS
py_run_string("import numpy as np")

observed_py <- py_run_string("observed_array = np.array(r.observed)", local = TRUE)$observed_array
estimated_py <- py_run_string("estimated_array = np.array(r.estimated)", local = TRUE)$estimated_array

performance <- metrics$calculate_all_metrics(observed_py, estimated_py)

# =============================================================================
# 5. AFFICHAGE DES RESULTATS
# =============================================================================

cat("\nRESULTATS DE L'ESTIMATION :\n")
cat("=" %+% rep("=", 50) %+% "\n")

# Afficher les metriques
for (nom in names(performance)) {
  valeur <- performance[[nom]]
  cat(sprintf("%-20s: %8.4f\n", nom, valeur))
}

cat("=" %+% rep("=", 50) %+% "\n")

# =============================================================================
# 6. VISUALISATION DES RESULTATS
# =============================================================================

cat("\nCreation des graphiques...\n")

# Convertir les resultats en DataFrame R pour ggplot2 ?
# Les resultats sont deje un DataFrame R, pas besoin de py_to_r()
results_df <- results

# Graphique 1 : Hydrogramme
p1 <- ggplot(results_df, aes(x = Date)) +
  geom_line(aes(y = !!sym(col_nappe), color = "Observed"), size = 1) +
  geom_line(aes(y = estimated, color = "Estimated"), size = 1, linetype = "dashed") +
  labs(
    title = paste("Hydrograph - Wells", target_well),
    subtitle = paste("From :", start_date, "to", end_date),
    x = "Date",
    y = "Water table depth (cm)",
    color = "Type"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold"),
    plot.subtitle = element_text(size = 12),
    legend.position = "bottom"
  ) +
  scale_color_manual(values = c("Observed" = "blue", "Estimated" = "red"))

print(p1)

# Graphique 2 : Comparaison observes vs estimes
p2 <- ggplot(results_df, aes_string(x = col_nappe, y = "estimated")) +
  geom_point(color = "purple", size = 2, alpha = 0.7) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "black") +
  labs(
    title = "Comparison of Observed vs. Estimated Values",
    x = "Observed (m)",
    y = "Estimated (m)"
  ) +
  theme_minimal() +
  theme(plot.title = element_text(size = 14, face = "bold"))

print(p2)

# =============================================================================
# FIN
# =============================================================================
