import os
import json
import time
import pandas as pd
import geopandas as gpd
from general_utilities import (
    get_processing_time,
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]

# Define tiles and output directory and logfile
tiles_geometries = os.path.join(data_dir, '1_Tiles', 'clark_gmw_tiles_country.geojson')
mpm_dir = os.path.join(data_dir, '16_Mangrove_potential', country_name)
mpm_statistics = os.path.join(mpm_dir, 'MPM_statistics.csv')
output_dir =  mpm_dir
time_logfile = data_dir

os.makedirs(output_dir, exist_ok=True)

# ------ Processing data -----------
start_time = time.time()

df = pd.read_csv(mpm_statistics)
df = df.rename(columns ={'tile_id': 'id'})
df['mpm_index'] = df['mean'] * df['count_valid']
print(df.columns)

gdf = gpd.read_file(tiles_geometries)
print(gdf.columns)

# Merge on 'id'
merged_gdf = gdf.merge(df, on='id', how='left')
output_file = os.path.join(output_dir,"tiles_visualization.geojson")

# Save to GeoJSON
merged_gdf.to_file(output_file , driver='GeoJSON')
print(f"Merged GeoJSON saved to {output_file}")

end_time = time.time()
get_processing_time(start_time, end_time, time_logfile)