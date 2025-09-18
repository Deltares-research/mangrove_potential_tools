import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_projwin,
    reproject_raster,
    fill_raster,
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
clark_files = config["clark_files"]
deltadtm_vrt = config["deltadtm_vrt"]
target_res_deg = config["target_res_deg"]  # Approximate 25 meters in degrees

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
clark_dir = os.path.join(clark_files, country_name)
output_dir = os.path.join(data_dir, '7_Elevation', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # vrt_raster =  os.path.join(output_dir, f"VRT_{tile_id}.tif")
    pon_raster = os.path.join(clark_dir, f"PON_{tile_id}.tif")
    cut_raster = os.path.join(output_dir, f"CUT_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    cor_raster = os.path.join(output_dir, f"COR_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"ELE_{tile_id}.tif")

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Clip and reproject raster
    reproject_raster(deltadtm_vrt, cut_raster, target_res_deg, projwin) 
    
    # Fill raster
    fill_raster(cut_raster, fil_raster)

    # Using raster calculator to assign 0.001 value to NoData pixels in cut_raster where pon_raster has values equal to 1
    elev_expression = f'(({fil_raster}@1) * 1 + ({pon_raster}@1) / 10000)'
    elev_rasters = [fil_raster, pon_raster]
    raster_calculator(elev_expression, elev_rasters, cor_raster)

    # Compress raster
    compress_raster(cor_raster, com_raster)
 
    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([cut_raster, fil_raster, cor_raster])

# Remove .xml files created by qgis when a files is opened
path_list = [clark_dir, output_dir]
for path in path_list:
    delete_xml_files(path)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)