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
pond_dir = os.path.join(data_dir, '3_Clark_classification', country_name)
gmw_dir = os.path.join(data_dir, '4_GMW', country_name)
rivers_dir = os.path.join(data_dir, "6_Rivers", country_name)
acc_dir = os.path.join(data_dir, '10_Accommodation_space', country_name)
urban_dir = os.path.join(data_dir, '11_Landcover', country_name)
subsidence_dir = os.path.join(data_dir, "12_Subsidence", country_name)
coastline_dir = os.path.join(data_dir, "13_Coastline", country_name)
mask_dir = os.path.join(data_dir, '15_Mask', country_name)
output_dir = os.path.join(data_dir, '16_Mangrove_potential', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    historical_raster = os.path.join(gmw_dir, f"HIS_{tile_id}.tif")
    seed_raster = os.path.join(gmw_dir, f"SEE_{tile_id}.tif")
    pond_raster = os.path.join(pond_dir, f"PON_{tile_id}.tif")
    rivers_raster = os.path.join(rivers_dir, f"PRR_{tile_id}.tif")
    acc_raster = os.path.join(acc_dir, f"ACC_{tile_id}.tif")
    subsidence_raster = os.path.join(subsidence_dir, f"SUB_{tile_id}.tif")
    coastline_raster = os.path.join(coastline_dir, f"PRC_{tile_id}.tif")
    mask_raster = os.path.join(mask_dir, f"NVA_{tile_id}.tif")
    empty_raster = os.path.join(mask_dir, f"EMA_{tile_id}.tif")

    # Define output rasters
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"MPM_{tile_id}.tif")

    # Check if all input rasters exist
    input_rasters  = [mask_raster, pond_raster, acc_raster, historical_raster, seed_raster,
                   rivers_raster, coastline_raster, subsidence_raster]
        
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

    # Add rasters
    expression = (
        f'if("NVA_{tile_id}@1" = 0, '
        f'("PON_{tile_id}@1" + '
        f'"ACC_{tile_id}@1" + '
        f'"HIS_{tile_id}@1" + '
        f'"SEE_{tile_id}@1" + '
        f'max("PRR_{tile_id}@1", "PRC_{tile_id}@1") + '
        f'"SUB_{tile_id}@1") / 6, '
        f'0)'
    )

    raster_calculator(expression, input_rasters, bin_raster)

    # Fill no data and compress raster
    fill_and_compress(bin_raster, fil_raster, com_raster, '')

    print(f"✔ Saved: {com_raster}")

    # Remove intermediate files
    remove_temp_files([bin_raster, fil_raster])

# Save log  
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, f"MPM.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)