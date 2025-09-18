import os
import json
import time
from general_utilities import (
    get_processing_time,

)
from ras_utilities import (
    clip_subsidence,

)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]
subsidence_data_2010 = config["subsidence_data_2010"]
subsidence_data_2010 = config["subsidence_data_2040"]

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
output_dir = os.path.join(data_dir, "12_Subsidence", country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

subsidence_log = clip_subsidence(tiles_dir, subsidence_data_2010, output_dir, "2010")
subsidence_log = clip_subsidence(tiles_dir, subsidence_data_2010, output_dir, "2040")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)

