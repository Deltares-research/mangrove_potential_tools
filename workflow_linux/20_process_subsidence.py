import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_qgis_layer,
    raster_calculator,
    get_projwin,
    reproject_raster,
    fill_extrapolation,
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
multipliers_2010 = config["subsidence_multipliers_2010"]
multipliers_2040 = config["subsidence_multipliers_2040"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
subsidence_dir = os.path.join(data_dir, "12_Subsidence", country_name)
output_dir = subsidence_dir
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    sub10_raster = os.path.join(subsidence_dir, f"CLI_{tile_id}_2010.tif")
    sub40_raster = os.path.join(subsidence_dir, f"CLI_{tile_id}_2040.tif")
    fil10_raster = os.path.join(subsidence_dir, f"FIL_{tile_id}_2010.tif")
    fil40_raster = os.path.join(subsidence_dir, f"FIL_{tile_id}_2040.tif")
    nor10_raster = os.path.join(output_dir, f"NOR_{tile_id}_2010.tif")
    nor40_raster = os.path.join(output_dir, f"NOR_{tile_id}_2040.tif")
    cal_raster = os.path.join(output_dir, f"CAL_{tile_id}.tif")
    rep_raster = os.path.join(output_dir, f"REP_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"SUB_{tile_id}.tif")

    fill_extrapolation(sub10_raster, fil10_raster, 50)
    fill_extrapolation(sub40_raster, fil40_raster, 50)

    fil10_name = f"FIL_{tile_id}_2010"
    fil40_name = f"FIL_{tile_id}_2040"

    # Load layers
    fil_layer = get_qgis_layer(fil10_raster, fil10_name)
    fil_layer = get_qgis_layer(fil40_raster, fil40_name)

    # Normalize raster
    # expression = (
    #     f'(({fil10_name}@1 = 1) * 100 + '
    #     f'({fil10_name}@1 = 2) * 80 + '
    #     f'({fil10_name}@1 = 3) * 60 + '
    #     f'({fil10_name}@1 = 4) * 40 + '
    #     f'({fil10_name}@1 = 5) * 20 + '
    #     f'({fil10_name}@1 = 6) * 0)'
    # )
    expr_terms = [
        f'("{fil10_name}@1" = {k}) * {v}'
        for k, v in multipliers_2010.items()
    ]
    expression = f'({" + ".join(expr_terms)})'
    input_rasters = [fil10_raster]
    raster_calculator(expression, input_rasters, nor10_raster)

    # expression = (
    #     f'(({fil40_name}@1 = 1) * 100 + '
    #     f'({fil40_name}@1 = 2) * 80 + '
    #     f'({fil40_name}@1 = 3) * 60 + '
    #     f'({fil40_name}@1 = 4) * 40 + '
    #     f'({fil40_name}@1 = 5) * 20 + '
    #     f'({fil40_name}@1 = 6) * 0)'
    # )
    expr_terms = [
        f'("{fil40_name}@1" = {k}) * {v}'
        for k, v in multipliers_2010.items()
    ]
    expression = f'({" + ".join(expr_terms)})'
    input_rasters = [fil40_raster]
    raster_calculator(expression, input_rasters, nor40_raster)

    expression = (
        f'(((("NOR_{tile_id}_2010@1")  + '
        f'("NOR_{tile_id}_2040@1")) / 200) + '
        f'max("NOR_{tile_id}_2010@1", "NOR_{tile_id}_2040@1") /100) /2 '
        
    )
    input_rasters = [nor10_raster, nor40_raster]
    raster_calculator(expression, input_rasters, cal_raster)

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Clip and reproject raster
    reproject_raster(cal_raster, rep_raster, target_res_deg, projwin)

    # Compress raster
    compress_raster(rep_raster, com_raster)

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([sub10_raster, sub40_raster, fil10_raster, fil40_raster, nor10_raster, nor40_raster, cal_raster, rep_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)