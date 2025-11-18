import os
import glob
import time
import pandas as pd
import rasterio
import numpy as np
from general_utilities import (
    get_config_file,
    get_processing_time,
    remove_temp_files,
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
time_logfile = config["time_logfile"]

# Define tiles and output directory
tiles_dir = os.path.join(data_dir, '1_Tiles', analysis_id)
mpm_dir = os.path.join(data_dir, '14_Mangrove_potential', analysis_id)

# ------ Processing data -----------
start_time = time.time()

log = []

for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
    # Get tile id
    tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
    print(f"\n>>> Calculating statistics tile: {tile_id}")

    # Define output raster
    mpm_raster = os.path.join(mpm_dir, f"MPM_{tile_id}.tif")

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
log_csv_path = os.path.join(mpm_dir, "MPM_statistics.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

end_time = time.time()
get_processing_time(start_time, end_time, time_logfile, analysis_id)