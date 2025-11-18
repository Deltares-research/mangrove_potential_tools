import os
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_projwin,
    reproject_raster,
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
gmw_last_year = config["gmw_last_year"]
target_res_deg_for_seed_dispersal = config["target_res_deg_for_seed_dispersal"] # resolution fo approx 100 m
gmw_vrt = config["gmw_vrt"]
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
gmw_vrt_last_year =  os.path.join(gmw_vrt, fr"gmw_v3_{gmw_last_year}_gtiff.vrt")
output_dir = os.path.join(data_dir , '6_GMW', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*10000.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_10000.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    cli_raster = os.path.join(output_dir, f"CLI_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    rep_raster = os.path.join(output_dir, f"REP_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"PRM_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue  

    # Get bounding box of tile
    projwin = get_projwin(tile_path, rounding=False)

    # Clip and reproject raster
    reproject_raster(gmw_vrt_last_year, cli_raster, target_res_deg_for_seed_dispersal, projwin)

    # Fill and compress raster
    fill_and_compress(cli_raster, fil_raster, rep_raster,'')

    print(f"✔ Saved outputs: {rep_raster}")

    # Remove intermediate files
    remove_temp_files([cli_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)