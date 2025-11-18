#!/bin/bash
#SBATCH --job-name=tiles_processing        # A short name for your job
#SBATCH --partition=4vcpu                 # Partition/queue to use
#SBATCH --time=3-05:29:00                  # Max runtime (D-HH:MM:SS)
#SBATCH --nodes=1                          # Number of nodes
#SBATCH --ntasks=1                         # Number of tasks (MPI processes)
#SBATCH --cpus-per-task=4                  # Number of CPU cores per task
#SBATCH --output=600.out           # Standard output log file

## ===============================================
## READ CONFIG FILE
## ===============================================

## Check for config file argument
if [ $# -lt 1 ]; then
    echo "❌ Error: No config file provided."
    echo "Usage: $0 <config_file.json>"
    exit 1
fi

CONFIG_FILE="$1"

## Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file '$CONFIG_FILE' not found."
    exit 1
fi

echo "✅ Using config file: $CONFIG_FILE"
echo "⏳ Starting tile processing workflow..."
echo "==============================================="

## ===============================================
## EXECUTE PYTHON SCRIPTS (QGIS & MRPM ENVIRONMENTS)
## ===============================================

## srun conda run -n qgis_env python 01_create_clark_vrt.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 01_create_deltadtm_vrt.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 01_create_gmw_vrt.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 02_processing_tiles_noponds.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 03_process_clark.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 04_process_gtsm.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 04_process_elevation.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 04_process_intertidal_space.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 04_process_accommodation_space.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 05_process_gmw.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 05_process_historical_gmw.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 05_process_recruitment_gmw.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 06_decrease_gmw_resolution.py "$CONFIG_FILE"
## srun conda run -n mrpm_env python 06_process_gmw_proximity.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 06_normalization_gmw_proximity.py "$CONFIG_FILE"
srun conda run -n mrpm_env python 07_process_coastline_rivers_distance.py "$CONFIG_FILE"
srun conda run -n qgis_env python 07_normalization_coastline.py "$CONFIG_FILE"
srun conda run -n qgis_env python 07_normalization_rivers.py "$CONFIG_FILE"
## srun conda run -n mrpm_env python 08_clip_subsidence.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 08_process_subsidence.py "$CONFIG_FILE"
## srun conda run -n mrpm_env python 09_process_landcover.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 10_process_permanent_water.py "$CONFIG_FILE"
## srun conda run -n qgis_env python 11_process_empty_areas.py "$CONFIG_FILE"
srun conda run -n qgis_env python 11_process_no_valid_areas.py "$CONFIG_FILE"
srun conda run -n qgis_env python 12_process_mangrove_potential_areas.py "$CONFIG_FILE"
## srun conda run -n mrpm_env python 13_calculate_statistics.py "$CONFIG_FILE"
## srun conda run -n mrpm_env python 14_create_visualization.py "$CONFIG_FILE"
srun conda run -n mrpm_env python 15_process_cog_files.py "$CONFIG_FILE"

echo "✅ All scripts completed successfully!"
echo "==============================================="