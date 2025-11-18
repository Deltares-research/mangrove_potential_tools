import os
import time 
import zipfile
from osgeo import gdal
from general_utilities import (
    get_config_file,
    get_processing_time,
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
time_logfile = config["time_logfile"] 
gmw_files = config["gmw_files"]
gmw_years = config["gmw_years"]

# ------ Processing data -----------
start_time = time.time()

# Load warnings for gdal
gdal.UseExceptions()

for year in gmw_years:
    print(f"\n>>> Processing year: {year}")

    tif_paths = []
    zip_path = os.path.join(gmw_files,f'gmw_v3_{year}_gtiff.zip')
    print("Reading zip file:", zip_path)

    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.namelist():
            base_name = os.path.basename(member)
            vsizip_path = f"/vsizip/{zip_path}/{member}"
            tif_paths.append(vsizip_path)

    # Create VRT if we found matching files
    if tif_paths:
        output_vrt = os.path.join(gmw_files, f"gmw_v3_{year}_gtiff.vrt")
        vrt_options = gdal.BuildVRTOptions(separate=False)
        gdal.BuildVRT(output_vrt, tif_paths, options=vrt_options)
        print(f"VRT created at: {output_vrt}")
    else:
        print("No matching .tif files found inside the zips.")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)