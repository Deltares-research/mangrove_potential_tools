import os
import time
from ras_utilities import (
    process_cogs,
)
from general_utilities import (
    get_config_file,
    get_processing_time,
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
geoserver_folder = config["geoserver_folder"]
time_logfile = config["time_logfile"]

# Define tiles and output directory
subscores_dir = os.path.join(geoserver_folder, analysis_id, 'subscores')
underlying_layers_dir = os.path.join(geoserver_folder, analysis_id, 'underlying_layers')
mangrove_potential_score_dir = os.path.join(geoserver_folder, analysis_id, 'mangrove_potential_score')

# ------ Processing data -----------
start_time = time.time()

# Define workflow steps (just the folder names)
workflow_steps = [
    "6_GMW",
    "9_Subsidence",
    "10_Landcover",
    "11_Permanent_water",
]

# Define subfolder codes corresponding to workflow steps
subfolders = [
    "GMW",
    "FIL",
    "LAN",
    "WAT",
]

process_cogs(data_dir, analysis_id, workflow_steps, subfolders, underlying_layers_dir)

# Define workflow steps (just the folder names)
workflow_steps = [
    "2_Clark_classification",
    "5_Accommodation_space",
    "6_GMW",
    "6_GMW",
    "7_Rivers",
    "8_Coastline",
    "9_Subsidence",
]

# Define subfolder codes corresponding to workflow steps
subfolders = [
    "PON",
    "ACC",
    "HIS",
    "PRM",
    "PRR",
    "PRC",
    "SUB",
]

# process_cogs(data_dir, analysis_id, workflow_steps, subfolders, subscores_dir)

# Define workflow steps (just the folder names)
workflow_steps = [
    "13_Mask",
    "14_Mangrove_potential",
]

# Define subfolder codes corresponding to workflow steps
subfolders = [
    "NVA",
    "MPM",
]

# process_cogs(data_dir, analysis_id, workflow_steps, subfolders, mangrove_potential_score_dir)

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)