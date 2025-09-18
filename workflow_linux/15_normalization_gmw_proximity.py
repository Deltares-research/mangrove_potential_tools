import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_projwin,
    get_qgis_layer,
    raster_calculator,
    reproject_raster,
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
target_res_deg = config["target_res_deg"]
multipliers = config["proximity_gmw_multipliers"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
gmw_dir = os.path.join(data_dir, '4_GMW', country_name)
time_logfile = data_dir

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")
    
    # Raster paths
    dil_500_raster = os.path.join(gmw_dir, f"DIL_{tile_id}_500.tif")
    dil_2500_raster = os.path.join(gmw_dir, f"DIL_{tile_id}_2500.tif")
    dil_10000_raster = os.path.join(gmw_dir, f"DIL_{tile_id}_10000.tif")
    add_raster = os.path.join(gmw_dir, f"ADD_{tile_id}.tif")
    cal_raster = os.path.join(gmw_dir, f"CAL_{tile_id}.tif")
    cli_raster = os.path.join(gmw_dir, f"CLI_{tile_id}.tif")
    com_raster = os.path.join(gmw_dir, f"SEE_{tile_id}.tif")

    # Layer names
    dil_500_name = f"DIL_{tile_id}_500"
    dil_2500_name = f"DIL_{tile_id}_2500"
    dil_10000_name = f"DIL_{tile_id}_10000"
    add_name = f"ADD_{tile_id}"

    # Load layers
    dil_500_layer = get_qgis_layer(dil_500_raster, dil_500_name)
    dil_2500_layer = get_qgis_layer(dil_2500_raster, dil_2500_name)
    dil_10000_layer = get_qgis_layer(dil_10000_raster, dil_10000_name)

    print("✅ All raster layers loaded successfully.")

    # Adding layers
    expression = (
        f'"{dil_500_name}@1" + '
        f'"{dil_2500_name}@1" + '
        f'"{dil_10000_name}@1"'
    )
    input_rasters =  [dil_500_layer, dil_2500_layer, dil_10000_layer]
    raster_calculator(expression, input_rasters, add_raster)

    # Normalizing layer
    # expression = (
    #     f'(("{add_name}@1" = 1) * 50 + '
    #     f'("{add_name}@1" = 2) * 89 + '
    #     f'("{add_name}@1" = 3) * 100) / 100'
    # )
    expr_terms = [
        f'("{add_name}@1" = {k}) * {v}'
        for k, v in multipliers.items()
    ]
    expression = f'({" + ".join(expr_terms)}) / 100'

    input_rasters = [add_raster]
    raster_calculator(expression, input_rasters, cal_raster)

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Reproject raster
    reproject_raster(cal_raster, cli_raster, target_res_deg, projwin)

    # Compress raster
    compress_raster(cli_raster, com_raster)

    # Remove intermediate files
    remove_temp_files([dil_500_raster, dil_2500_raster, dil_10000_raster, add_raster, cal_raster, cli_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(gmw_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)