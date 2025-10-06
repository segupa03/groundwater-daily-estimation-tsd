# =============================================================================
# Single Well Estimation - CSV Data
# Script R pour l'estimation (mode "estimation") plutôt que la calibration
# =============================================================================

# Installer reticulate, tcltk, ggplot2
# !!!!!!!!! JUSTE LA PREMIÈRE FOIS !!!!!!!!!
# install.packages("reticulate")
# install.packages("ggplot2")

# Import packages de R
library(reticulate)
library(tcltk)
library(ggplot2)

# Utiliser l'environnement conda
reticulate::use_condaenv("tsd_env", required = TRUE)

# Installer le module avec pip
# !!!!!!!!! JUSTE LA PREMIERE FOIS !!!!!!!!! 
# py_install("pip")

# Installer module via subprocess.
# !!!!!!!!! JUSTE LA PREMIERE FOIS !!!!!!!!! 
# cat("Installation du module groundwater-estimation-tsd...\n")
# system("python -m pip install git+https://github.com/segupa03/groundwater-daily-estimation-tsd.git")

# Importer le module groundwater_estimation
groundwater <- import("groundwater_estimation")
cat("Module Python importé dans R !\n")

# =============================================================================
# 1. CONFIGURATION DES DONNÉES
# =============================================================================

# Ouvrir la boite de dialogue pour selectionner le fichier
cat("Sélection du fichier de données...\n")
path_to_database <- tk_choose.files(
  caption = "Sélectionnez votre fichier de données",
  multi = FALSE,
  filters = matrix(c("Fichiers CSV", "*.csv", 
                     "Fichiers SQLite", "*.sqlite", 
                     "Fichiers Excel", "*.xlsx",
                     "Tous les fichiers", "*.*"), 
                   ncol = 2, byrow = TRUE)
)

if (length(path_to_database) == 0) {
  stop("Aucun fichier sélectionné. Arrêt du script.")
}

cat("Fichier sélectionné:", path_to_database, "\n")

# =============================================================================
# 2. INITIALISATION DU MODULE
# =============================================================================

# Charger les classes nécessaires
DataLoader <- groundwater$DataLoader
LocalRegionalDecomposition <- groundwater$LocalRegionalDecomposition
PerformanceMetrics <- groundwater$PerformanceMetrics

# Charger les données
cat("\nChargement des données...\n")
loader <- DataLoader(path_to_database)
decomposition <- LocalRegionalDecomposition(loader)
metrics <- PerformanceMetrics()

# =============================================================================
# 3. CONFIGURATION DES PARAMÈTRES
# =============================================================================

# Paramètres du test - MODIFIER SELON VOS DONNÉES
target_well <- "D"             # Puits cible (avec données limitées - mesures manuelles)
reference_well <- "C"          # Puits de référence (avec données journalières - enregistreur)
treatment_unit <- 10           # Unité de traitement (basin)
year <- 2013                   # Année
start_date <- "2013-05-15"    
end_date <- "2013-10-07"      

cat("Configuration :\n")
cat("   - Puits cible :", target_well, "\n")
cat("   - Puits de référence :", reference_well, "\n")
cat("   - Unité de traitement :", treatment_unit, "\n")
cat("   - Année :", year, "\n")
cat("   - Période :", start_date, "jusqu'à", end_date, "\n")

# Vérifier que les puits existent
available_wells <- loader$get_available_wells()
cat("Puits disponibles :", paste(available_wells, collapse = ", "), "\n")

if (!target_well %in% available_wells) {
  stop("ERREUR: Puits cible '", target_well, "' non trouvé!")
}

if (!reference_well %in% available_wells) {
  stop("ERREUR: Puits de référence '", reference_well, "' non trouvé!")
}

cat("Tous les puits trouvés\n")

# =============================================================================
# 4. ESTIMATION DES VALEURS JOURNALIÈRES (MODE ESTIMATION)
# =============================================================================

cat("\nEstimation en cours (mode estimation)...\n")

