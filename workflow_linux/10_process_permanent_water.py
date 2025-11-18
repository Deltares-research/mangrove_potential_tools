import os
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
permanent_water_vrt = config["permanent_water_vrt"]
permanent_water_treshold = config["permanent_water_threshold"]
target_res_deg = config["target_res_deg"]  # Approximate 25 meters in degrees
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
pond_dir = os.path.join(data_dir, '2_Clark_classification', analysis_id)
output_dir = os.path.join(data_dir, '11_Permanent_water', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    pon_raster = os.path.join(pond_dir, f"PON_{tile_id}.tif")
    cla_raster = os.path.join(output_dir, f"CLA_{tile_id}.tif")
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"WAT_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue

    # Get bounding box of tile
    projwin = get_projwin(tile_path)

    # Clip and reproject raster
    reproject_raster(permanent_water_vrt, cla_raster, target_res_deg, projwin)

    # Normalize raster
    expression = (
        f'(("CLA_{tile_id}@1" > {permanent_water_treshold}) - "PON_{tile_id}@1") > 0 '
    )
    input_rasters = [cla_raster, pon_raster]
    raster_calculator(expression, input_rasters, bin_raster)

    # Fill no data and compress raster
    fill_and_compress(bin_raster, fil_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([cla_raster, bin_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
path_list = [output_dir, pond_dir]
for path in path_list:
    delete_xml_files(path)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)