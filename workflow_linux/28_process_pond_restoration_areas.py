import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    raster_calculator,
    fill_and_compress
)
from general_utilities import (
    get_processing_time,
    remove_temp_files,
    delete_xml_files
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
qgis_env_path = config["qgis_env_path"]
country_name = config["country_name"]
data_dir = config["data_dir"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
pond_dir = os.path.join(data_dir, '3_Clark_classification', country_name)
mpm_dir = os.path.join(data_dir, '16_Mangrove_potential', country_name)
output_dir = os.path.join(data_dir, '16_Mangrove_potential', country_name, 'ponds')
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    pond_raster = os.path.join(pond_dir, f"PON_{tile_id}.tif")
    mpm_raster = os.path.join(mpm_dir, f"MPM_{tile_id}.tif")
    bin_raster = os.path.join(output_dir, f"BMR_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FMR_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"MRM_{tile_id}.tif")

    # Check if all input rasters exist
    input_rasters  = [pond_raster, mpm_raster]
        
    missing = [r for r in input_rasters if not os.path.exists(r)]
    if missing:
        print(f"⚠️ Missing raster(s) for tile {tile_id}: {missing}")
        continue

    # Add rasters
    expression = (
        f'if("PON_{tile_id}@1" = 1, '
        f'("MPM_{tile_id}@1"),'
        f'0)'
    )

    raster_calculator(expression, input_rasters, bin_raster)

    # Fill no data and compress raster
    fill_and_compress(bin_raster, fil_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([bin_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)