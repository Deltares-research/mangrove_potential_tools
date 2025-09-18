#!/bin/bash

# Exit immediately if a command fails
set -e

# Load conda into the shell
source /opt/miniforge3/etc/profile.d/conda.sh

# Activate your QGIS environment
conda activate qgis_env

# Navigate to your project directory
cd /p/11211992-tki-mangrove-restoration/02_scripts_and_processing/mrpm_tools/workflow_linux_testing

# Run the Python script
python 01_processing_tiles.py
python 02_create_clark_vrt.py
python 03_process_clark.py
python 04_process_gtsm.py
python 05_create_deltadtm_vrt.py
python 06_process_elevation.py
python 07_process_intertidal_space.py
python 08_process_accommodation_space.py
python 09_create_gmw_vrt.py
python 10_fill_gmw_nodata.py
python 11_process_historical_gmw.py
python 12_process_recruitment_gmw.py
python 13_decrease_gmw_resolution.py

# Switch to Rasterio environment
conda deactivate
conda activate mrpm_env

# Run the Python script
python 14_process_gmw_proximity.py

# Switch back to QGIS environment
conda deactivate
conda activate qgis_env

# Run the Python scripts
python 15_normalization_gmw_proximity.py

# Switch back to Rasterio environment
conda deactivate
conda activate mrpm_env

# Run the final Python script
python 16_process_coastline_rivers_distance.py

# Switch back to QGIS environment
conda deactivate
conda activate qgis_env

# Run the Python script
python 17_normalization_coastline.py
python 18_normalization_rivers.py

# Switch back to Rasterio environment
conda deactivate
conda activate mrpm_env

# Run the Python script
python 19_clip_subsidence.py

# Switch back to QGIS environment
conda deactivate
conda activate qgis_env

# Run the Python script
python 20_process_subsidence.py

# Switch back to Rasterio environment
conda deactivate
conda activate mrpm_env

# Run the Python script
python 21_process_landcover.py

# Switch back to QGIS environment
conda deactivate
conda activate qgis_env

python 22_process_permanent_water.py
python 23_process_no_valid_areas.py
python 24_process_empty_areas.py
python 25_process_mangrove_potential_areas.py