# Effectuer la décomposition et l'estimation en mode "estimation"
# Le mode "estimation" utilise les fluctuations régionales du puits de référence
# au lieu des fluctuations locales du puits cible
results <- decomposition$estimate_daily_values(
  target_well = target_well,
  reference_well = reference_well,
  treatment_unit = treatment_unit,
  year = year,
  start_date = start_date,
  end_date = end_date,
  mode = "estimation"  # MODE ESTIMATION FORCÉ
)

cat("Estimation terminée\n")

# =============================================================================
# 5. ANALYSE DES RÉSULTATS
# =============================================================================

cat("\nAnalyse des résultats...\n")

# En mode estimation, on n'a pas de valeurs observées journalières
# On a seulement quelques points de mesures manuelles
cat("Données extraites :\n")
cat("   - Nombre de jours estimés :", nrow(results), "\n")
cat("   - Période d'estimation :", min(results$Date), "à", max(results$Date), "\n")

# Détecter les colonnes automatiquement
column_mapping <- loader$`_detect_column_names`(results)
col_nappe <- column_mapping$water_level

if (is.null(col_nappe)) {
  stop("Impossible de détecter la colonne du niveau d'eau (nappe) dans les résultats.")
}

cat("   - Colonne détectée pour le niveau d'eau :", col_nappe, "\n")


# =============================================================================
# 6. VISUALISATION DES RÉSULTATS
# =============================================================================

cat("\nCréation des graphiques...\n")

# Convertir les résultats en DataFrame R pour ggplot2
results_df <- results

# Charger les données originales pour obtenir les points observés (mesures manuelles)
original_data <- loader$load_data()
target_original <- original_data[original_data$Well_ID == target_well & 
                                 original_data$Basin == treatment_unit, ]

# Convertir les dates si nécessaire
if (is.character(target_original$Date)) {
  target_original$Date <- as.Date(target_original$Date, format = "%m/%d/%Y")
}

# Filtrer les données pour la période d'intérêt
target_original$Date <- as.Date(target_original$Date)
target_original <- target_original[target_original$Date >= as.Date(start_date) & 
                                  target_original$Date <= as.Date(end_date), ]

cat("   - Points observés (mesures manuelles) :", nrow(target_original), "\n")

# Graphique 1 : Hydrogramme avec courbe estimée et points observés
p1 <- ggplot(results_df, aes(x = Date)) +
  # Ligne de l'estimation journalière
  geom_line(aes(y = estimated), color = "red", size = 1, alpha = 0.8) +
  # Points des mesures manuelles observées
  geom_point(data = target_original, 
             aes(x = Date, y = !!sym(col_nappe)), 
             color = "blue", size = 3, alpha = 0.8) +
  labs(
    title = paste("Hydrograph - Well", target_well, "(Estimation mode)"),
    subtitle = paste("estimation (rouge) and observed points (bleu) - from:", start_date, "to", end_date),
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
  # Ajouter une légende manuelle
  annotate("text", x = Inf, y = Inf, 
           label = "Red: dairy estimation \nBlue: Manual measurements", 
           hjust = 1, vjust = 1, size = 3)

print(p1)

# =============================================================================
# 8. EXPORT DES RÉSULTATS
# =============================================================================

cat("\nExport des résultats...\n")

# Créer un nom de fichier pour l'export
output_filename <- paste0("estimation_results_", target_well, "_", year, ".csv")
output_path <- file.path(dirname(path_to_database), output_filename)

# Exporter les résultats
write.csv(results_df, output_path, row.names = FALSE)
cat("Résultats exportés vers:", output_path, "\n")

# =============================================================================
# 9. RÉSUMÉ FINAL
# =============================================================================

cat("\nESTIMATION TERMINÉE AVEC SUCCÈS !\n")
cat("=====================================\n")
cat("Mode utilisé : ESTIMATION\n")
cat("Puits cible :", target_well, "(mesures manuelles)\n")
cat("Puits de référence :", reference_well, "(données journalières)\n")
cat("Période :", start_date, "à", end_date, "\n")
cat("Nombre de jours estimés :", nrow(results), "\n")
cat("Points observés (mesures manuelles) :", nrow(target_original), "\n")
cat("Fichier de résultats :", output_path, "\n")

cat("\nScript terminé avec succès !\n")

# =============================================================================
# FIN
# =============================================================================
