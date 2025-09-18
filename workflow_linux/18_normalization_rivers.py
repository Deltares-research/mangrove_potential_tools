import os
import json
import glob
import time
import pandas as pd
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    fill_raster,
    get_qgis_layer,
    raster_calculator,
    get_projwin,
    reproject_raster,
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
target_res_deg = config["target_res_deg"]
multipliers = config["proximity_rivers_multipliers"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
coastline_dir = os.path.join(data_dir, "6_Rivers", country_name)
output_dir = coastline_dir
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    ove_250 = os.path.join(output_dir, f"OVE_{tile_id}_250.tif")
    ove_500 = os.path.join(output_dir, f"OVE_{tile_id}_500.tif")
    ove_2500 = os.path.join(output_dir, f"OVE_{tile_id}_2500.tif")

    ove_250_r = os.path.join(output_dir, f"OVE_{tile_id}_250_r.tif")
    ove_500_r = os.path.join(output_dir, f"OVE_{tile_id}_500_r.tif")
    ove_2500_r = os.path.join(output_dir, f"OVE_{tile_id}_2500_r.tif")

    ove_250_f = os.path.join(output_dir, f"OVE_{tile_id}_250_f.tif")
    ove_500_f = os.path.join(output_dir, f"OVE_{tile_id}_500_f.tif")
    ove_2500_f = os.path.join(output_dir, f"OVE_{tile_id}_2500_f.tif")

    add_raster = os.path.join(output_dir, f"ADR_{tile_id}.tif")
    nor_raster = os.path.join(output_dir, f"NOR_{tile_id}.tif")
    com_raster = os.path.join(output_dir, f"PRR_{tile_id}.tif")

    # Map in order from largest to smallest
    ove_files = [
        (ove_2500, ove_2500_r, ove_2500_f, f"OVE_{tile_id}_2500_f"),
        (ove_500,  ove_500_r,  ove_500_f,  f"OVE_{tile_id}_500_f"),
        (ove_250,  ove_250_r,  ove_250_f,  f"OVE_{tile_id}_250_f")
    ]

    # Check existence
    ove_2500_exists = os.path.exists(ove_2500)
    ove_500_exists = os.path.exists(ove_500)
    ove_250_exists = os.path.exists(ove_250)

    # ---- Determine which case applies ----
    if not os.path.exists(ove_2500):
        print(f"Skipping tile {tile_id}, ove_2500 missing (mandatory).")
        log.append({"tile_id": tile_id, "ove_2500": ove_2500_exists, "ove_500": ove_500_exists, "ove_250": ove_250_exists, "add_raster": False})
    else:
        # Always include ove_2500
        to_process = [ove_files[0]]

        # Check sequentially for smaller files
        if os.path.exists(ove_500):
            to_process.append(ove_files[1])
            if os.path.exists(ove_250):
                to_process.append(ove_files[2])

        print(f"Tile {tile_id}: processing {[f[0] for f in to_process]}")
        log.append({"tile_id": tile_id, "ove_2500": ove_2500_exists, "ove_500": ove_500_exists, "ove_250": ove_250_exists, "add_raster": True})

        # ---- Process selected files ----
        projwin = get_projwin(tile_path)

        input_rasters = []
        expr_terms = []
        rasters_to_remove = []
        for in_file, out_r, out_f, layer_name in to_process:
            print(in_file, out_r, out_f, layer_name, '\n')
            reproject_raster(in_file, out_r, target_res_deg, projwin)
            fill_raster(out_r, out_f)
            layer = get_qgis_layer(out_f, layer_name)
            input_rasters.append(out_f)
            rasters_to_remove.extend([in_file, out_r, out_f])
            expr = f'("{layer_name}@1" = 1) * 1'
            expr_terms.append(expr)

        # Add raster
        expression = f'({" + ".join(expr_terms)})'
        raster_calculator(expression, input_rasters, add_raster)

        # Normalize raster
        add_name = f"ADR_{tile_id}"

        # Normalize raster
        # expression = (
        #     f'(({add_name}@1 = 1) * 50 + '
        #     f'({add_name}@1 = 2) * 67 + '
        #     f'({add_name}@1 = 3) * 100) /100'
        # )
        expr_terms = [
            f'("{add_name}@1" = {k}) * {v}'
            for k, v in multipliers.items()
        ]
        expression = f'({" + ".join(expr_terms)}) / 100'

        input_rasters = [add_raster]
        raster_calculator(expression, input_rasters, nor_raster)

        # Compress raster
        compress_raster(nor_raster, com_raster)

        print(f"✔ Saved: {com_raster}")

        # Remove intermediate files
        remove_temp_files(rasters_to_remove + [add_raster, nor_raster])

# Save log  
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, f"OVE_ADD.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)