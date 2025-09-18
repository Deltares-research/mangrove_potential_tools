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
deltadtm_files = config["deltadtm_files"]

# Define logfile
time_logfile = data_dir  

# ------ Processing data -----------
start_time = time.time()

# Load warnings for gdal
gdal.UseExceptions()

tif_paths = []

for file_name in os.listdir(deltadtm_files):
    if file_name.lower().endswith(".zip") and file_name.lower() not in {"mask_tiles.zip"}:
        zip_path = os.path.join(deltadtm_files, file_name)
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            for member in z.namelist():
                if member.lower().endswith(".tif"):
                    vsizip_path = f"/vsizip/{zip_path}/{member}"
                    tif_paths.append(vsizip_path)

# Create VRT if we found matching files
if tif_paths:
    output_vrt = os.path.join(deltadtm_files, "deltadtm_globe.vrt")
    vrt_options = gdal.BuildVRTOptions(separate=False)
    gdal.BuildVRT(output_vrt, tif_paths, options=vrt_options)
    print(f"VRT created at: {output_vrt}")
else:
    print("No .tif files found inside the zips.")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)