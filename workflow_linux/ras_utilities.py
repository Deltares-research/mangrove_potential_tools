import os
import glob
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
from shapely.geometry import mapping
import rasterio
import numpy as np
from scipy.ndimage import binary_dilation

def apply_dilation(raster_data, output_path, distance_m, meters_per_pixel, profile):
    radius_px = distance_m / meters_per_pixel
    y, x = np.ogrid[-radius_px:radius_px+1, -radius_px:radius_px+1]
    structure = (x**2 + y**2) <= radius_px**2
    dilated_mask = binary_dilation(raster_data == 1, structure=structure)
    dilated_data = dilated_mask.astype(np.uint8)

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(dilated_data, 1)
    print(f"✔ Dilation ({distance_m}m) saved to: {output_path}")

def buffer_features(features_gdf, buffer_m):
    features_proj = features_gdf.to_crs(epsg=3857)
    features_proj['geometry'] = features_proj.geometry.buffer(buffer_m)
    features_gdf_buffered = features_proj.to_crs(features_gdf.crs)
    return features_gdf_buffered

def clip_river_to_single_tile(features_path, tile_path, output_dir, prefix, buffer_m, tile_id, tile_log):

    # Read features
    features_gdf = gpd.read_file(features_path, columns=["QMEAN", "width_m", "geometry"])
    tile_gdf = gpd.read_file(tile_path)

    # Clip features to buffered tile geometry
    tile_geom = gpd.GeoSeries([tile_gdf.geometry.iloc[0]], crs=tile_gdf.crs)
    tile_proj = tile_geom.to_crs(epsg=3857)  # project to meters
    tile_buffered = tile_proj.buffer(buffer_m)  # This buffer is applied over the tiles to extract data in the proximities of the tiles
    tile_buffered = tile_buffered.to_crs(tile_gdf.crs).iloc[0]  # back to original CRS and single geometry
    clipped = gpd.clip(features_gdf, tile_buffered)

    if len(clipped) > 0:
        if clipped.crs.is_geographic:
            clipped = clipped.to_crs(epsg=3857)
        clipped["geometry"] = clipped.apply(
            lambda row: row.geometry.buffer(row["width_m"]), axis=1
        )
        clipped= clipped.to_crs(tile_gdf.crs)
        clipped = clipped.dissolve() 
        buffered = buffer_features(clipped, buffer_m)
        buffered = gpd.clip(buffered, tile_gdf['geometry'])
        out_file = os.path.join(output_dir, f"{prefix}_{tile_id}_{str(buffer_m)}.geojson")
        buffered.to_file(out_file, driver="GeoJSON")
        tile_log.append({"tile_id": tile_id, "has_features": True})
    else:
        print(f"Tile {tile_id} has no features, skipping save.")
        tile_log.append({"tile_id": tile_id, "has_features": False})

    return tile_log

def clip_coastline_to_single_tile(features_path, tile_path, output_dir, prefix, buffer_m, tile_id, tile_log):

    # Read features
    features_gdf = gpd.read_file(features_path)
    tile_gdf = gpd.read_file(tile_path)

    # Clip features to buffered tile geometry
    tile_geom = gpd.GeoSeries([tile_gdf.geometry.iloc[0]], crs=tile_gdf.crs)
    tile_proj = tile_geom.to_crs(epsg=3857)  # project to meters
    tile_buffered = tile_proj.buffer(buffer_m)  # This buffer is applied over the tiles to extract data in the proximities of the tiles
    tile_buffered = tile_buffered.to_crs(tile_gdf.crs).iloc[0]  # back to original CRS and single geometry
    clipped = gpd.clip(features_gdf, tile_buffered)

    if len(clipped) > 0:
        clipped = clipped.dissolve() 
        buffered = buffer_features(clipped, buffer_m)
        buffered = gpd.clip(buffered, tile_gdf['geometry'])
        out_file = os.path.join(output_dir, f"{prefix}_{tile_id}_{str(buffer_m)}.geojson")
        buffered.to_file(out_file, driver="GeoJSON")
        tile_log.append({"tile_id": tile_id, "has_features": True})
    else:
        print(f"Tile {tile_id} has no features, skipping save.")
        tile_log.append({"tile_id": tile_id, "has_features": False})

    return tile_log
    
