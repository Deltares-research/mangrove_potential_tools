import os
import time
import pandas as pd
import geopandas as gpd
from general_utilities import (
    get_config_file,
    get_processing_time,
)

# Load config from external file
config = get_config_file()

# Define inputs from config
analysis_id = config["analysis_id"]
data_dir = config["data_dir"]
time_logfile = config["time_logfile"]

# Define tiles and output directory
tiles_geometries = os.path.join(data_dir, '1_Tiles', analysis_id, "overall", 'clark_gmw_tiles_country.geojson')
mpm_dir = os.path.join(data_dir, '14_Mangrove_potential', analysis_id)
mpm_statistics = os.path.join(mpm_dir, 'MPM_statistics.csv')

# ------ Processing data -----------
start_time = time.time()

df = pd.read_csv(mpm_statistics)
df = df.rename(columns ={'tile_id': 'id'})
# df['mpm_index'] = df['mean'] * df['count_valid']
print(df.columns)

gdf = gpd.read_file(tiles_geometries)
print(gdf.columns)

# Merge on 'id'
merged_gdf = gdf.merge(df, on='id', how='left')
output_file = os.path.join(mpm_dir,"tiles_visualization.geojson")

# Postprocessing data
# Remove columns missing_file.
merged_gdf.drop(columns=['lon', 'lat', 'xmin', 'xmax', 'ymin', 'ymax', 'missing_file', 'num_countries'], inplace=True)

# Add area of geometry in m2 transforming to EPSG:3857
merged_gdf['area_tile'] = merged_gdf.to_crs(epsg=3857).geometry.area

# Devide count_valid by area_tile to get density. Multiply count_valid by 25 x 25 m pixel size to get area in m2
merged_gdf['coverage'] = merged_gdf['count_valid'] * 25 * 25 / merged_gdf['area_tile']

# MRPM index
merged_gdf['i_median'] = merged_gdf['median'] * merged_gdf["coverage"]
merged_gdf['i_mean'] = merged_gdf['mean'] * merged_gdf["coverage"]

# Move column 'std'to the position after 'median'
std_col = merged_gdf.pop('std')
merged_gdf.insert(merged_gdf.columns.get_loc('median') + 1, 'std', std_col)

# Move column countries to the end before geometry
countries_col = merged_gdf.pop('countries')
merged_gdf['countries'] = countries_col

# Rename count_valid column to count
merged_gdf = merged_gdf.rename(columns={'count_valid': 'count'})

# Take it back to EPSG:4326
merged_gdf = merged_gdf.to_crs(epsg=4326)

# Save to GeoJSON
merged_gdf.to_file(output_file , driver='GeoJSON')
print(f"Merged GeoJSON saved to {output_file}")

end_time = time.time()
get_processing_time(start_time, end_time, time_logfile, analysis_id)