#!/bin/bash

#SBATCH --job-name=tiles_processing # A short name for your job 
#SBATCH --partition=4vcpu # Which partition/queue to use 
#SBATCH --time=03-05:29:00 # Max runtime (D-HH:MM:SS) 
#SBATCH --nodes=1 # Number of nodes (computers) 
#SBATCH --ntasks=1 # Number of tasks (MPI processes) 
#SBATCH --cpus-per-task=4 # Number of CPU cores per task 
#SBATCH --output=output_mrpm_processing.out

## Load the required software
module load miniforge
conda init

## Execute the python script

## QGIS environment
## srun conda run -n qgis_env python 01_processing_tiles.py
## srun conda run -n qgis_env python 02_create_clark_vrt.py
## srun conda run -n qgis_env python 03_process_clark.py
## srun conda run -n qgis_env python 04_process_gtsm.py
## srun conda run -n qgis_env python 05_create_deltadtm_vrt.py
## srun conda run -n qgis_env python 06_process_elevation.py
## srun conda run -n qgis_env python 07_process_intertidal_space.py
## srun conda run -n qgis_env python 08_process_accommodation_space.py
## srun conda run -n qgis_env python 09_create_gmw_vrt.py
## srun conda run -n qgis_env python 10_fill_gmw_nodata.py
## srun conda run -n qgis_env python 11_process_historical_gmw.py
## srun conda run -n qgis_env python 12_process_recruitment_gmw.py
## srun conda run -n qgis_env python 13_decrease_gmw_resolution.py

## MRPM environment
## srun conda run -n mrpm_env python 14_process_gmw_proximity.py

## QGIS environment
## srun conda run -n qgis_env python 15_normalization_gmw_proximity.py

## MRPM environment
## srun conda run -n mrpm_env python 16_process_coastline_rivers_distance.py

## QGIS environment
## srun conda run -n qgis_env python 17_normalization_coastline.py
## srun conda run -n qgis_env python 18_normalization_rivers.py

## MRPM environment
## srun conda run -n mrpm_env python 19_clip_subsidence.py

## QGIS environment
## srun conda run -n qgis_env python 20_process_subsidence.py

## MRPM environment
## srun conda run -n mrpm_env python 21_process_landcover.py

## QGIS environment
## srun conda run -n qgis_env python 22_process_permanent_water.py
srun conda run -n qgis_env python 23_process_no_valid_areas.py
srun conda run -n qgis_env python 24_process_empty_areas.py
srun conda run -n qgis_env python 25_process_mangrove_potential_areas.py
