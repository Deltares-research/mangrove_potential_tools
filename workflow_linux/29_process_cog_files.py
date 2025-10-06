import os
import glob
import rasterio
from rasterio.shutil import copy as rio_copy

def process_folder(input_folder, output_base, subfolder):
    # Remove all .xml files
    for xml_file in glob.glob(os.path.join(input_folder, "*.xml")):
        os.remove(xml_file)
        print(f"Removed: {xml_file}")

    # Prepare output folder
    output_folder = os.path.join(output_base, subfolder)
    os.makedirs(output_folder, exist_ok=True)

    # Convert all .tif files to COG
    for tif_file in glob.glob(os.path.join(input_folder, f"{subfolder}*.tif")):
        output_file = os.path.join(output_folder, os.path.basename(tif_file))

        with rasterio.open(tif_file) as src:
            rio_copy(src, output_file, driver="COG", compress="LZW", overview_resampling="nearest")
        print(f"COG saved: {output_file}")

def process_folder_subsidence(input_folder, output_base, subfolder, year):
    # Remove all .xml files
    for xml_file in glob.glob(os.path.join(input_folder, "*.xml")):
        os.remove(xml_file)
        print(f"Removed: {xml_file}")

    # Prepare output folder
    output_folder = os.path.join(output_base, "SUB", year)
    os.makedirs(output_folder, exist_ok=True)

    # Convert all .tif files to COG
    for tif_file in glob.glob(os.path.join(input_folder, f"{subfolder}*{year}.tif")):
        output_file = os.path.join(output_folder, os.path.basename(tif_file))

        with rasterio.open(tif_file) as src:
            rio_copy(src, output_file, driver="COG", compress="LZW", overview_resampling="nearest")
        print(f"COG saved: {output_file}")

def process_folder_gmw(input_folder, output_base, subfolder, year):
    # Remove all .xml files
    for xml_file in glob.glob(os.path.join(input_folder, "*.xml")):
        os.remove(xml_file)
        print(f"Removed: {xml_file}")

    # Prepare output folder
    output_folder = os.path.join(output_base, "GMW", year)
    os.makedirs(output_folder, exist_ok=True)

    # Convert all .tif files to COG
    for tif_file in glob.glob(os.path.join(input_folder, f"{subfolder}*{year}.tif")):
        output_file = os.path.join(output_folder, os.path.basename(tif_file))

        # If output_file already exists, skip processing
        if os.path.exists(output_file):
            print(f"Skipping (already exists): {output_file}")
            continue

        with rasterio.open(tif_file) as src:
            rio_copy(src, output_file, driver="COG", compress="LZW", overview_resampling="nearest")
        print(f"COG saved: {output_file}")

def process_tiles(input_folder, output_base, subfolder, tiles):
    # Remove all .xml files
    for xml_file in glob.glob(os.path.join(input_folder, "*.xml")):
        os.remove(xml_file)
        print(f"Removed: {xml_file}")

    # Prepare output folder
    output_folder = os.path.join(output_base, subfolder)
    os.makedirs(output_folder, exist_ok=True)

    # Convert all .tif files to COG
    for tif_file in glob.glob(os.path.join(input_folder, f"{subfolder}*.tif")):

        # if tile_file has ["S01E099", "S02E099", "S03E099", "S01E098", "S02E098"] in its name, process the rest if not raise a message saying it was already processed
        if not any(tile in os.path.basename(tif_file) for tile in tiles):
            print(f"Skipping: {tif_file}")
            continue

        output_file = os.path.join(output_folder, os.path.basename(tif_file))

        with rasterio.open(tif_file) as src:
            rio_copy(src, output_file, driver="COG", compress="LZW", overview_resampling="nearest")
        print(f"COG saved: {output_file}")

def remove_xml_files(input_folder):
    # Remove all .xml files
    for xml_file in glob.glob(os.path.join(input_folder, "*.xml")):
        os.remove(xml_file)
        print(f"Removed: {xml_file}")

def rename_files(folder, original_prefix="SEE", new_prefix="PRM"):
    for tif_file in glob.glob(os.path.join(folder, f"{original_prefix}*.tif")):
        base = os.path.basename(tif_file)
        new_base = f"{new_prefix}" + base[len(original_prefix):]  # Replace 'SEE' with 'PRM'
        new_path = os.path.join(folder, new_base)
        os.rename(tif_file, new_path)
        print(f"Renamed: {tif_file} -> {new_path}")

def erase_tif_with_prefix(folder, prefix):
    pattern = f"{prefix}*.tif"
    for tif_file in glob.glob(os.path.join(folder, pattern)):
        os.remove(tif_file)
        print(f"Removed: {tif_file}")

# Run processing for each folder and subfolder
input_folders = [
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/3_Clark_classification/global/",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/10_Accommodation_space/global",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/4_GMW/global/",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/4_GMW/global/",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/4_GMW/global/",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/4_GMW/global/",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/13_Coastline/global",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/6_Rivers/global",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/7_Elevation/global",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/12_Subsidence/global",
    "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/16_Mangrove_potential/global",
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/15_Mask/global"
    # "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/11_Landcover/global"
]

subfolders = [
    # "CLA",
    # "ACC",
    # "HIS",
    # "PRM",
    # "REC",
    # "GMW",
    # "LAN",
    # "PRR",
    # "ELE",
    # "FIL",
    "MPM",
    # "HIS"
]

# output_base = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/subscores"

# for input_folder, subfolder in zip(input_folders, subfolders):
#     process_folder(input_folder, output_base, subfolder)

# output_base = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/underlying_layers"

# for input_folder, subfolder in zip(input_folders, subfolders):
#     process_folder_subsidence(input_folder, output_base, subfolder, "2040")

# output_base = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/underlying_layers"

# for i in [2007,2008,2009,2010,2015,2016,2017,2018,2019]:
#     for input_folder, subfolder in zip(input_folders, subfolders):
#         process_folder_gmw(input_folder, output_base, subfolder, str(i))

output_base = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/mangrove_potential_score"

for input_folder, subfolder in zip(input_folders, subfolders):
    process_tiles(input_folder, output_base, subfolder, [ "S02E099", "S03E099","S02E098"])

# input_folders = [
#     "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/11_Landcover/global",
#     "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/14_Permanent_water/global",
# ]

# for input_folder in input_folders:
#     remove_xml_files(input_folder)

# folder = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/subscores/EXH"
# rename_files(folder, "EXH", "HIS")

# folder = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/12_Subsidence/global/"
# erase_tif_with_prefix(folder, "CLI")
