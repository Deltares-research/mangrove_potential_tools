import os
import json
import glob
import time
import pandas as pd
import geopandas as gpd
import pystac_client
import planetary_computer
import odc.stac
import rioxarray
from general_utilities import (
    get_processing_time
)

# Load config from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Define inputs from config
country_name = config["country_name"]
data_dir = config["data_dir"]
target_res_deg = config["target_res_deg"]

# Define tiles and output directory and logfile
tiles_dir = os.path.join(data_dir, '1_Tiles', country_name)
output_dir = os.path.join(data_dir, '11_Landcover', country_name)
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
    til_vector = os.path.join(tiles_dir, f"TIL_{tile_id}_0.geojson")
    land_raster = os.path.join(output_dir, f"LAN_{tile_id}.tif")

    if os.path.exists(land_raster):
        print(f"Skipping {tile_id}, {land_raster} already exists.")
        continue  
        
    try:
        # Get bbox til vector
        gdf = gpd.read_file(til_vector)
        minx, miny, maxx, maxy = gdf.total_bounds
        bbox_of_interest_original = [minx, miny, maxx, maxy]

        # Get buffered bbox (reduced to avoid getting data form other regions)
        gdf_proj = gdf.to_crs(epsg=3857)
        gdf_buffered = gdf_proj.buffer(-10000)
        gdf_buffered = gpd.GeoDataFrame(geometry=gdf_buffered, crs=gdf_proj.crs)
        gdf_wgs84 = gdf_buffered.to_crs(epsg=4326)
        minx, miny, maxx, maxy = gdf_wgs84.total_bounds
        bbox_of_interest = [minx, miny, maxx, maxy]
        print("Buffered BBOX:", bbox_of_interest)

        # Look for collection
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        search = catalog.search(
            collections=["esa-worldcover"],
            bbox=bbox_of_interest,
        )

        items = list(search.items())
        items_filtered = [item for item in items if item.properties.get("esa_worldcover:product_version") == "2.0.0"]
        print(items_filtered)

        # Load in memory products
        ds = odc.stac.load(items_filtered, crs="EPSG:4326", resolution=target_res_deg, bbox=bbox_of_interest_original)
        map_data = ds["map"].isel(time=0).load()
        
        # Get only urban areas '50'
        binary_mask = (map_data == 50).astype('uint8')

        # Assign metadata for export
        binary_mask.rio.write_crs(ds.rio.crs, inplace=True)
        binary_mask.rio.write_transform(ds.rio.transform(), inplace=True)

        # Export data as geotiff with LZW compression 
        binary_mask.rio.to_raster(
        land_raster,
        compress='LZW',
        tiled=True,
        predictor=2  # good for continuous data; use 1 for categorical
        )

        print(f"Binary mask saved to {land_raster}")
    
    except:
        print(f"The file {tile_id} could not be created")
        log.append({"tile_id": tile_id, "tile_exist": False})

# Save log  
log_df = pd.DataFrame(log)
log_csv_path = os.path.join(output_dir, f"LAN.csv")
log_df.to_csv(log_csv_path, index=False)
print(f"Processing finished. Log saved to {log_csv_path}")

end_time = time.time()

get_processing_time(start_time, end_time, time_logfile)