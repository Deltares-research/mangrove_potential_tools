#!/bin/bash

# Exit immediately if a command fails
set -e

# Load conda into the shell
source /opt/miniforge3/etc/profile.d/conda.sh

# Navigate to your project directory
cd /p/11211992-tki-mangrove-restoration/02_scripts_and_processing/mrpm_tools/workflow_linux

# Activate QGIS environment
conda activate qgis_env

# Read config file from command line argument
if [ $# -lt 1 ]; then
    echo "❌ Error: No config file provided."
    echo "Usage: $0 <config_file.json>"
    exit 1
fi

CONFIG_FILE="$1"

# Check if file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file '$CONFIG_FILE' not found."
    exit 1
fi

# # Create vrt files
# python 01_create_clark_vrt.py "$CONFIG_FILE"
# python 01_create_deltadtm_vrt.py "$CONFIG_FILE"
# python 01_create_gmw_vrt.py "$CONFIG_FILE"

# # Create tiles to process data
python 02_processing_tiles.py "$CONFIG_FILE"

# Process pond areas
python 03_process_clark.py "$CONFIG_FILE"

# Process accommodation space
python 04_process_gtsm.py "$CONFIG_FILE"
python 04_process_elevation.py "$CONFIG_FILE"
python 04_process_intertidal_space.py "$CONFIG_FILE"
python 04_process_accommodation_space.py "$CONFIG_FILE"

# Process historical and recruitment gmw
python 05_process_gmw.py "$CONFIG_FILE"
python 05_process_historical_gmw.py "$CONFIG_FILE"
python 05_process_recruitment_gmw.py "$CONFIG_FILE"

# Process seed availability
python 06_decrease_gmw_resolution.py "$CONFIG_FILE"

# Activate Rasterio environment
conda deactivate
conda activate mrpm_env

python 06_process_gmw_proximity.py "$CONFIG_FILE"

# Activate QGIS environment
conda deactivate
conda activate qgis_env

python 06_normalization_gmw_proximity.py "$CONFIG_FILE"

# Process coastline and rivers proximities
# Activate Rasterio environment
conda deactivate
conda activate mrpm_env

python 07_process_coastline_rivers_distance.py "$CONFIG_FILE"

# Activate QGIS environment
conda deactivate
conda activate qgis_env

python 07_normalization_coastline.py "$CONFIG_FILE"
python 07_normalization_rivers.py "$CONFIG_FILE"

# Process subsidence
# Activate Rasterio environment
conda deactivate
conda activate mrpm_env

python 08_clip_subsidence.py "$CONFIG_FILE"

# Activate QGIS environment
conda deactivate
conda activate qgis_env

python 08_process_subsidence.py "$CONFIG_FILE"

# Process landcover
# Activate Rasterio environment
conda deactivate
conda activate mrpm_env

python 09_process_landcover.py "$CONFIG_FILE"

# Process permanent water
# Activate QGIS environment
conda deactivate
conda activate qgis_env

python 10_process_permanent_water.py "$CONFIG_FILE"

# Process empty areas and no valid areas
python 11_process_empty_areas.py "$CONFIG_FILE"
python 11_process_no_valid_areas.py "$CONFIG_FILE"

# Process mangrove potential areas
python 12_process_mangrove_potential_areas.py "$CONFIG_FILE"

# Post-processing
# Activate Rasterio environment
conda deactivate
conda activate mrpm_env

python 13_calculate_statistics.py "$CONFIG_FILE"
python 14_create_visualization.py "$CONFIG_FILE"
python 15_process_cog_files.py "$CONFIG_FILE"