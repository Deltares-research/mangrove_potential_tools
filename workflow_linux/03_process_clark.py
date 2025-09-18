import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_projwin,
    reproject_raster,
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
clark_vrt = config["clark_vrt"]
multipliers = config["clark_multipliers"]
target_res_deg = config["target_res_deg"]  # Approximate 25 meters in degrees

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
output_dir = os.path.join(data_dir, '3_Clark_classification', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    cla_raster = os.path.join(output_dir, f"CLA_{tile_id}.tif")
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"PON_{tile_id}.tif")

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Clip and reproject raster
    reproject_raster(clark_vrt, cla_raster, target_res_deg, projwin)

    # Normalize raster
    # expression = (
    #     f'(("CLA_{tile_id}@1" = 1) * 0 + '
    #     f'("CLA_{tile_id}@1" = 2) * 0 + '
    #     f'("CLA_{tile_id}@1" = 3) * 100 + ' # Class 3 (ponds) gets higher score
    #     f'("CLA_{tile_id}@1" = 4) * 0 + '
    #     f'("CLA_{tile_id}@1" = 5) * 0) / 100' 
    # )
    expr_terms = [
        f'("CLA_{tile_id}@1" = {k}) * {v}'
        for k, v in multipliers.items()
    ]
    expression = f'({" + ".join(expr_terms)}) / 100'
    input_rasters = [cla_raster]
    raster_calculator(expression, input_rasters, bin_raster)

    # Fill no data and compress raster
    fill_and_compress(bin_raster, fil_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([cla_raster, bin_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)