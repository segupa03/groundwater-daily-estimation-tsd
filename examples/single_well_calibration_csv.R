# =============================================================================
# Single Well Calibration - CSV Data
# Equivalent R script basé sur single_well_calibration_csv.py
# =============================================================================

# Installer et charger reticulate
if (!require(reticulate)) {
  install.packages("reticulate", type = "binary")
  library(reticulate)
}

# Installer le module Python
cat("🔄 Installation du module groundwater-estimation-tsd...\n")
py_run_string("
import subprocess
import sys
try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git'])
    print('✅ Module installé avec succès')
except Exception as e:
    print(f'❌ Erreur installation: {e}')
")

# Importer le module Python
cat("🔄 Importation du module...\n")
groundwater <- import("groundwater_estimation")

# Charger les classes nécessaires
DataLoader <- groundwater$DataLoader
LocalRegionalDecomposition <- groundwater$LocalRegionalDecomposition
PerformanceMetrics <- groundwater$PerformanceMetrics

# =============================================================================
# CONFIGURATION DES DONNÉES
# =============================================================================

# Sélection du fichier de données
cat("📁 Sélection du fichier de données...\n")

# Charger tcltk pour la sélection de fichier
if (!require(tcltk)) {
  install.packages("tcltk")
  library(tcltk)
}

# Ouvrir la boîte de dialogue pour sélectionner le fichier
path_to_database <- tk_choose.files(
  caption = "🌊 Sélectionnez votre fichier de données",
  multi = FALSE,
  filters = matrix(c("Fichiers CSV", "*.csv", 
                     "Fichiers SQLite", "*.sqlite", 
                     "Fichiers Excel", "*.xlsx",
                     "Tous les fichiers", "*.*"), 
                   ncol = 2, byrow = TRUE)
)

# Vérifier si un fichier a été sélectionné
if (length(path_to_database) == 0) {
  cat("❌ Aucun fichier sélectionné. Utilisation du fichier par défaut.\n")
  path_to_database <- "./data/sample_data/sample_data.csv"
} else {
  cat("✅ Fichier sélectionné :", path_to_database, "\n")
}

# Alternatives (décommentez selon vos besoins) :
# path_to_database <- "S:/Seb-Académique/Doc/Donnees/St-Modeste/Final/UNITÉ.sqlite"
# path_to_database <- "/media/sebastian/My Passport/Seb-Académique/Doc/Donnees/St-Modeste/Final/UNITÉ.sqlite"

# Paramètres du test
target_well <- "well_A"
# target_well <- "E"  # Alternative
reference_well <- "well_B"
# reference_well <- "G"  # Alternative
treatment_unit <- 1
# treatment_unit <- 4  # Alternative
year <- 2017
start_date <- "2017-05-20"
end_date <- "2017-10-18"

cat("📊 Configuration :\n")
cat("   - Puits cible :", target_well, "\n")
cat("   - Puits de référence :", reference_well, "\n")
cat("   - Unité de traitement :", treatment_unit, "\n")
cat("   - Année :", year, "\n")
cat("   - Période :", start_date, "à", end_date, "\n")

# =============================================================================
# CHARGEMENT DES DONNÉES ET INITIALISATION
# =============================================================================

cat("\n🔄 Chargement des données...\n")

# Charger les données
loader <- DataLoader(path_to_database)
decomposition <- LocalRegionalDecomposition(loader)
metrics <- PerformanceMetrics()

cat("✅ Données chargées avec succès\n")

# =============================================================================
# ESTIMATION DES VALEURS JOURNALIÈRES
# =============================================================================

cat("\n🔄 Estimation en cours...\n")

# Effectuer la décomposition et l'estimation (mode détecté automatiquement)
results <- decomposition$estimate_daily_values(
  target_well = target_well,
  reference_well = reference_well,
  treatment_unit = treatment_unit,
  year = year,
  start_date = start_date
  # end_date = end_date  # Optionnel
)

cat("✅ Estimation terminée\n")

# =============================================================================
# CALCUL DES MÉTRIQUES DE PERFORMANCE
# =============================================================================

cat("\n🔄 Calcul des métriques de performance...\n")

# Détecter les colonnes automatiquement
column_mapping <- loader$`_detect_column_names`(results)
col_nappe <- column_mapping$water_level

if (is.null(col_nappe)) {
  stop("❌ Impossible de détecter la colonne du niveau d'eau (nappe) dans les résultats.")
}

# Extraire les valeurs observées et estimées
# Les résultats sont déjà des objets R, pas besoin de py_to_r()
observed <- as.numeric(results[[col_nappe]])
estimated <- as.numeric(results$estimated)

# Vérifier que les données sont valides
if (length(observed) == 0 || length(estimated) == 0) {
  stop("❌ Erreur : Aucune donnée observée ou estimée trouvée.")
}

if (length(observed) != length(estimated)) {
  stop("❌ Erreur : Le nombre de valeurs observées et estimées ne correspond pas.")
}

cat("📊 Données extraites :\n")
cat("   - Valeurs observées :", length(observed), "\n")
cat("   - Valeurs estimées :", length(estimated), "\n")
cat("   - Type observées :", class(observed), "\n")
cat("   - Type estimées :", class(estimated), "\n")

# Calculer toutes les métriques de performance
# Convertir les vecteurs R en arrays numpy Python
py_run_string("import numpy as np")

observed_py <- py_run_string("observed_array = np.array(r.observed)", local = TRUE)$observed_array
estimated_py <- py_run_string("estimated_array = np.array(r.estimated)", local = TRUE)$estimated_array

performance <- metrics$calculate_all_metrics(observed_py, estimated_py)

# =============================================================================
# AFFICHAGE DES RÉSULTATS
# =============================================================================

cat("\n📊 RÉSULTATS DE L'ESTIMATION :\n")
cat(paste(rep("=", 50), collapse = ""), "\n")

# Afficher les métriques
for (nom in names(performance)) {
  valeur <- performance[[nom]]
  cat(sprintf("%-20s: %8.4f\n", nom, valeur))
}

cat(paste(rep("=", 50), collapse = ""), "\n")

# =============================================================================
# VISUALISATION DES RÉSULTATS
# =============================================================================

cat("\n🔄 Création des graphiques...\n")

# Charger ggplot2
if (!require(ggplot2)) {
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
    title = paste("🌊 Hydrogramme - Puits", target_well),
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
    title = "📈 Comparaison Observé vs Estimé",
    x = "Observé (m)",
    y = "Estimé (m)"
  ) +
  theme_minimal() +
  theme(plot.title = element_text(size = 14, face = "bold"))

print(p2)

# =============================================================================
# EXPORT DES RÉSULTATS
# =============================================================================

cat("\n💾 Export des résultats...\n")

# Sauvegarder les résultats
output_file <- paste0("results_", target_well, "_", reference_well, "_", year, ".csv")
write.csv(results_df, output_file, row.names = FALSE)

cat("✅ Résultats exportés vers :", output_file, "\n")
cat("📊 Nombre de lignes :", nrow(results_df), "\n")

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================

cat("\n🎉 ANALYSE TERMINÉE AVEC SUCCÈS !\n")
cat(paste(rep("=", 50), collapse = ""), "\n")
cat("📋 Résumé :\n")
cat("   - Puits analysé :", target_well, "\n")
cat("   - Puits de référence :", reference_well, "\n")
cat("   - Période :", start_date, "à", end_date, "\n")
cat("   - Valeurs estimées :", nrow(results_df), "\n")
cat("   - Fichier de sortie :", output_file, "\n")
cat(paste(rep("=", 50), collapse = ""), "\n")

# =============================================================================
# NOTES D'UTILISATION
# =============================================================================

cat("\n💡 NOTES D'UTILISATION :\n")
cat("   - Ce script reproduit exactement single_well_calibration_csv.py\n")
cat("   - Modifiez les paramètres au début du script selon vos besoins\n")
cat("   - Les graphiques sont créés avec ggplot2 (style R)\n")
cat("   - Les résultats sont exportés en CSV\n")
cat("   - Pour d'autres puits, changez target_well et reference_well\n")
cat("\n🚀 Script R terminé avec succès !\n")
