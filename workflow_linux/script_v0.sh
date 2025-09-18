#!/bin/bash

#SBATCH --job-name=tiles_processing # A short name for your job 
#SBATCH --partition=4vcpu # Which partition/queue to use 
#SBATCH --time=00-05:29:00 # Max runtime (D-HH:MM:SS) 
#SBATCH --nodes=1 # Number of nodes (computers) 
#SBATCH --ntasks=1 # Number of tasks (MPI processes) 
#SBATCH --cpus-per-task=4 # Number of CPU cores per task 
#SBATCH --output=/dev/null      # Prevent default slurm-<jobid>.out
#SBATCH --error=/dev/null       # (optional) suppress stderr default too

module load miniforge
conda init
source activate qgis_env

# Run the Python script
srun python python 01_processing_tiles.py




