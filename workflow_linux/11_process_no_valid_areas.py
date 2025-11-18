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
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
clark_dir = os.path.join(data_dir, '2_Clark_classification', analysis_id)
elevation_dir = os.path.join(data_dir, '4_Elevation', analysis_id)
accommodation_dir = os.path.join(data_dir, '5_Accommodation_space', analysis_id)
subsidence_dir = os.path.join(data_dir, '9_Subsidence', analysis_id)
gmw_dir = os.path.join(data_dir, '6_GMW', analysis_id)
riv_dir = os.path.join(data_dir, '7_Rivers', analysis_id)
urban_dir = os.path.join(data_dir, '10_Landcover', analysis_id)
coastline_dir = os.path.join(data_dir, "8_Coastline", analysis_id)
water_dir = os.path.join(data_dir, '11_Permanent_water', analysis_id)
empty_dir = os.path.join(data_dir, '12_Empty_areas', analysis_id)
output_dir = os.path.join(data_dir, '13_Mask', analysis_id)

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
    his_raster = os.path.join(gmw_dir, f"HIS_{tile_id}.tif")
    prm_raster = os.path.join(gmw_dir, f"PRM_{tile_id}.tif")
    clark_raster = os.path.join(clark_dir, f"PON_{tile_id}.tif")
    elevation_raster = os.path.join(elevation_dir, f"ELE_{tile_id}.tif")
    accommodation_raster = os.path.join(accommodation_dir, f"ACC_{tile_id}.tif")
    subsidence_raster = os.path.join(subsidence_dir, f"SUB_{tile_id}.tif")
    urb_raster = os.path.join(urban_dir, f"LAN_{tile_id}.tif")
    coa_raster = os.path.join(coastline_dir, f"PRC_{tile_id}.tif")
    riv_raster = os.path.join(riv_dir, f"PRR_{tile_id}.tif")
    wat_raster = os.path.join(water_dir, f"WAT_{tile_id}.tif")
    empty_raster = os.path.join(empty_dir, f"EMA_{tile_id}.tif")
    bin_raster = os.path.join(output_dir, f"BIN_{tile_id}.tif")
    fil_raster = os.path.join(output_dir, f"FIL_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"NVA_{tile_id}.tif")

    # if os.path.exists(com_raster):
    #     print(f"Skipping {tile_id}, {com_raster} already exists.")
    #     continue 

    input_rasters = [
        coa_raster, 
        riv_raster, 
        gmw_raster, 
        urb_raster, 
        wat_raster,
        prm_raster,
        clark_raster, 
        elevation_raster,
        accommodation_raster,
        subsidence_raster,
        his_raster,
    ]

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
    # expression = (
    #     f'(((("PRC_{tile_id}@1" = 0) - ("PRR_{tile_id}@1" > 0)) > 0) + "GMW_{tile_id}_2020@1" + "LAN_{tile_id}@1" + "WAT_{tile_id}@1") > 0' # There is a mismatch in the years of Clark dataset and GMW so it would be better to not remove mangrove areas from 2020
    # )

    expression = (
        f'('
        f'((("PRC_{tile_id}@1" = 0) - ("PRR_{tile_id}@1" > 0) - ("PRM_{tile_id}@1" > (60/100))) > 0) + '  # Compare PRC and PRR
        f'"GMW_{tile_id}_2020@1" + '                                    # Add 2020 mangrove layer
        # f'("PRM_{tile_id}@1" < (60/100)) + '                                         # Add land layer
        f'"LAN_{tile_id}@1" + '                                         # Add land layer
        f'"WAT_{tile_id}@1"'                                            # Add water layer
        f') > 0'                                                        # Final condition
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

get_processing_time(start_time, end_time, time_logfile, analysis_id)