import os
from collections import defaultdict
from osgeo import gdal

# Common root path (Linux mount for P:)
root = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow"

# Paths and initials
path_initials = {
    os.path.join(root, "3_Clark_classification", "Tiles_analysis"): ["PON"],
    os.path.join(root, "4_GMW", "Tiles_analysis", "gmw_v3"): ["GMW", "R25"],  # yearly handling
    os.path.join(root, "4_GMW", "Tiles_analysis"): ["HIS", "REC", "SEE"],
    os.path.join(root, "7_Elevation", "Tiles_analysis"): ["ELE"],
    os.path.join(root, "8_Tides", "Tiles_analysis"): ["GTS"],
    os.path.join(root, "10_Accommodation_space", "Tiles_analysis"): ["MSL", "HAT", "ACC"],
    os.path.join(root, "11_Landcover", "Tiles_analysis"): ["LAN"],
}

gdal.UseExceptions()
results = defaultdict(list)

for path, initials_list in path_initials.items():
    paths_to_search = []

    # Special handling for GMW yearly folders
    if os.path.basename(path) == "gmw_v3":
        parent_dir = os.path.dirname(path)
        if os.path.exists(parent_dir):
            # Find all gmw_v3_* folders
            for name in os.listdir(parent_dir):
                full_path = os.path.join(parent_dir, name)
                if os.path.isdir(full_path) and name.startswith("gmw_v3_"):
                    paths_to_search.append(full_path)
    else:
        if os.path.exists(path):
            paths_to_search.append(path)

    # Process each folder found
    for search_path in paths_to_search:
        folder_name = os.path.basename(search_path)
        year_suffix = None
        if folder_name.startswith("gmw_v3_"):
            # Extract year from folder name
            year_suffix = folder_name.split("_")[-1]

        try:
            files = os.listdir(search_path)
        except FileNotFoundError:
            continue

        for initials in initials_list:
            tif_files = [
                os.path.join(search_path, f)
                for f in files
                if f.lower().endswith(".tif") and f.startswith(initials)
            ]
            if year_suffix:
                key = f"{initials}_{year_suffix}_path"
            else:
                key = f"{initials}_path"
            results[key].extend(tif_files)

# Deduplicate & sort
for key in results:
    results[key] = sorted(set(results[key]))

# Print summary
for key, file_list in results.items():
    print(f"{key}: {len(file_list)} files")

# Create VRT if we found matching files
for key in results:
    if results[key]:
        output_vrt = os.path.join(root, f"{key}.vrt")
        vrt_options = gdal.BuildVRTOptions(separate=False)
        gdal.BuildVRT(output_vrt, results[key], options=vrt_options)
        print(f"VRT created at: {output_vrt}")
    else:
        print("No matching .tif files found inside the zips.")
