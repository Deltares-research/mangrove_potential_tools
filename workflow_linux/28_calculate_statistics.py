import os
import json
import glob
import time
import pandas as pd
import rasterio
import numpy as np
from general_utilities import (
    get_processing_time,
    remove_temp_files,
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
mpm_dir = os.path.join(data_dir, '16_Mangrove_potential', country_name, 'ponds')
output_dir=  mpm_dir 
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

log = []

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Calculating statistics tile: {tile_id}")

    # Define output raster
    mpm_raster = os.path.join(output_dir, f"MRM_{tile_id}.tif")

    if not os.path.exists(mpm_raster):
        log.append({
            "tile_id": tile_id,
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
            "median": None,
            "p5": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
            "p33": None,
            "p67": None,
            "count_valid": None,
            "missing_file": mpm_raster
        })
        continue

    # --- Calculate statistics ---
    with rasterio.open(mpm_raster) as src:
        band = src.read(1, masked=True)  # read first band
        band = np.ma.masked_where(band == 0, band)  # mask nodata (0)

        if band.count() > 0:
            data = band.compressed()  # drop masked values
            stats = {
                "tile_id": tile_id,
                "min": float(data.min()),
                "max": float(data.max()),
                "mean": float(data.mean()),
                "std": float(data.std()),
                "median": float(np.median(data)),
                "p5": float(np.percentile(data, 5)),
                "p25": float(np.percentile(data, 25)),
                "p50": float(np.percentile(data, 50)),
                "p75": float(np.percentile(data, 75)),
                "p95": float(np.percentile(data, 95)),
                "p33": float(np.percentile(data, 33.33)),  # tercile 1 threshold
                "p67": float(np.percentile(data, 66.67)),  # tercile 2 threshold
                "count_valid": int(data.size),
                "missing_file": None
            }
        else:
            stats = {
                "tile_id": tile_id,
                "min": None,
                "max": None,
                "mean": None,
                "std": None,
                "median": None,
                "p5": None,
                "p25": None,
                "p50": None,
                "p75": None,
                "p95": None,
                "p33": None,
                "p67": None,
                "count_valid": 0,
                "missing_file": None
            }

    log.append(stats)

    # Remove intermediate files
    remove_temp_files([])

# Save log with statistics
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, "MRM_statistics.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

end_time = time.time()
get_processing_time(start_time, end_time, time_logfile)