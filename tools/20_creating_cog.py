import os
from rasterio.shutil import copy as rio_copy
import rasterio

# === CONFIGURATION ===
src_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/southeast_asia_50"
dst_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/southeast_asia_50_cog"
tile_dir = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/1_Tiles/global"

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

        # Make sure the destination folder exists
        os.makedirs(dst_folder_path, exist_ok=True)

        with rasterio.open(src_file_path) as src:
            rio_copy(src, dst_file_path, driver="COG", compress="LZW", overview_resampling="nearest")
        print(f"COG saved: {dst_file_path}")

print("🎉 Done resampling all rasters from 25 m to 50 m.")