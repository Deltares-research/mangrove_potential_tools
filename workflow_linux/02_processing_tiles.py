import os
import time
from general_utilities import (
    get_config_file,
    get_clark_tiles_ids,
    get_clark_geometries,
    get_gmw_geometries_by_latitude,
    add_country_info,
    get_tiles_vector,
    get_tiles_vector_with_buffer,    
    get_processing_time
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
tiles_ids = config["tiles_ids"] # Test tiles: ["S01E117", "S02E117"] 
tiles_to_add = config["tiles_to_add"]
tiles_to_skip = config["tiles_to_skip"]
global_tiles = config["global_tiles"]
clark_tiles = config["clark_tiles"]
gmw_tiles = config["gmw_tiles"]
countries_geometries = config["countries_geometries"] 
time_logfile = config["time_logfile"]

# Define output directory and logfile
output_dir = os.path.join(data_dir, "1_Tiles", analysis_id)
os.makedirs(output_dir, exist_ok=True)

# ------ Processing data ----------- 
# Filetering Clark tiles to obtain tiles within gmw latitude range and with information about srtm id and overlapping countries
# strm id is only relevant when gmw tile data is used as the naming is incorrect and don't match other dataset ids 
# buffers of 10km and 100km are created for further analysis using QGIS tools
start_time = time.time()

normalized_ids = get_clark_tiles_ids(clark_tiles, tiles_to_add, tiles_to_skip)
clark_tiles = get_clark_geometries(global_tiles, normalized_ids, tiles_ids, output_dir)
clark_gmw_tiles = get_gmw_geometries_by_latitude(gmw_tiles, clark_tiles)
clark_gmw_tiles_country = add_country_info(clark_gmw_tiles, countries_geometries, output_dir)

get_tiles_vector(output_dir, clark_gmw_tiles_country)
get_tiles_vector_with_buffer(output_dir, clark_gmw_tiles_country, "EPSG:3857", 10000)
get_tiles_vector_with_buffer(output_dir, clark_gmw_tiles_country, "EPSG:3857", 200000)

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)