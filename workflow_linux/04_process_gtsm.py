import os
import glob
import time
import pandas as pd
from qgis_utilities import (
    initialize_qgis, 
    initialize_processing, 
    get_projwin,
    get_voronoi_from_gtsm,
    rasterize_vector,
    compress_raster
)
from general_utilities import (
    get_config_file,
    get_processing_time,
    remove_temp_files,
    delete_xml_files
)

# Load config from external file
config = get_config_file()

# Define inputs from config
qgis_env_path = config["qgis_env_path"]
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
gtsm_points = config["gtsm_points"]
target_res_deg = config["target_res_deg"]  # Approximate 25 meters in degrees
time_logfile = config["time_logfile"]

# Initialize qgis
qgs = initialize_qgis(qgis_env_path)
initialize_processing()

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
output_dir = os.path.join(data_dir, '3_Tides', analysis_id)

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []
for tiles_path in glob.glob(os.path.join(tiles_dir, '*200000.geojson')):
    # Get tile id
    tile_id = os.path.basename(tiles_path).replace("TIL_", "").replace("_200000.geojson", "")
    print(f"\n>>> Processing tile: {tile_id}")

    # Define intermediate and output file paths
    til_vector = os.path.join(tiles_dir, f"TIL_{tile_id}_0.geojson")
    gts_vector = os.path.join(output_dir, f"GTS_{tile_id}.geojson")
    vor_vector = os.path.join(output_dir, f"VOR_{tile_id}.geojson")
    cli_vector = os.path.join(output_dir, f"CLI_{tile_id}.geojson")
    ras_raster = os.path.join(output_dir, f"RAS_{tile_id}.tif")
    gts_raster = os.path.join(output_dir, f"GTS_{tile_id}.tif")

    if os.path.exists(gts_raster):
        print(f"Skipping {tile_id}, {gts_raster} already exists.")
        continue
    
    # Try processing processing if not norwing add the id into log.append({"tile_id": tile_id, "missing_file": raster})
    try:
        # Get bounding box of tile
        projwin = get_projwin(til_vector)

        # Calculate voronoi polygons and clip to tile
        get_voronoi_from_gtsm(gtsm_points, tiles_path, til_vector, gts_vector, vor_vector, cli_vector)

        # Rasterize clipped voronoi polygons
        rasterize_vector(cli_vector, 'HAT', target_res_deg, projwin, ras_raster)

        # Apply LZW compression to raster
        compress_raster(ras_raster, gts_raster)

        print(f"✔ Saved outputs: {gts_raster}")

        # Remove intermediate files
        remove_temp_files([gts_vector, vor_vector, cli_vector, ras_raster])

    except Exception as e:
        print(f"✘ Error processing {tile_id}: {e}")
        log.append({"tile_id": tile_id, "error": str(e)})
        remove_temp_files([gts_vector])  
        continue

# Save log  
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, f"GTS.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

# Remove .xml files created by qgis when a files is opened
delete_xml_files(output_dir)

# Close qgis
# qgs.exitQgis()

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile, analysis_id)