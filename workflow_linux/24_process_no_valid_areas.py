import os
import json
import glob
import time
import shutil
import pandas as pd
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    raster_calculator,
    fill_and_compress
)
from general_utilities import (
    get_processing_time,
    remove_temp_files,
    delete_xml_files
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
qgis_env_path = config["qgis_env_path"]
country_name = config["country_name"]
data_dir = config["data_dir"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
gmw_dir = os.path.join(data_dir, '4_GMW', country_name)
riv_dir = os.path.join(data_dir, '6_Rivers', country_name)
urban_dir = os.path.join(data_dir, '11_Landcover', country_name)
coastline_dir = os.path.join(data_dir, "13_Coastline", country_name)
water_dir = os.path.join(data_dir, '14_Permanent_water', country_name)
output_dir = os.path.join(data_dir, '15_Mask', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    gmw_raster = os.path.join(gmw_dir, f"GMW_{tile_id}_2020.tif")
    urb_raster = os.path.join(urban_dir, f"LAN_{tile_id}.tif")
    coa_raster = os.path.join(coastline_dir, f"PRC_{tile_id}.tif")
    riv_raster = os.path.join(riv_dir, f"PRR_{tile_id}.tif")
    wat_raster = os.path.join(water_dir, f"WAT_{tile_id}.tif")
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    empty_raster = os.path.join(output_dir, f"EMA_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"NVA_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue 

    input_rasters = [coa_raster, riv_raster, gmw_raster, urb_raster, wat_raster]

    # Check for missing rasters
    for raster in input_rasters:
        if not os.path.exists(raster):
            # Record missing raster in log
            print(f"⚠️ Raster missing for tile {tile_id}: {raster}")
            log.append({"tile_id": tile_id, "missing_file": raster})

            # Copy EMA template to the missing raster path
            try:
                shutil.copy(empty_raster, raster)
                print(f"✅ Created placeholder raster: {raster}")
            except Exception as e:
                print(f"❌ Could not copy EMA raster for {raster}: {e}")

    missing = [r for r in input_rasters if not os.path.exists(r)]
    if missing:
        print(f"⚠️ Missing raster(s) for tile {tile_id}: {missing}")
        continue

    # Normalize raster
    expression = (
        f'(((("PRC_{tile_id}@1" = 0) - ("PRR_{tile_id}@1" > 0)) > 0) + "GMW_{tile_id}_2020@1" + "LAN_{tile_id}@1" + "WAT_{tile_id}@1") > 0' # There is a mismatch in the years of Clark dataset and GMW so it would be better to not remove mangrove areas from 2020
    )
    
    raster_calculator(expression, input_rasters, bin_raster)

    # Fill no data and compress raster
    fill_and_compress(bin_raster, fil_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([bin_raster, fil_raster])

# Save log  
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, f"NVA.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)