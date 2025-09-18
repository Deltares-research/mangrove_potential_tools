import os
import json
import time 
import zipfile
from osgeo import gdal
from general_utilities import (
    get_processing_time,
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]
gmw_years = config["gmw_years"]

# Define directories and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
output_dir = os.path.join(data_dir, '4_GMW', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

# Load warnings for gdal
gdal.UseExceptions()

for year in gmw_years:
    print(f"\n>>> Processing year: {year}")

    tif_paths = []
    zip_path = os.path.join(data_dir,'4_GMW',f'gmw_v3_{year}_gtiff.zip')
    print("Reading zip file:", zip_path)

    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.namelist():
            base_name = os.path.basename(member)
            vsizip_path = f"/vsizip/{zip_path}/{member}"
            tif_paths.append(vsizip_path)

    # Create VRT if we found matching files
    if tif_paths:
        output_vrt = os.path.join(output_dir, f"gmw_v3_{year}_gtiff.vrt")
        vrt_options = gdal.BuildVRTOptions(separate=False)
        gdal.BuildVRT(output_vrt, tif_paths, options=vrt_options)
        print(f"VRT created at: {output_vrt}")
    else:
        print("No matching .tif files found inside the zips.")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)