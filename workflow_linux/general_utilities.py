import os
import re
import glob
import inspect
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

def get_processing_time(start_time, end_time, time_logfile): 
    elapsed_seconds = end_time - start_time
    frame = inspect.stack()[1]
    calling_script = os.path.basename(frame.filename)
    log_message = f">>> Processing time: {calling_script}: {elapsed_seconds:.2f} seconds\n"
    print(log_message)
    log_path = os.path.join(time_logfile, "timing_log.txt")
    with open(log_path, "a") as f:
        f.write(log_message)

def remove_temp_files(files_list):
    for temp_file in files_list:
        try:
            os.remove(temp_file)
            print(f"🗑️ Deleted temporal file: {temp_file}")
        except OSError as e:
            print(f"⚠️ Error deleting temporal file {temp_file}: {e}")

# Clean up .xml files from qgis
def delete_xml_files(directory):
    for tide_path in glob.glob(os.path.join(directory, "*.xml")):
        try:
            os.remove(tide_path)
            print(f"🗑️ Deleted .xml file: {tide_path}")
        except OSError as e:
            print(f"⚠️ Could not delete {tide_path}: {e}")

# Clean up .geojson files from qgis
def delete_geojson_files(directory):
    for tide_path in glob.glob(os.path.join(directory, "*.geojson")):
        try:
            os.remove(tide_path)
            print(f"🗑️ Deleted .xml file: {tide_path}")
        except OSError as e:
            print(f"⚠️ Could not delete {tide_path}: {e}")

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

def get_clark_tiles_ids(clark_dir):
    tif_files = [f for f in os.listdir(clark_dir) if f.endswith(".tif")]
    raw_ids = [re.search(r'_(W|E)\d+_(N|S)\d+', f).group(0)[1:] for f in tif_files]
    normalized_ids = [normalize_id_name(t) for t in raw_ids]
    return normalized_ids

def get_clark_geometries(tiles_geometries, normalized_ids, output_dir):
    gdf = gpd.read_file(tiles_geometries)
    gdf['id'] = gdf.apply(lambda row: normalize_id_gdf(row['lat'], row['lon']), axis=1)
    selected = gdf[gdf["id"].isin(normalized_ids)]

    # Rise message in case there are tiles not found
    ids_in_gdf = set(gdf["id"])
    ids_in_files = set(normalized_ids)
    missing_ids = sorted(list(ids_in_files - ids_in_gdf))
    print(f"Selected {len(selected)} geometries out of {len(gdf)}")
    print(f"Found {len(ids_in_files) - len(missing_ids)} matches, {len(missing_ids)} missing.")

    # Save selected geometries one folder up from output_dir
    selected_dir = os.path.dirname(output_dir)
    selected.to_file(os.path.join(selected_dir,"clark_tiles.geojson"), driver="GeoJSON")    

    return selected

def get_gmw_geometries_by_centroid(gdf_gmw, gdf_clark, output_dir, tile_col="tile", projected_crs="EPSG:3857"):

    if gdf_gmw.crs != gdf_clark.crs:
        gdf_clark = gdf_clark.to_crs(gdf_gmw.crs)

    gdf_clark_proj = gdf_clark.to_crs(projected_crs)

    centroids = gdf_clark_proj.copy()
    centroids["geometry"] = gdf_clark_proj.geometry.centroid

    centroids = centroids.to_crs(gdf_gmw.crs)

    joined = gpd.sjoin(
        centroids, gdf_gmw[[tile_col, "geometry"]], 
        how="left", predicate="within"
    )

    result = gdf_clark.copy()
    result[tile_col] = joined[tile_col].values
    result = result.dropna(subset=[tile_col])
    cols = [c for c in result.columns if c != "geometry"] + ["geometry"]
    result = result[cols]
    result.reset_index(drop=True, inplace=True)
    # result.to_file(os.path.join(output_dir,"clark_gmw_tiles.geojson"), driver="GeoJSON")
    return result

def get_gmw_geometries_by_latitude(gmw_tiles, clark_tiles, output_dir):
    gmw_gdf = gpd.read_file(gmw_tiles)
    max_lat = gmw_gdf.geometry.bounds.maxy.max()
    min_lon = gmw_gdf.geometry.bounds.minx.min()

    filtered_clark_tiles = clark_tiles[
        (clark_tiles.geometry.bounds.maxy <= max_lat) &
        (clark_tiles.geometry.bounds.minx >= min_lon)
    ]

    filtered_clark_tiles = filtered_clark_tiles

    filtered_clark_tiles_dir = os.path.dirname(output_dir)
    filtered_clark_tiles.to_file(os.path.join(filtered_clark_tiles_dir,"clark_gmw_tiles.geojson"), driver="GeoJSON")  

    return filtered_clark_tiles

