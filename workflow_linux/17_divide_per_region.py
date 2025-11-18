import os
import shutil
import re

# Source and destination paths
src_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/data"
dst_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/data_by_region"

# Region definitions (name -> (min_lon, max_lon))
# Note: lon is negative for W, positive for E
regions = {
    "W180_W017": (-180, -17),
    "W018_E091": (-18, 91),
    "E092_E179": (92, 179)
}

# Create top-level region folders (and an UNKNOWN folder)
for region in list(regions.keys()) + ["UNKNOWN"]:
    os.makedirs(os.path.join(dst_root, region), exist_ok=True)

# Regex to find longitude token in filename, e.g. W123, E045, w12, e7
lon_pattern = re.compile(r'([WE])\s*0*([0-9]{1,3})', re.IGNORECASE)

def extract_longitude_from_name(filename):
    """
    Returns an integer longitude (negative for W, positive for E) or None if not found.
    """
    m = lon_pattern.search(filename)
    if not m:
        return None
    hemi = m.group(1).upper()
    val = int(m.group(2))
    return -val if hemi == "W" else val

# Walk through all files and folders in source
for root, dirs, files in os.walk(src_root):
    for file in files:
        if not file.lower().endswith(".tif"):
            continue

        src_file_path = os.path.join(root, file)

        # Compute relative path from source root (preserves folder structure)
        rel_dir = os.path.relpath(root, src_root)  # '.' if root == src_root
        if rel_dir == ".":
            rel_dir = ""  # so join works nicely

        lon = extract_longitude_from_name(file)
        region_folder = None

        if lon is None:
            region_folder = "UNKNOWN"
            print(f"ℹ️  No lon found in '{file}'. Will copy to UNKNOWN.")
        else:
            # Determine region by checking in the defined order (first match wins)
            for region_name, (min_lon, max_lon) in regions.items():
                if min_lon <= lon <= max_lon:
                    region_folder = region_name
                    break

            if region_folder is None:
                # If longitude doesn't fall in any region, send to UNKNOWN
                region_folder = "UNKNOWN"
                print(f"⚠️  Lon {lon} for '{file}' not in any region ranges. Sent to UNKNOWN.")

        # Destination folder: region + relative path (preserves structure)
        dst_folder_path = os.path.join(dst_root, region_folder, rel_dir)
        os.makedirs(dst_folder_path, exist_ok=True)

        dst_file_path = os.path.join(dst_folder_path, file)

        # Skip if file already exists (you can change behavior if you prefer overwrite)
        if os.path.exists(dst_file_path):
            print(f"⏭️  Exists: {dst_file_path} (skipping)")
            continue

        shutil.copy2(src_file_path, dst_file_path)
        print(f"✅ Copied: {src_file_path} -> {dst_file_path}")
