# =============================================================================
# Single Well Calibration - CSV Data
# Equivalent R script basé sur single_well_calibration_csv.py
# =============================================================================

# Installer reticulate, tcltk, ggplot2
# ????????? JUSTE LA PREMIÈRE FOIS
install.packages("reticulate")
install.packages("tcltk")
install.packages("ggplot2")

# Import packages de R
library(reticulate)
library(tcltk)
library(ggplot2)

# Vérifier Python
py_config()

# Installer le module avec pip (pas conda).
# ????????? JUSTE LA PREMIÈRE FOIS
py_install("pip")

# Installer module via subprocess.
# JUSTE LA PREMIÈRE FOIS
cat("???? Installation du module groundwater-estimation-tsd...\n")
py_run_string("import subprocess; subprocess.check_call(['pip', 'install', 'git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git'])")

# Ou méthode alternative. 
# ????????? JUSTE LA PREMIÈRE FOIS
#system("python -m pip install git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git")

# Importer le module groundwater_estimation
groundwater <- import("groundwater_estimation")
cat("??? Module Python importé dans R !")

# =============================================================================
# 1. CONFIGURATION DES DONNÉES
# =============================================================================

# Ouvrir la boîte de dialogue pour sélectionner le fichier sample_data.csv
# Sélection du fichier de données
cat("???? Sélection du fichier de données...\n")
path_to_database <- tk_choose.files(
  caption = "???? Sélectionnez votre fichier de données",
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

# Charger les classes nécessaires
DataLoader <- groundwater$DataLoader
LocalRegionalDecomposition <- groundwater$LocalRegionalDecomposition
PerformanceMetrics <- groundwater$PerformanceMetrics

# Charger les données
cat("\n???? Chargement des données...\n")
loader <- DataLoader(path_to_database)
decomposition <- LocalRegionalDecomposition(loader)
metrics <- PerformanceMetrics()

# Paramètres du test
target_well <- "well_A"
reference_well <- "well_B"
treatment_unit <- 1

year <- 2017
start_date <- "2017-05-20"
end_date <- "2017-10-18"

cat("???? Configuration :\n")
cat("   - Puits cible :", target_well, "\n")
cat("   - Puits de référence :", reference_well, "\n")
cat("   - Unité de traitement :", treatment_unit, "\n")
cat("   - Année :", year, "\n")
cat("   - Période :", start_date, "à", end_date, "\n")

# =============================================================================
# 3. ESTIMATION DES VALEURS JOURNALIÈRES
# =============================================================================

cat("\n???? Estimation en cours...\n")

# Effectuer la décomposition et l'estimation (mode détecté automatiquement)
results <- decomposition$estimate_daily_values(
  target_well = target_well,
  reference_well = reference_well,
  treatment_unit = treatment_unit,
  year = year,
  start_date = start_date
  # end_date = end_date  # Optionnel
)

cat("??? Estimation terminée\n")

# =============================================================================
# 4. CALCUL DES MÉTRIQUES DE PERFORMANCE
# =============================================================================

cat("\n???? Calcul des métriques de performance...\n")

# Détecter les colonnes automatiquement
column_mapping <- loader$`_detect_column_names`(results)
col_nappe <- column_mapping$water_level

if (is.null(col_nappe)) {
  stop("??? Impossible de détecter la colonne du niveau d'eau (nappe) dans les résultats.")
}

# Extraire les valeurs observées et estimées
# Les résultats sont déjà des objets R, pas besoin de py_to_r()
observed <- as.numeric(results[[col_nappe]])
estimated <- as.numeric(results$estimated)

# Vérifier que les données sont valides
if (length(observed) == 0 || length(estimated) == 0) {
  stop("??? Erreur : Aucune donnée observée ou estimée trouvée.")
}

if (length(observed) != length(estimated)) {
  stop("??? Erreur : Le nombre de valeurs observées et estimées ne correspond pas.")
}

cat("???? Données extraites :\n")
cat("   - Valeurs observées :", length(observed), "\n")
cat("   - Valeurs estimées :", length(estimated), "\n")
cat("   - Type observées :", class(observed), "\n")
cat("   - Type estimées :", class(estimated), "\n")

# Calculer toutes les métriques de performance
# Convertir les vecteurs R en arrays numpy Python
# ????????? JUSTE LA PREMIÈRE FOIS
py_run_string("import numpy as np")

observed_py <- py_run_string("observed_array = np.array(r.observed)", local = TRUE)$observed_array
estimated_py <- py_run_string("estimated_array = np.array(r.estimated)", local = TRUE)$estimated_array

performance <- metrics$calculate_all_metrics(observed_py, estimated_py)

# =============================================================================
# 5. AFFICHAGE DES RÉSULTATS
# =============================================================================

cat("\n???? RÉSULTATS DE L'ESTIMATION :\n")
cat("=" %+% rep("=", 50) %+% "\n")

# Afficher les métriques
for (nom in names(performance)) {
  valeur <- performance[[nom]]
  cat(sprintf("%-20s: %8.4f\n", nom, valeur))
}

cat("=" %+% rep("=", 50) %+% "\n")

# =============================================================================
# 6. VISUALISATION DES RÉSULTATS
# =============================================================================

cat("\n???? Création des graphiques...\n")

# Charger ggplot2
if (!require()) {
  install.packages("ggplot2")
  library(ggplot2)
}

# Convertir les résultats en DataFrame R pour ggplot2
# Les résultats sont déjà un DataFrame R, pas besoin de py_to_r()
results_df <- results

# Graphique 1 : Hydrogramme
p1 <- ggplot(results_df, aes(x = Date)) +
  geom_line(aes(y = !!sym(col_nappe), color = "Observé"), size = 1) +
  geom_line(aes(y = estimated, color = "Estimé"), size = 1, linetype = "dashed") +
  labs(
    title = paste("Hydrogramme - Puits", target_well),
    subtitle = paste("Période :", start_date, "à", end_date),
    x = "Date",
    y = "Niveau de la nappe (m)",
    color = "Type"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold"),
    plot.subtitle = element_text(size = 12),
    legend.position = "bottom"
  ) +
  scale_color_manual(values = c("Observé" = "blue", "Estimé" = "red"))

print(p1)

# Graphique 2 : Comparaison observé vs estimé
p2 <- ggplot(results_df, aes_string(x = col_nappe, y = "estimated")) +
  geom_point(color = "purple", size = 2, alpha = 0.7) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "black") +
  labs(
    title = "Comparaison Observé vs Estimé",
    x = "Observé (m)",
    y = "Estimé (m)"
  ) +
  theme_minimal() +
  theme(plot.title = element_text(size = 14, face = "bold"))

print(p2)

# =============================================================================
# FIN
# =============================================================================
