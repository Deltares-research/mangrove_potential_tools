import os
import json
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
gmw_years = config["gmw_years"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
output_dir = os.path.join(data_dir, '4_GMW', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for year in gmw_years:
    print(f"\n>>> Processing year: {year}")

    for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
        # Get tile id
        tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
        print(f"\n>>> Processing tile: {tile_id}")

        gmw_vrt = os.path.join(output_dir,f"gmw_v3_{year}_gtiff.vrt")
        rep_raster = os.path.join(output_dir, f"REP_{tile_id}_{year}.tif")
        fil_raster = os.path.join(output_dir, f"FIL_{tile_id}_{year}.tif")
        com_raster = os.path.join(output_dir, f"GMW_{tile_id}_{year}.tif")

        # Get bounding box of tile
        projwin = get_projwin(tile_path)

        # Clip and reproject raster
        reproject_raster(gmw_vrt, rep_raster, None, projwin)

        # Fill no data and compress rasters
        fill_and_compress(rep_raster, fil_raster, com_raster, '')

        # Remove intermediate files
        remove_temp_files([rep_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)