import os
import json
import time
from general_utilities import (
    get_clark_tiles_ids,
    get_clark_geometries,
    get_gmw_geometries_by_latitude,
    add_country_info,
    get_tiles_vector,
    get_tiles_vector_with_buffer,    
    get_processing_time
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]
tiles_ids = config["tiles_ids"] # Test tiles: ["S01E117", "S02E117"] 
global_tiles = config["global_tiles"]
clark_tiles = config["clark_tiles"]
clark_countries = config["clark_countries"] 
gmw_tiles = config["gmw_tiles"]
countries_geometries = config["countries_geometries"] 

# Define output directory and logfile
output_dir = os.path.join(data_dir, "1_Tiles", country_name)
os.makedirs(output_dir, exist_ok=True)
time_logfile = data_dir 

# ------ Processing data ----------- 
# Filetering Clark tiles to obtain tiles within gmw latitude range and with information about srtm id and overlapping countries
# strm id is only relevant when gmw tile data is used as the naming is incorrect and don't match other dataset ids 
# buffers of 10km and 100km are created for further analysis using QGIS tools
start_time = time.time()

normalized_ids = get_clark_tiles_ids(clark_tiles)
clark_tiles = get_clark_geometries(global_tiles, normalized_ids, output_dir)

if tiles_ids is not None:
    clark_tiles  = clark_tiles[clark_tiles['id'].isin(tiles_ids)]

clark_gmw_tiles = get_gmw_geometries_by_latitude(gmw_tiles, clark_tiles, output_dir)
clark_gmw_tiles_country = add_country_info(clark_gmw_tiles, countries_geometries, clark_countries, output_dir)

get_tiles_vector(output_dir, clark_gmw_tiles_country)
get_tiles_vector_with_buffer(output_dir, clark_gmw_tiles_country, "EPSG:3857", 10000)
get_tiles_vector_with_buffer(output_dir, clark_gmw_tiles_country, "EPSG:3857", 200000)

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)



