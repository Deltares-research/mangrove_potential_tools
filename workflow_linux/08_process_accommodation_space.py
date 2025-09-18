import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_qgis_layer,
    get_projwin,
    raster_calculator,
    compress_raster
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
multipliers = config["accommodation_multipliers"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
acc_dir = os.path.join(data_dir, '10_Accommodation_space', country_name)
time_logfile = data_dir

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Raster paths
    bey_path = os.path.join(acc_dir, f"BEY_{tile_id}.tif")
    hat_path = os.path.join(acc_dir, f"HAT_{tile_id}.tif")
    msl_path = os.path.join(acc_dir, f"MSL_{tile_id}.tif")
    unc_path = os.path.join(acc_dir, f"UNC_{tile_id}.tif")
    cal_path = os.path.join(acc_dir, f"CAL_{tile_id}.tif")
    acc_path = os.path.join(acc_dir, f"ACC_{tile_id}.tif")

    # Layer names
    bey_name = f"BEY_{tile_id}"
    hat_name = f"HAT_{tile_id}"
    msl_name = f"MSL_{tile_id}"
    unc_name = f"UNC_{tile_id}"
    acc_name = f"ACC_{tile_id}"

    # Load layers
    bey_layer = get_qgis_layer(bey_path, bey_name)
    hat_layer = get_qgis_layer(hat_path, hat_name)
    msl_layer = get_qgis_layer(msl_path, msl_name)

    print("✅ All raster layers loaded successfully.")

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Combine layers from MSL - HAT and HAT + 1m
    expression = (
        f'"{msl_name}@1"*2+'
        f'"{bey_name}@1"*1'  
    )
    input_rasters = [msl_layer, bey_path]
    raster_calculator(expression, input_rasters, unc_path)

    # Normalizing layer
    # expression = (
    #     f'(("{unc_name}@1" = 2) * 100 + ' Highest score to intertidal zone
    #     f'("{unc_name}@1" = 1) * 25) / 100'
    # )
    expr_terms = [
        f'("{unc_name}@1" = {k}) * {v}'
        for k, v in multipliers.items()
    ]
    expression = f'({" + ".join(expr_terms)}) / 100'
    input_rasters = [unc_path]
    raster_calculator(expression, input_rasters, cal_path)

    # Compress raster
    compress_raster(cal_path, acc_path)

    # Remove intermediate files
    remove_temp_files([bey_path, hat_path, msl_path, unc_path, cal_path])

# Remove .xml files created by qgis when a files is opened
path_list = [acc_dir]
for path in path_list:
    delete_xml_files(path)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)