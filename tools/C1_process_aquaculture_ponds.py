import os
import re
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
from shapely.geometry import mapping

def normalize_id_name(tile_id):
    lon, lat = tile_id.split("_")  # e.g., W117, N32
    lat_dir = lat[0]
    lat_num = int(lat[1:])
    lat_fmt = f"{lat_dir}{lat_num:02d}"
    lon_dir = lon[0]
    lon_num = int(lon[1:])
    lon_fmt = f"{lon_dir}{lon_num:03d}"
    return f"{lat_fmt}{lon_fmt}"

def normalize_id_gdf(lat, lon):
    # Latitude
    lat_dir = 'N' if lat >= 0 else 'S'
    lat_num = abs(int(lat))
    lat_fmt = f"{lat_dir}{lat_num:02d}"
    
    # Longitude
    lon_dir = 'E' if lon >= 0 else 'W'
    lon_num = abs(int(lon))
    lon_fmt = f"{lon_dir}{lon_num:03d}"
    
    return f"{lat_fmt}{lon_fmt}"

def buffer_features(features_gdf, buffer_m):
    features_proj = features_gdf.to_crs(epsg=3857)
    features_proj['geometry'] = features_proj.geometry.buffer(buffer_m)
    features_gdf_buffered = features_proj.to_crs(features_gdf.crs)
    return features_gdf_buffered

def clip_data_to_tiles(features_path, tiles_gdf, output_dir, prefix, buffer_m):
    os.makedirs(output_dir, exist_ok=True)

    # Read features
    features_gdf = gpd.read_file(features_path)

    # Prepare log
    tile_log = []
    
    for idx, tile in tiles_gdf.iterrows():
        tile_id = tile['id']
        print(f">>> Processing tile: {idx} - {tile_id}")
        
        # --- Buffer the tile geometry ---
        tile_geom = gpd.GeoSeries([tile['geometry']], crs=tiles_gdf.crs)
        tile_proj = tile_geom.to_crs(epsg=3857)  # project to meters
        tile_buffered = tile_proj.buffer(buffer_m)  # This buffer is applied over the tiles to extract data in the proximities of the tiles
        tile_buffered = tile_buffered.to_crs(tiles_gdf.crs).iloc[0]  # back to original CRS and single geometry

        # Clip features to buffered tile geometry
        clipped = gpd.clip(features_gdf, tile_buffered)

        if len(clipped) > 0:
            clipped = clipped.dissolve() 
            buffered = buffer_features(clipped, buffer_m)
            buffered = gpd.clip(buffered, tile['geometry'])
            out_file = os.path.join(output_dir, f"{prefix}_{tile_id}.geojson")
            buffered.to_file(out_file, driver="GeoJSON")
            tile_log.append({"tile_id": tile_id, "has_features": True})
        else:
            tile_log.append({"tile_id": tile_id, "has_features": False})
            print(f"Tile {tile_id} has no features, skipping save.")
    
    # Save log
    log_df = pd.DataFrame(tile_log)
    log_csv_path = os.path.join(output_dir, f"tiles_{prefix.lower()}_log.csv")
    log_df.to_csv(log_csv_path, index=False)
    print(f"Processing finished. Log saved to {log_csv_path}")

    return log_df
  
