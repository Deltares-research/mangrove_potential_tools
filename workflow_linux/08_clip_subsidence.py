import os
import time
from general_utilities import (
    get_config_file,
    get_processing_time,

)
from ras_utilities import (
    clip_subsidence,

)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
subsidence_data_2010 = config["subsidence_data_2010"]
subsidence_data_2010 = config["subsidence_data_2040"]
time_logfile = config["time_logfile"]

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
output_dir = os.path.join(data_dir, "9_Subsidence", analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

subsidence_log = clip_subsidence(tiles_dir, subsidence_data_2010, output_dir, "2010")
subsidence_log = clip_subsidence(tiles_dir, subsidence_data_2010, output_dir, "2040")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)