def add_strm_and_country_info(gmw_tiles, srtm_zip_path, countries_path, list_countries, output_dir):

    # Load data
    srtm_grid = gpd.read_file(f"zip://{srtm_zip_path}")
    countries = gpd.read_file(countries_path)

    # Drop Z from geometry
    gmw_tiles['geometry'] = gmw_tiles['geometry'].apply(drop_z)

    # Add SRTM ID to tiles
    gmw_tiles = add_overlapping_id_with_buffer(
        gmw_tiles, srtm_grid, id_col='id', new_col='id', crs_proj='EPSG:3857'
    )

    # Reproject countries if needed
    if countries.crs != gmw_tiles.crs:
        countries = countries.to_crs(gmw_tiles.crs)

    # Build spatial index for countries
    countries_sindex = countries.sindex

    # Store overlapping country names
    country_names_list = []

    for tile_geom in gmw_tiles.geometry:
        possible_matches_idx = list(countries_sindex.intersection(tile_geom.bounds))
        possible_matches = countries.iloc[possible_matches_idx]
        overlapping = possible_matches[possible_matches.intersects(tile_geom)]

        if not overlapping.empty:
            country_names = overlapping['name'].unique().tolist()
        else:
            country_names = ['any']

        country_names_list.append(country_names)

    # Add new columns to tiles
    gmw_tiles['countries'] = country_names_list
    gmw_tiles['num_countries'] = gmw_tiles['countries'].apply(lambda x: 0 if x == ['any'] else len(x))

    print("Get country tiles")
    print(f"Projection gmw_tiles: {gmw_tiles.crs}")
    print(f"Projection srtm_grid: {srtm_grid.crs}")
    print(f"Projection countries: {countries.crs}")
    print(f"Found {sum([c != ['any'] for c in country_names_list])} tiles overlapping any country.")

    # mask = gmw_tiles['countries'].apply(lambda lst: any(c in list_countries for c in lst))
    # filtered_df = gmw_tiles[mask]

    # filtered_df_dir = os.path.dirname(output_dir)
    # filtered_df.to_file(os.path.join(filtered_df_dir,"clark_gmw_tiles_country.geojson"), driver="GeoJSON")  

    gmw_tiles_dir = os.path.dirname(output_dir)
    gmw_tiles.to_file(os.path.join(gmw_tiles_dir,"clark_gmw_tiles_country.geojson"), driver="GeoJSON")  

    return gmw_tiles

def add_country_info(gmw_tiles, countries_path, list_countries, output_dir):

    # Load data
    countries = gpd.read_file(countries_path)

    # Drop Z from geometry
    gmw_tiles['geometry'] = gmw_tiles['geometry'].apply(drop_z)

    # Reproject countries if needed
    if countries.crs != gmw_tiles.crs:
        countries = countries.to_crs(gmw_tiles.crs)

    # Build spatial index for countries
    countries_sindex = countries.sindex

    # Store overlapping country names
    country_names_list = []

    for tile_geom in gmw_tiles.geometry:
        possible_matches_idx = list(countries_sindex.intersection(tile_geom.bounds))
        possible_matches = countries.iloc[possible_matches_idx]
        overlapping = possible_matches[possible_matches.intersects(tile_geom)]

        if not overlapping.empty:
            country_names = overlapping['name'].unique().tolist()
        else:
            country_names = ['any']

        country_names_list.append(country_names)

    # Add new columns to tiles
    gmw_tiles['countries'] = country_names_list
    gmw_tiles['num_countries'] = gmw_tiles['countries'].apply(lambda x: 0 if x == ['any'] else len(x))

    print("Get country tiles")
    print(f"Projection gmw_tiles: {gmw_tiles.crs}")
    print(f"Projection countries: {countries.crs}")
    print(f"Found {sum([c != ['any'] for c in country_names_list])} tiles overlapping any country.")

    # mask = gmw_tiles['countries'].apply(lambda lst: any(c in list_countries for c in lst))
    # filtered_df = gmw_tiles[mask]

    # filtered_df_dir = os.path.dirname(output_dir)
    # filtered_df.to_file(os.path.join(filtered_df_dir,"clark_gmw_tiles_country.geojson"), driver="GeoJSON")  

    gmw_tiles_dir = os.path.dirname(output_dir)
    gmw_tiles.to_file(os.path.join(gmw_tiles_dir,"clark_gmw_tiles_country.geojson"), driver="GeoJSON")  

    return gmw_tiles

def get_tiles_vector(output_dir, tiles_geometry):
    for i, row in tiles_geometry.iterrows():
        # Convert the row to a GeoDataFrame using .loc[[i]]
        tile_geom = tiles_geometry.loc[[i]]

        output_path = os.path.join(output_dir, f"TIL_{row['id']}_0.geojson")
        tile_geom.to_file(output_path, driver="GeoJSON")

        print(f"Saved: {output_path}")

    print("\n")

