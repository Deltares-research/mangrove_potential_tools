import os
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
    fill_and_compress
)
from general_utilities import (
    get_config_file,
    get_processing_time,
    remove_temp_files,
    delete_xml_files
)

# Load config from external file
config = get_config_file()

# Define inputs from config
qgis_env_path = config["qgis_env_path"]
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
target_res_deg = config["target_res_deg"]
multipliers_2010 = config["subsidence_multipliers_2010"]
multipliers_2040 = config["subsidence_multipliers_2040"]
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
subsidence_dir = os.path.join(data_dir, "9_Subsidence", analysis_id)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    sub10_raster = os.path.join(subsidence_dir, f"CLI_{tile_id}_2010.tif")
    sub40_raster = os.path.join(subsidence_dir, f"CLI_{tile_id}_2040.tif")

    if not os.path.exists(sub10_raster):
        print(f"Sub10 does not exist {tile_id}, {sub10_raster}.")
        continue  

    if not os.path.exists(sub40_raster):
        print(f"Sub40 does not exist {tile_id}, {sub40_raster}.")
        continue

    fil10_raster = os.path.join(subsidence_dir, f"FIL_{tile_id}_2010.tif")
    fil40_raster = os.path.join(subsidence_dir, f"FIL_{tile_id}_2040.tif")
    nor10_raster = os.path.join(subsidence_dir, f"NOR_{tile_id}_2010.tif")
    nor40_raster = os.path.join(subsidence_dir, f"NOR_{tile_id}_2040.tif")
    cal_raster = os.path.join(subsidence_dir, f"CAL_{tile_id}.tif")
    rep_raster = os.path.join(subsidence_dir, f"REP_{tile_id}.tif")
    nnu_raster = os.path.join(subsidence_dir, f"NNU_{tile_id}.tif")
    com_raster = os.path.join(subsidence_dir, f"SUB_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue  

    fill_extrapolation(sub10_raster, fil10_raster, 20)
    fill_extrapolation(sub40_raster, fil40_raster, 20)

    fil10_name = f"FIL_{tile_id}_2010"
    fil40_name = f"FIL_{tile_id}_2040"

    # Load layers
    fil_layer = get_qgis_layer(fil10_raster, fil10_name)
    fil_layer = get_qgis_layer(fil40_raster, fil40_name)

    # Normalize raster
    expr_terms = [
        f'("{fil10_name}@1" = {k}) * {v}'
        for k, v in multipliers_2010.items()
    ]
    expression = f'({" + ".join(expr_terms)})'
    input_rasters = [fil10_raster]
    raster_calculator(expression, input_rasters, nor10_raster)

    # Normalize raster
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
    fill_and_compress(rep_raster, nnu_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([sub10_raster, sub40_raster, nor10_raster, nor40_raster, cal_raster, rep_raster, nnu_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(subsidence_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)