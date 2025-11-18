import os
import shutil

# Source and destination paths
src_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/800"
dst_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/data"

os.makedirs(dst_root, exist_ok=True)


# Walk through all files and folders in source
for root, dirs, files in os.walk(src_root):
    for file in files:
        if file.lower().endswith(".tif"):
            src_file_path = os.path.join(root, file)
            
            # Compute relative path to maintain folder structure
            rel_path = os.path.relpath(root, src_root)
            dst_folder_path = os.path.join(dst_root, rel_path)
            
            # Create destination folder if it doesn't exist
            os.makedirs(dst_folder_path, exist_ok=True)
            
            # Copy file
            dst_file_path = os.path.join(dst_folder_path, file)
            # if file exists, continue
            # if os.path.exists(dst_file_path):
            #     print(f"File {dst_file_path} already exists. Skipping.")
            #     continue

            shutil.copy2(src_file_path, dst_file_path)
            print(f"Copied {src_file_path} to {dst_file_path}")
