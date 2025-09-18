import os
import json
import glob
import time
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_qgis_layer,
    raster_calculator,
    compress_raster
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
gmw_years = config["recruitment_gmw_years"]
multipliers = config["recruitment_gmw_multipliers"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
gmw_dir = os.path.join(data_dir, '4_GMW', country_name)
time_logfile = data_dir

# ------ Processing data -----------
start_time = time.time()

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    exp_raster = os.path.join(gmw_dir, f"EXP_{tile_id}.tif")
    cal_raster = os.path.join(gmw_dir, f"CAL_{tile_id}.tif")
    nor_raster = os.path.join(gmw_dir, f"REC_{tile_id}.tif")

    # Load gmw rasters
    raster_info = {}
    for year in gmw_years:
        fil_name = f"GMW_{tile_id}_{year}"
        fil_raster = os.path.join(gmw_dir, f"{fil_name}.tif")
        fil_layer = get_qgis_layer(fil_raster, fil_name)

        raster_info[year] = {
            "fil_name": fil_name,
            "fil_raster": fil_raster,
            "fil_layer": fil_layer
        }

    print("✅ All raster layers loaded successfully.")

    # Compute expression historical mangroves
    expression_parts = []
    layers_to_use = []

    for i, year in enumerate(gmw_years):
        current = raster_info[year]["fil_name"]
        current_layer = raster_info[year]["fil_layer"]
        layers_to_use.append(current_layer)

        # Mask: ensure the pixel is not mangrove in any *later* years
        later_years = gmw_years[i + 1:]
        mask_conditions = [f'("{raster_info[y]["fil_name"]}@1" != 1)' for y in later_years]
        mask_expr = " * ".join(mask_conditions)

        expr = f'("{current}@1" = 1) * {year}'
        if mask_expr:
            expr += f' * {mask_expr}'

        expression_parts.append(expr)

    final_expr = " +\n".join(expression_parts)
    print(f"📐 Raster calculator expression:\n{final_expr}")
    raster_calculator(final_expr, layers_to_use, exp_raster)

    # Normalizing layer
    exp_name = f"EXP_{tile_id}"
    # expression = (
    #     f'(("{exp_name}@1" = 1996) * 0 + '
    #     f'("{exp_name}@1" = 2007) * 36 + '
    #     f'("{exp_name}@1" = 2008) * 40 + '
    #     f'("{exp_name}@1" = 2009) * 45 + '
    #     f'("{exp_name}@1" = 2010) * 49 + '
    #     f'("{exp_name}@1" = 2015) * 70 + '
    #     f'("{exp_name}@1" = 2016) * 75 + '
    #     f'("{exp_name}@1" = 2017) * 79 + '
    #     f'("{exp_name}@1" = 2018) * 83 + '
    #     f'("{exp_name}@1" = 2019) * 87 + '
    #     f'("{exp_name}@1" = 2020) * 100) / 100'
    # )
    expr_terms = [
        f'("{exp_name}@1" = {year}) * {multiplier}'
        for year, multiplier in multipliers.items()
    ]
    expression = f'({" + ".join(expr_terms)}) / 100'
    input_rasters = [exp_raster]
    raster_calculator(expression, input_rasters, cal_raster)

    # Compress raster
    compress_raster(cal_raster, nor_raster)

    # Remove intermediate files
    rasters_to_remove = []
    for year in gmw_years:
        if year != 2020:
            fil_raster = os.path.join(gmw_dir, f"GMW_{tile_id}_{year}.tif")
            rasters_to_remove.append(fil_raster)

    remove_temp_files([exp_raster, cal_raster] + rasters_to_remove)

# Remove .xml files created by qgis when a files is opened
delete_xml_files(gmw_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)