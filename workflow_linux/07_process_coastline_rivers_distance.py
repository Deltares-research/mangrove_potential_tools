import os
import time
from general_utilities import (
    get_config_file,
    get_processing_time,
    delete_xml_files,
    delete_geojson_files
)
from ras_utilities import (
    process_tiles_clips,
    process_tiles_overlay,
    rasterize_tiles,
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
rivers_geometries = config["rivers_geometries"]
coastline_geometries = config["coastline_geometries"]
time_logfile = config["time_logfile"]

# Define the paths
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
gmw_dir = os.path.join(data_dir, '6_GMW', analysis_id)
riv_dir = os.path.join(data_dir, '7_Rivers', analysis_id)
coa_dir = os.path.join(data_dir, '8_Coastline', analysis_id)

os.makedirs(riv_dir, exist_ok=True)
os.makedirs(coa_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

process_tiles_clips(tiles_dir, coastline_geometries, 500, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 2500, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 5000, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 7500, "COA", coa_dir)
rasterize_tiles(500, "COA", tiles_dir, gmw_dir, coa_dir, coa_dir)
rasterize_tiles(2500, "COA", tiles_dir, gmw_dir, coa_dir, coa_dir)
rasterize_tiles(5000, "COA", tiles_dir, gmw_dir, coa_dir, coa_dir)
rasterize_tiles(7500, "COA", tiles_dir, gmw_dir, coa_dir, coa_dir)

process_tiles_clips(tiles_dir, coastline_geometries, 30000, "COR", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 250, "RIV", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 500, "RIV", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 2500, "RIV", riv_dir)
process_tiles_overlay(tiles_dir, riv_dir, [250, 500, 2500])
rasterize_tiles(250, "OVE", tiles_dir, gmw_dir, riv_dir, riv_dir)
rasterize_tiles(500, "OVE", tiles_dir, gmw_dir, riv_dir, riv_dir)
rasterize_tiles(2500, "OVE", tiles_dir, gmw_dir, riv_dir, riv_dir)

delete_xml_files(gmw_dir)
delete_geojson_files(riv_dir)
delete_geojson_files(coa_dir)

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)