import os
import json
import time
from general_utilities import (
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
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]
rivers_geometries = config["rivers_geometries"]
coastline_geometries = config["coastline_geometries"]

# Define the paths
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
tides_dir = os.path.join(data_dir, '8_Tides', country_name)
riv_dir = os.path.join(data_dir, '6_Rivers', country_name)
coa_dir = os.path.join(data_dir, '13_Coastline', country_name)
time_logfile = data_dir

os.makedirs(riv_dir, exist_ok=True)
os.makedirs(coa_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

process_tiles_clips(tiles_dir, coastline_geometries, 500, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 2500, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 5000, "COA", coa_dir)
process_tiles_clips(tiles_dir, coastline_geometries, 7500, "COA", coa_dir)
rasterize_tiles(500, "COA", tiles_dir, tides_dir, coa_dir, coa_dir)
rasterize_tiles(2500, "COA", tiles_dir, tides_dir, coa_dir, coa_dir)
rasterize_tiles(5000, "COA", tiles_dir, tides_dir, coa_dir, coa_dir)
rasterize_tiles(7500, "COA", tiles_dir, tides_dir, coa_dir, coa_dir)

process_tiles_clips(tiles_dir, coastline_geometries, 30000, "COA", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 250, "RIV", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 500, "RIV", riv_dir)
process_tiles_clips(tiles_dir, rivers_geometries, 2500, "RIV", riv_dir)
process_tiles_overlay(tiles_dir, riv_dir, [250, 500, 2500])
rasterize_tiles(250, "OVE", tiles_dir, tides_dir, riv_dir, riv_dir)
rasterize_tiles(500, "OVE", tiles_dir, tides_dir, riv_dir, riv_dir)
rasterize_tiles(2500, "OVE", tiles_dir, tides_dir, riv_dir, riv_dir)

delete_xml_files(tides_dir)
delete_geojson_files(riv_dir)
delete_geojson_files(coa_dir)

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)


