import os
import json
import time 
import zipfile
from osgeo import gdal
from general_utilities import (
    get_processing_time
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
data_dir = config["data_dir"]
clark_files = config["clark_files"]
clark_year = config["clark_year"]  

# Define logfile
time_logfile = data_dir  

# ------ Processing data -----------
start_time = time.time()

# Load warnings for gdal
gdal.UseExceptions()

# List to hold virtual paths to .tif files inside zips
tif_paths = []

for file_name in os.listdir(clark_files):
    if file_name.lower().endswith(".zip"):
        zip_path = os.path.join(clark_files, file_name)
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            for member in z.namelist():
                base_name = os.path.basename(member)
                if base_name.endswith(f"_{clark_year}_v1exp.tif") or base_name.endswith(f"_{clark_year}_v2exp.tif"):
                    vsizip_path = f"/vsizip/{zip_path}/{member}"
                    tif_paths.append(vsizip_path)

# Create VRT if we found matching files
if tif_paths:
    output_vrt = os.path.join(clark_files, "clark_data_global.vrt")
    vrt_options = gdal.BuildVRTOptions(separate=False)
    gdal.BuildVRT(output_vrt, tif_paths, options=vrt_options)
    print(f"VRT created at: {output_vrt}")
else:
    print("No matching .tif files found inside the zips.")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)
