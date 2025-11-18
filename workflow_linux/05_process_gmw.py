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
gmw_years = config["gmw_years"]
gmw_vrt = config["gmw_vrt"]
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
output_dir = os.path.join(data_dir, '6_GMW', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for year in gmw_years:
    print(f"\n>>> Processing year: {year}")

    for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
        # Get tile id
        tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
        print(f"\n>>> Processing tile: {tile_id}")

        gmw_raster = os.path.join(gmw_vrt, f"gmw_v3_{year}_gtiff.vrt")
        rep_raster = os.path.join(output_dir, f"REP_{tile_id}_{year}.tif")
        fil_raster = os.path.join(output_dir, f"FIL_{tile_id}_{year}.tif")
        com_raster = os.path.join(output_dir, f"GMW_{tile_id}_{year}.tif")

        if os.path.exists(com_raster):
            print(f"Skipping {tile_id}, {com_raster} already exists.")
            continue

        # Get bounding box of tile
        projwin = get_projwin(tile_path)

        # Clip and reproject raster
        reproject_raster(gmw_raster, rep_raster, None, projwin)

        # Fill no data and compress rasters
        fill_and_compress(rep_raster, fil_raster, com_raster, '')

        # Remove intermediate files
        remove_temp_files([rep_raster, fil_raster])

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)