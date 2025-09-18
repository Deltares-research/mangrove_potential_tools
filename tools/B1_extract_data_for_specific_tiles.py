import os
import shutil
from collections import defaultdict
from osgeo import gdal
import zipfile  # <-- Import para crear ZIP

# Common root path
root = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow"
dest_folder = os.path.join(root, "areas_of_interest")

# Paths and initials relative to root
path_initials = {
    os.path.join(root, "3_Clark_classification", "Tiles_analysis"): ["PON"],
    os.path.join(root, "4_GMW", "Tiles_analysis"): ["HIS", "REC", "SEE"],
    # This will be expanded for year folders
    os.path.join(root, "4_GMW", "Tiles_analysis", "gmw_v3"): ["GMW", "R25"],
    os.path.join(root, "7_Elevation", "Tiles_analysis"): ["ELE"],
    os.path.join(root, "8_Tides", "Tiles_analysis"): ["GTS"],
    os.path.join(root, "10_Accommodation_space", "Tiles_analysis"): ["MSL", "HAT", "ACC"],
    os.path.join(root, "11_Landcover", "Tiles_analysis"): ["LAN"],
}

# Years to check for the GMW dataset
gmw_years = [1996, 2007, 2008, 2009, 2010, 2015, 2016, 2017, 2018, 2019, 2020]

# Valid suffixes after the initials
valid_suffixes = ["S06E110", "N00E117", "N09E104"]

# Load warnings for gdal
gdal.UseExceptions()

# Store results
results = defaultdict(list)

for path, initials_list in path_initials.items():
    # Special case for GMW yearly folders
    if path.endswith(r"4_GMW\Worldwide\gmw_v3") or path.endswith("4_GMW/Worldwide/gmw_v3"):
        paths_to_search = [
            f"{path}_{year}" for year in gmw_years
            if os.path.exists(f"{path}_{year}")
        ]
    else:
        paths_to_search = [path] if os.path.exists(path) else []

    for search_path in paths_to_search:
        files = os.listdir(search_path)
        for initials in initials_list:
            tif_files = {
                os.path.join(search_path, f)
                for f in files
                if (
                    f.lower().endswith(".tif") and
                    f.startswith(initials) and
                    any(f[len(initials):].startswith("_" + suffix) for suffix in valid_suffixes)
                )
            }
            results[f"{initials}_path"].extend(tif_files)

# Remove duplicates and sort
for key in results:
    results[key] = sorted(set(results[key]))

# Print summary by initials
print("\n===== Summary =====")
for key, file_list in results.items():
    print(f"{key}: {len(file_list)} files")

# Create destination folder if not exists
os.makedirs(dest_folder, exist_ok=True)

# Copy all filtered files to destination
for file_list in results.values():
    for file_path in file_list:
        dest_path = os.path.join(dest_folder, os.path.basename(file_path))

        # Avoid overwriting files with the same name
        base, ext = os.path.splitext(dest_path)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = f"{base}_{counter}{ext}"
            counter += 1

        shutil.copy2(file_path, dest_path)

print(f"\n✅ All filtered files copied to: {dest_folder}")

# Crear archivo ZIP con el contenido del folder
zip_path = dest_folder + ".zip"
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
    for foldername, subfolders, filenames in os.walk(dest_folder):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            # Guardar en el ZIP con ruta relativa para no almacenar la ruta completa
            arcname = os.path.relpath(file_path, dest_folder)
            zipf.write(file_path, arcname)

print(f"✅ Folder compressed to ZIP: {zip_path}")