def get_tiles_vector_with_buffer(output_folder, gmw_tiles_country, buffer_crs, buffer_meters):

    original_crs = gmw_tiles_country.crs

    for i, row in gmw_tiles_country.iterrows():
        # Select row as GeoDataFrame
        tile_geom = gmw_tiles_country.loc[[i]]

        # Reproject to buffer CRS
        tile_geom_proj = tile_geom.to_crs(buffer_crs)

        # Apply buffer
        tile_geom_proj['geometry'] = tile_geom_proj.buffer(buffer_meters)

        # Reproject back to original CRS
        tile_geom_buffered = tile_geom_proj.to_crs(original_crs)

        # Output path
        output_path = os.path.join(output_folder, f"TIL_{row['id']}_{str(buffer_meters)}.geojson")

        # Save to GeoJSON
        tile_geom_buffered.to_file(output_path, driver="GeoJSON")

        print(f"Saved: {output_path}")

    print("\n")

def drop_z(geom):
    if geom.has_z:
        # Extract only XY coords, drop Z
        if geom.geom_type == 'Polygon':
            exterior = [(x, y) for x, y, z in geom.exterior.coords]
            interiors = [[(x, y) for x, y, z in ring.coords] for ring in geom.interiors]
            return Polygon(exterior, interiors)
        elif geom.geom_type == 'MultiPolygon':
            polygons = []
            for poly in geom.geoms:
                exterior = [(x, y) for x, y, z in poly.exterior.coords]
                interiors = [[(x, y) for x, y, z in ring.coords] for ring in poly.interiors]
                polygons.append(Polygon(exterior, interiors))
            return MultiPolygon(polygons)
    else:
        return geom
    
def add_overlapping_id_with_buffer(gdf1, gdf2, id_col='id', new_col='srtm_id', crs_proj='EPSG:3857', buffer_m=500):
    # Reproject both GeoDataFrames to projected CRS for accurate distance calculations
    gdf1_proj = gdf1.to_crs(crs_proj).copy()
    gdf2_proj = gdf2.to_crs(crs_proj).copy()

    gdf1_proj[new_col] = None
    sindex = gdf2_proj.sindex

    for idx1, geom1 in gdf1_proj.geometry.items():
        possible_matches_index = list(sindex.intersection(geom1.bounds))
        possible_matches = gdf2_proj.iloc[possible_matches_index]

        precise_matches = possible_matches[possible_matches.intersects(geom1)]
        if precise_matches.empty:
            continue

        centroid1 = geom1.centroid
        # Create buffer of specified meters around centroid1
        centroid_buffer = centroid1.buffer(buffer_m)

        # Select geometries whose centroid intersects with the buffer zone
        candidate_matches = precise_matches[precise_matches.geometry.centroid.intersects(centroid_buffer)]

        if not candidate_matches.empty:
            # Assign the id of the first matched geometry (you can modify to handle multiple)
            gdf1_proj.at[idx1, new_col] = candidate_matches.iloc[0][id_col]

    # Optionally transform back to original CRS
    gdf1_final = gdf1_proj.to_crs(gdf1.crs)

    cols = list(gdf1_final.columns)             
    cols.insert(1, cols.pop(cols.index('id')))    
    gdf1_final  = gdf1_final[cols] 
    gdf1_final 

    return gdf1_final

def get_country_tiles(geojson_path, srtm_zip_path, countries_path, country_name):
    # Load data
    gmw_tiles = gpd.read_file(geojson_path)
    srtm_grid = gpd.read_file(f"zip://{srtm_zip_path}")

    # Correct tile data and add srtm id
    gmw_tiles['geometry'] = gmw_tiles['geometry'].apply(drop_z)
    gmw_tiles = add_overlapping_id_with_buffer(gmw_tiles, srtm_grid, id_col='id', new_col='id', crs_proj='EPSG:3857')

    # Filter to overlapping with country
    countries = gpd.read_file(countries_path)
    country = countries[countries['name'] == country_name]

    if gmw_tiles.crs != country.crs:
        country = country.to_crs(gmw_tiles.crs)

    ind_sindex = country.sindex
    overlapping_idx = []

    for idx, geom in gmw_tiles.geometry.items():
        possible_matches_idx = list(ind_sindex.intersection(geom.bounds))
        possible_matches = country.iloc[possible_matches_idx]
        if not possible_matches[possible_matches.intersects(geom)].empty:
            overlapping_idx.append(idx)

    gmw_tiles_country = gmw_tiles.loc[overlapping_idx].copy()

    print("Get country tiles")
    print(f"Projection gmw_tiles: {gmw_tiles.crs}")
    print(f"Projection srtm_grid: {srtm_grid.crs}")
    print(f"Projection countries: {countries.crs}")
    print(f"Projection gmw_tiles_country: {gmw_tiles_country.crs}")
    
    print(f"Found {len(gmw_tiles_country)} polygons overlapping {country_name}.")
    print("\n")
    return gmw_tiles_country