def process_tiles_overlay(input_path, tiles_gdf, output_dir):
    import os
    import geopandas as gpd
    import pandas as pd

    os.makedirs(output_dir, exist_ok=True)
    
    log = []

    for idx, tile in tiles_gdf.iterrows():
        tile_id = tile['id']
        print(f">>> Processing tile: {idx} - {tile_id}")

        # File paths
        c30_file = os.path.join(input_path, f'C30_{tile_id}.geojson')
        riv_file = os.path.join(input_path, f'RIV_{tile_id}.geojson')
        ove_file = os.path.join(output_dir, f'OVE_{tile_id}.geojson')

        # Check existence
        c30_exists = os.path.exists(c30_file)
        riv_exists = os.path.exists(riv_file)
        ove_created = False

        # Check RIV
        if not riv_exists:
            print(f"ERROR: RIV file missing for tile {tile_id}, skipping overlay.")
            log.append({"tile_id": tile_id, "C30_exists": c30_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
            continue

        riv_gdf = gpd.read_file(riv_file)
        if riv_gdf.empty:
            print(f"ERROR: RIV file for tile {tile_id} is empty, skipping overlay.")
            riv_exists = False
            log.append({"tile_id": tile_id, "C30_exists": c30_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
            continue

        # Check C30
        if not c30_exists:
            print(f"ERROR: C30 file missing for tile {tile_id}, skipping overlay.")
            log.append({"tile_id": tile_id, "C30_exists": c30_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
            continue

        c30_gdf = gpd.read_file(c30_file)
        if c30_gdf.empty:
            print(f"ERROR: C30 file for tile {tile_id} is empty, skipping overlay.")
            c30_exists = False
            log.append({"tile_id": tile_id, "C30_exists": c30_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
            continue

        # Overlay
        try:
            ove_gdf = gpd.overlay(c30_gdf, riv_gdf, how="intersection")
            if len(ove_gdf) > 0:
                ove_gdf.to_file(ove_file, driver="GeoJSON")
                ove_created = True
                print(f"Overlay created for tile {tile_id}.")
        except Exception as e:
            print(f"Failed to create overlay for tile {tile_id}: {e}")

        log.append({"tile_id": tile_id, "C30_exists": c30_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})

    # Save log
    log_df = pd.DataFrame(log)
    log_file = os.path.join(output_dir, 'tiles_ove_log.csv')
    log_df.to_csv(log_file, index=False)
    print(f"Processing finished. Log saved to {log_file}")
    
    return log_df

def process_tiles_addition(input_path, tiles_gdf, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    log = []

    for idx, tile in tiles_gdf.iterrows():
        tile_id = tile['id']
        print(f">>> Processing tile: {idx} - {tile_id}")

        # File paths
        c07_file = os.path.join(input_path, f'C07_{tile_id}.geojson')
        ove_file = os.path.join(output_dir, f'OVE_{tile_id}.geojson')
        add_file = os.path.join(output_dir, f'ADD_{tile_id}.geojson')

        # Check existence
        c07_exists = os.path.exists(c07_file)
        ove_exists = os.path.exists(ove_file)
        add_created = False

        # Check C07
        if not c07_exists:
            print(f"ERROR: C07 file missing for tile {tile_id}, skipping addition.")
            log.append({"tile_id": tile_id, "C07_exists": c07_exists, "OVE_exists": ove_exists, "ADD_created": add_created})
            continue

        c07_gdf = gpd.read_file(c07_file)
        if c07_gdf.empty:
            print(f"ERROR: C07 file for tile {tile_id} is empty, skipping addition.")
            c07_exists = False
            log.append({"tile_id": tile_id, "C07_exists": c07_exists, "OVE_exists": ove_exists, "ADD_created": add_created})
            continue

        # Handle OVE missing
        if not ove_exists:
            print(f"WARNING: OVE file missing for tile {tile_id}, saving only C07 as ADD.")
            c07_gdf.to_file(add_file, driver="GeoJSON")
            add_created = True
        else:
            ove_gdf = gpd.read_file(ove_file)
            if ove_gdf.empty:
                print(f"WARNING: OVE file for tile {tile_id} is empty, saving only C07 as ADD.")
                c07_gdf.to_file(add_file, driver="GeoJSON")
                add_created = True
            else:
                # Append polygons
                combined_gdf = pd.concat([c07_gdf, ove_gdf], ignore_index=True)
                combined_gdf = combined_gdf.dissolve() 
                combined_gdf.to_file(add_file, driver="GeoJSON")
                add_created = True
                print(f"Addition created for tile {tile_id}.")

        # Log entry
        log.append({
            "tile_id": tile_id,
            "C07_exists": c07_exists,
            "OVE_exists": ove_exists,
            "ADD_created": add_created
        })

    # Save log CSV
    log_df = pd.DataFrame(log)
    log_path = os.path.join(output_dir, 'tiles_add_log.csv')
    log_df.to_csv(log_path, index=False)
    print(f"Processing finished. Log saved to {log_path}")
    
    return log_df

def process_tiles(tiles_gdf, raster_dir, vector_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    log = []

    for idx, tile in tiles_gdf.iterrows():
        tile_id = tile['id']
        print(f">>> Processing tile: {idx} - {tile_id}")

        # Extract lat/lon from tile_id (assuming format N22E068)
        # lat = tile_id[0:3]
        # lon = tile_id[3:7]
        lat = tile_id[0] + str(int(tile_id[1:3]))   # letter + number without leading zeros
        lon = tile_id[3] + str(int(tile_id[4:7]))   # letter + number without leading zeros
        print(lat, lon)
        print(tile_id)

        # Build file paths
        raster_file = os.path.join(raster_dir, f"aquaculture_2022_{lon}_{lat}.tif")
        vector_file = os.path.join(vector_dir, f"ADD_{tile_id}.geojson")
        output_file = os.path.join(output_dir, f"aquaculture_2022_{lon}_{lat}_masked.tif")

        raster_exists = os.path.exists(raster_file)
        vector_exists = os.path.exists(vector_file)
        masked_created = False

        # Skip if missing vector
        if not vector_exists:
            print(f"WARNING: Vector file missing for tile {tile_id}, skipping.")
            log.append({"tile_id": tile_id, "raster_exists": raster_exists, "vector_exists": vector_exists, "masked_created": masked_created})
            continue

        # Skip if missing raster
        if not raster_exists:
            print(f"WARNING: Raster file missing for tile {tile_id}, skipping.")
            log.append({"tile_id": tile_id, "raster_exists": raster_exists, "vector_exists": vector_exists, "masked_created": masked_created})
            continue

        try:
            # Read vector
            vector_gdf = gpd.read_file(vector_file)
            if vector_gdf.empty:
                print(f"Vector {vector_file} is empty, skipping.")
                log.append({"tile_id": tile_id, "raster_exists": raster_exists, "vector_exists": False, "masked_created": masked_created})
                continue

            # Open raster and mask
            with rasterio.open(raster_file) as src:
                out_image, out_transform = rasterio.mask.mask(src, [mapping(geom) for geom in vector_gdf.geometry], crop=True)
                out_meta = src.meta.copy()

            # Update metadata
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "compress": "lzw"   # ✅ Apply LZW compression
            }) 

            # Save masked raster
            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(out_image)

            masked_created = True
            print(f"Masked raster created for {tile_id}")

        except Exception as e:
            print(f"ERROR: Failed to process {tile_id} → {e}")

        log.append({
            "tile_id": tile_id,
            "raster_exists": raster_exists,
            "vector_exists": vector_exists,
            "masked_created": masked_created
        })

    # Save log CSV
    log_df = pd.DataFrame(log)
    log_file = os.path.join(output_dir, "masking_log.csv")
    log_df.to_csv(log_file, index=False)
    print(f"Processing finished. Log saved to {log_file}")

    return log_df

# Paths
tif_folder = "/p/mangroves-sfincs/01_data/aquaculture/regridded"
vector_path = "/p/mangroves-sfincs/01_data/aquaculture/regridded/global_grid_1deg.shp"

# --- 1. Get list of .tif files ---
tif_files = [f for f in os.listdir(tif_folder) if f.endswith(".tif")]
# --- 2. Extract IDs like W117_N32 ---
raw_ids = [re.search(r'_(W|E)\d+_(N|S)\d+', f).group(0)[1:] for f in tif_files]
# --- 3. Transform to N32W117 form with padding ---
normalized_ids = [normalize_id_name(t) for t in raw_ids]

# --- 4. Read vector data ---
gdf = gpd.read_file(vector_path)
# Apply to dataframe
gdf['id'] = gdf.apply(lambda row: normalize_id_gdf(row['lat'], row['lon']), axis=1)
# Save updated dataframe
# output_path = "/p/mangroves-sfincs\01_data\aquaculture\regridded\global_grid_1deg_id.geojson"
# gdf.to_file(output_path, driver="GeoJSON")

# --- 5. Select geometries where "id" matches ---
selected = gdf[gdf["id"].isin(normalized_ids)]
# --- 5b. Keep only the first N tiles (e.g., first 5) ---
# N = 5
# selected = selected.head(N)
# selected = selected[selected["id"]=="N10E106"]
# selected = selected[selected["id"]=="N16W098"]

# --- 6. Find missing IDs ---
ids_in_gdf = set(gdf["id"])
ids_in_files = set(normalized_ids)
missing_ids = sorted(list(ids_in_files - ids_in_gdf))
print(f"Selected {len(selected)} geometries out of {len(gdf)}")
print(f"Found {len(ids_in_files) - len(missing_ids)} matches, {len(missing_ids)} missing.")

#----------Processing rivers and coastline-------------------------------------------
rivers_path = "/p/11211992-tki-mangrove-restoration/01_data/rivers_lin2019/1000QMEAN_rivers.geojson"
coastline_path = "/p/archivedprojects/11209193-vincarr/01_data/osm_coastlines_segments_180226/coastline_segments.shp"
output_dir = "/p/11211992-tki-mangrove-restoration/01_data/rivers_lin2019/data_in_tiles"

log_riv = clip_data_to_tiles(rivers_path, selected, output_dir, "RIV", 2500)
log_c07 = clip_data_to_tiles(coastline_path, selected, output_dir, "C07", 7500)
log_c30 = clip_data_to_tiles(coastline_path, selected, output_dir, "C30", 30000)

log_ove = process_tiles_overlay(output_dir, selected, output_dir)
log_add = process_tiles_addition(output_dir, selected, output_dir)

raster_dir = "/p/mangroves-sfincs/01_data/aquaculture/regridded"
vector_dir = "/p/11211992-tki-mangrove-restoration/01_data/rivers_lin2019/data_in_tiles"
output_dir = "/p/11211992-tki-mangrove-restoration/01_data/aquaculture/masked_compressed"

log_df = process_tiles(selected, raster_dir, vector_dir, output_dir)

