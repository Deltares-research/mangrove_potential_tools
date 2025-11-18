import os
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    reproject_raster,
    get_projwin,
)
from general_utilities import (
    get_config_file,
)
import processing

# Load config from external file
config = get_config_file()

# Define inputs from config
qgis_env_path = config["qgis_env_path"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# === CONFIGURATION ===
src_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/southeast_asia"
dst_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/southeast_asia_50"
tile_dir = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/1_Tiles/global"

target_res_deg_25m = 0.0002222222222219999985
target_res_deg_50m = 0.0004497
target_res_deg_100m = 0.000898

os.makedirs(dst_root, exist_ok=True)

# === LOOP OVER ALL .TIF FILES ===
for root, dirs, files in os.walk(src_root):
    for file in files:
        if not file.lower().endswith(".tif"):
            continue

        src_file_path = os.path.join(root, file)
        rel_path = os.path.relpath(root, src_root)
        dst_folder_path = os.path.join(dst_root, rel_path)
        dst_file_path = os.path.join(dst_folder_path, file)

        file_name = os.path.basename(src_file_path)
        name_no_ext = os.path.splitext(file_name)[0]

        if  name_no_ext.split("_")[0] == "GMW" or name_no_ext.split("_")[0] == "FIL":
            id_tile = name_no_ext.split("_")[-2]
        else:
            id_tile = name_no_ext.split("_")[-1]

        tile_path = os.path.join(tile_dir, f"TIL_{id_tile}_0.geojson")
        print(tile_path)

        # Check if tile_path exists and stop the process if it does not exist
        if not os.path.exists(tile_path):
            raise FileNotFoundError(f"Tile file not found: {tile_path}")

        # Make sure the destination folder exists
        os.makedirs(dst_folder_path, exist_ok=True)

        # Get bounding box of tile
        projwin = get_projwin(tile_path, rounding=False)

        print(f"Processing: {file}")

        # Define processing parameters
        params = {
            'INPUT': src_file_path,
            'SOURCE_CRS': 'EPSG:4326',  # ✅ Replace if needed
            'TARGET_CRS': 'EPSG:4326',  # ✅ Same CRS if only resampling
            'RESAMPLING': 0,  # 0 = Nearest
            'NODATA': None,
            'TARGET_RESOLUTION': target_res_deg_50m,
            'OPTIONS': '',
            'DATA_TYPE': 0,
            'TARGET_EXTENT': projwin,  # ✅ Must be [xmin, xmax, ymin, ymax]
            'TARGET_EXTENT_CRS': 'EPSG:4326',
            'MULTITHREADING': False,
            'EXTRA': '',
            'OUTPUT': dst_file_path
        }

        # Run algorithm and check result
        result = processing.run("gdal:warpreproject", params)
        print("Output result:", result)


print("🎉 Done resampling all rasters from 25 m to 50 m.")