def rasterize_tiles(buffer, prefix, tiles_dir, raster_dir, vector_dir, output_dir):

    log = []
    for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
        tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
        print(f"\n>>> Processing tile: {tile_id}")

        # Build file paths
        raster_file = os.path.join(raster_dir, f"GTS_{tile_id}.tif")
        vector_file = os.path.join(vector_dir, f"{prefix}_{tile_id}_{str(buffer)}.geojson")
        output_file = os.path.join(output_dir, f"{prefix}_{tile_id}_{str(buffer)}.tif")

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
                out_image = (out_image > 0).astype(out_image.dtype)
                out_meta = src.meta.copy()

            # Update metadata
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "compress": "lzw",   # ✅ Apply LZW compression
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

    # # Save log CSV
    # log_df = pd.DataFrame(log)
    # log_file = os.path.join(output_dir, f"RAS_{prefix}_{str(buffer)}.csv")
    # log_df.to_csv(log_file, index=False)
    # print(f"Processing finished. Log saved to {log_file}")

def process_tiles_clips(tiles_dir, features, buffer, prefix, output_dir):
    log = []
    for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
        tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
        print(f"\n>>> Processing tile: {tile_id}")
        if prefix =="RIV":
            log = clip_river_to_single_tile(features, tile_path, output_dir, prefix, buffer, tile_id, log)
        elif prefix =="COA":
            log = clip_coastline_to_single_tile(features, tile_path, output_dir, prefix, buffer, tile_id, log)
        else:
            print(f"Unknown prefix {prefix}, skipping tile {tile_id}")
            continue
    # Save log  
    # log_df = pd.DataFrame(log)
    # log_csv_path = os.path.join(output_dir, f"{prefix}_{str(buffer)}.csv")
    # log_df.to_csv(log_csv_path, index=False)
    # print(f"Processing finished. Log saved to {log_csv_path}")

def process_tiles_overlay(tiles_dir, input_path, buffers):
    for buffer in buffers:
        log = []
        for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
            tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
            print(f"\n>>> Processing tile: {tile_id}")

            # File paths
            c300_file = os.path.join(input_path, f'COA_{tile_id}_30000.geojson')
            riv_file = os.path.join(input_path, f'RIV_{tile_id}_{buffer}.geojson')
            ove_file = os.path.join(input_path, f'OVE_{tile_id}_{buffer}.geojson')

            # Check existence
            C300_exists = os.path.exists(c300_file)
            riv_exists = os.path.exists(riv_file)
            ove_created = False

            # Check RIV
            if not riv_exists:
                print(f"ERROR: RIV file missing for tile {tile_id}, skipping overlay.")
                log.append({"tile_id": tile_id, "C300_exists": C300_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
                continue

            riv_gdf = gpd.read_file(riv_file)
            if riv_gdf.empty:
                print(f"ERROR: RIV file for tile {tile_id} is empty, skipping overlay.")
                riv_exists = False
                log.append({"tile_id": tile_id, "C300_exists": C300_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
                continue

            # Check C30
            if not C300_exists:
                print(f"ERROR: C30 file missing for tile {tile_id}, skipping overlay.")
                log.append({"tile_id": tile_id, "C300_exists": C300_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
                continue

            c30_gdf = gpd.read_file(c300_file)
            if c30_gdf.empty:
                print(f"ERROR: C30 file for tile {tile_id} is empty, skipping overlay.")
                C300_exists = False
                log.append({"tile_id": tile_id, "C300_exists": C300_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})
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

            log.append({"tile_id": tile_id, "C300_exists": C300_exists, "RIV_exists": riv_exists, "OVE_created": ove_created})

        # # Save log
        # log_df = pd.DataFrame(log)
        # log_file = os.path.join(input_path, f'OVE_{str(buffer)}.csv')
        # log_df.to_csv(log_file, index=False)
        # print(f"Processing finished. Log saved to {log_file}")

def clip_subsidence(tiles_dir, raster_file, output_dir, id):

    log = []
    for tile_path in glob.glob(os.path.join(tiles_dir, '*_0.geojson')):
        tile_id = os.path.basename(tile_path).replace("TIL_", "").replace("_0.geojson", "")
        print(f"\n>>> Processing tile: {tile_id}")

        sub_file = os.path.join(output_dir, f"CLI_{tile_id}_{id}.tif")

        masked_created = False  # default in case it fails

        try:
            tile = gpd.read_file(tile_path)

            with rasterio.open(raster_file) as src:
                out_image, out_transform = rasterio.mask.mask(src, [tile.geometry.iloc[0]], crop=True)
                out_meta = src.meta.copy()

            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "compress": "lzw"
            })

            with rasterio.open(sub_file, "w", **out_meta) as dest:
                dest.write(out_image)

            masked_created = True
            print(f"✅ Masked raster created for {tile_id}")

        except Exception as e:
            print(f"⚠️ Failed processing {tile_id}: {e}")

        log.append({
            "tile_id": tile_id,
            "raster_created": masked_created
        })

    # Save log CSV
    log_df = pd.DataFrame(log)
    log_file = os.path.join(output_dir, f"clipping_log_{id}.csv")
    log_df.to_csv(log_file, index=False)
    print(f"Processing finished. Log saved to {log_file}")

    return log_df