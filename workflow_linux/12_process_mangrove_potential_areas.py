import os
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
    get_config_file,
    get_processing_time,
    remove_temp_files,
    delete_xml_files
)

# Load config from external file
config = get_config_file()

# Define inputs from config
qgis_env_path = config["qgis_env_path"]
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
time_logfile = config["time_logfile"]
weights = config["weights"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
pond_dir = os.path.join(data_dir, '2_Clark_classification', analysis_id)
gmw_dir = os.path.join(data_dir, '6_GMW', analysis_id)
rivers_dir = os.path.join(data_dir, "7_Rivers", analysis_id)
acc_dir = os.path.join(data_dir, '5_Accommodation_space', analysis_id)
urban_dir = os.path.join(data_dir, '10_Landcover', analysis_id)
subsidence_dir = os.path.join(data_dir, "9_Subsidence", analysis_id)
coastline_dir = os.path.join(data_dir, "8_Coastline", analysis_id)
empty_dir = os.path.join(data_dir, '12_Empty_areas', analysis_id)
mask_dir = os.path.join(data_dir, '13_Mask', analysis_id)
output_dir = os.path.join(data_dir, '14_Mangrove_potential', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    historical_raster = os.path.join(gmw_dir, f"HIS_{tile_id}.tif")
    seed_raster = os.path.join(gmw_dir, f"PRM_{tile_id}.tif")
    pond_raster = os.path.join(pond_dir, f"PON_{tile_id}.tif")
    rivers_raster = os.path.join(rivers_dir, f"PRR_{tile_id}.tif")
    acc_raster = os.path.join(acc_dir, f"ACC_{tile_id}.tif")
    subsidence_raster = os.path.join(subsidence_dir, f"SUB_{tile_id}.tif")
    coastline_raster = os.path.join(coastline_dir, f"PRC_{tile_id}.tif")
    mask_raster = os.path.join(mask_dir, f"NVA_{tile_id}.tif")
    empty_raster = os.path.join(empty_dir, f"EMA_{tile_id}.tif")

    # Define output rasters
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"MPM_{tile_id}.tif")

    if os.path.exists(com_raster):
        print(f"Skipping {tile_id}, {com_raster} already exists.")
        continue  

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
        f'("PON_{tile_id}@1" * {str(weights["PON"])} + '
        f'"ACC_{tile_id}@1" * {str(weights["ACC"])} + '
        f'"HIS_{tile_id}@1" * {str(weights["HIS"])} + '
        f'"PRM_{tile_id}@1" * {str(weights["PRM"])} + '
        f'max("PRR_{tile_id}@1", "PRC_{tile_id}@1") * {str(weights["PRC_PRR"])} + '
        f'"SUB_{tile_id}@1" * {str(weights["SUB"])}) / 600, '
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

get_processing_time(start_time, end_time, time_logfile, analysis_id)