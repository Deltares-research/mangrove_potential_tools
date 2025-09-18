#!/bin/bash

#SBATCH --job-name=tiles_processing # A short name for your job 
#SBATCH --partition=4vcpu # Which partition/queue to use 
#SBATCH --time=00-05:29:00 # Max runtime (D-HH:MM:SS) 
#SBATCH --nodes=1 # Number of nodes (computers) 
#SBATCH --ntasks=1 # Number of tasks (MPI processes) 
#SBATCH --cpus-per-task=4 # Number of CPU cores per task 
#SBATCH --output=_mrpm_processing.out

## Load the required software
module load miniforge
conda init

## Execute the python script
## srun conda run -n qgis_env python 01_processing_tiles.py
srun conda run -n mrpm_env 16_process_coastline_rivers_distance.py
srun conda run -n qgis_env python 17_normalization_coastline.py
srun conda run -n qgis_env python 18_normalization_rivers.py