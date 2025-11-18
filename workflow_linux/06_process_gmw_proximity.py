import os
import glob
import time
import rasterio 
from general_utilities import (
    get_config_file,
    get_processing_time,
    remove_temp_files,

)
from ras_utilities import (
    apply_dilation,

)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
proximity_distances = config["proximity_distances"]
meters_per_pixel = config["target_res_deg_for_seed_dispersal"] * 111320  # Convert degrees to meters
time_logfile = config["time_logfile"]

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
output_dir = os.path.join(data_dir, '6_GMW', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    fil_raster_path = os.path.join(output_dir, f"REP_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"PRM_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue  

    with rasterio.open(fil_raster_path) as src:
        raster_data = src.read(1)
        profile = src.profile

    for d in proximity_distances:
        dil_raster_path = os.path.join(output_dir, f"DIL_{tile_id}_{d}.tif")
        apply_dilation(raster_data, dil_raster_path, d, meters_per_pixel, profile)

    # Remove intermediate files
    remove_temp_files([fil_raster_path])

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)