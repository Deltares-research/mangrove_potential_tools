import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_qgis_layer,
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
deltadtm_mangrove_correction = config["deltadtm_mangrove_correction"]
intertidal_slr_correction = config["intertidal_slr_correction"]
target_res_deg = config["target_res_deg"]  # Approximate 25 meters in degrees

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tides_dir = os.path.join(data_dir, '8_Tides', country_name)
elevation_dir = os.path.join(data_dir, '7_Elevation', country_name)
output_dir = os.path.join(data_dir, '10_Accommodation_space', country_name)
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

for tide_path in glob.glob(os.path.join(tides_dir, '*.tif')):
    tide_id = os.path.basename(tide_path).replace("GTS_", "").replace(".tif", "")
    print(f"\n>>> Processing tile: {tide_id}")

    # Define output paths
    output_acc = os.path.join(output_dir, f"IN1_{tide_id}.tif")
    output_hat = os.path.join(output_dir, f"IN2_{tide_id}.tif")
    output_bey = os.path.join(output_dir, f"IN3_{tide_id}.tif")
    output_acc_filled = os.path.join(output_dir, f"FI1_{tide_id}.tif")
    output_hat_filled = os.path.join(output_dir, f"FI2_{tide_id}.tif")
    output_bey_filled = os.path.join(output_dir, f"FI3_{tide_id}.tif")
    output_acc_compressed = os.path.join(output_dir, f"MSL_{tide_id}.tif")
    output_hat_compressed = os.path.join(output_dir, f"HAT_{tide_id}.tif")
    output_bey_compressed = os.path.join(output_dir, f"BEY_{tide_id}.tif")

    # Load rasters as layers with appropriate names
    tide_raster = tide_path
    elevation_raster = os.path.join(elevation_dir, f"ELE_{tide_id}.tif")
    tide_name = f"GTS_{tide_id}"
    elevation_name = f"ELE_{tide_id}"
    elev_layer = get_qgis_layer(elevation_raster, elevation_name)
    tide_layer = get_qgis_layer(tide_raster, tide_name)

    # Derive binary map where elevation >= 0 and elevation <= tide
    acc_expression = f'(({elevation_name}@1 > 0) AND (({elevation_name}@1 * 100 - {str(deltadtm_mangrove_correction)}) <= (GTS_{tide_id}@1 * 100)))'
    acc_rasters = [elev_layer, tide_layer]
    raster_calculator(acc_expression, acc_rasters, output_acc)

    # Derive binary map where elevation > tide
    hat_expression = f'(({elevation_name}@1 * 100 - {str(deltadtm_mangrove_correction)}) > (GTS_{tide_id}@1 * 100))'
    hat_rasters = [elev_layer, tide_layer]
    raster_calculator(hat_expression, hat_rasters, output_hat)

    # Derive binary map where elevation > tide and elevation <= tide + 1
    bey_expression = f'((({elevation_name}@1 * 100 - {str(deltadtm_mangrove_correction)}) > (GTS_{tide_id}@1 * 100)) AND (({elevation_name}@1 * 100 - {str(deltadtm_mangrove_correction)}) <= ((GTS_{tide_id}@1 + {str(intertidal_slr_correction)}/100) * 100)))'
    bey_rasters = [elevation_raster, tide_raster]
    raster_calculator(bey_expression, bey_rasters, output_bey)

    # Fill no data and compress rasters
    fill_and_compress(output_acc, output_acc_filled, output_acc_compressed, f'-tr {target_res_deg} {target_res_deg}')
    fill_and_compress(output_hat, output_hat_filled, output_hat_compressed, f'-tr {target_res_deg} {target_res_deg}')
    fill_and_compress(output_bey, output_bey_filled, output_bey_compressed, f'-tr {target_res_deg} {target_res_deg}')

    print(f"✔ Saved outputs: {output_acc_compressed}, {output_hat_compressed}, {output_bey_compressed}")

    # Remove intermediate files
    remove_temp_files([output_acc, output_hat, output_bey, output_acc_filled, output_hat_filled, output_bey_filled])

# Remove .xml files created by qgis when a files is opened
path_list = [output_dir, elevation_dir, tides_dir]
for path in path_list:
    delete_xml_files(path)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)