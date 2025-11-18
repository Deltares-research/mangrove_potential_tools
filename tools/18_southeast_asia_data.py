import os
import shutil
import geopandas as gpd

# === CONFIGURATION ===
geojson_path = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/14_Mangrove_potential/global/tiles_visualization.geojson"
src_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/global"
dst_root = "/p/11211992-tki-mangrove-restoration/01_data/1_Geoserver/southeast_asia"
filtered_geojson = os.path.join(os.path.dirname(geojson_path), "tiles_visualization_southeast_asia.geojson")

# === DEFINE SOUTHEAST ASIA COUNTRIES ===
sea_countries = {
    "Vietnam", "Thailand", "Malaysia", "Singapore", "Indonesia", "Philippines",
    "Cambodia", "Laos", "Myanmar", "Timor-Leste", "Brunei"
}

# === LOAD GEOJSON ===
print("📂 Reading GeoJSON...")
gdf = gpd.read_file(geojson_path)

# === FILTER BY COUNTRY NAMES ===
def has_sea_country(countries_str):
    if not isinstance(countries_str, str):
        return False
    countries = [c.strip() for c in countries_str.split(",")]
    return any(c in sea_countries for c in countries)

filtered_gdf = gdf[gdf["countries"].apply(has_sea_country)]

# === SAVE FILTERED GEOJSON ===
filtered_gdf.to_file(filtered_geojson, driver="GeoJSON")
print(f"✅ Saved filtered GeoJSON: {filtered_geojson}")

# === GET TILE IDS ===
selected_ids = set(filtered_gdf["id"].astype(str))
print(f"✅ Found {len(selected_ids)} tile IDs for Southeast Asia.")

# === COPY FILES ===
os.makedirs(dst_root, exist_ok=True)

print("📦 Copying matching .tif files...")
for root, dirs, files in os.walk(src_root):
    for file in files:
        if not file.lower().endswith(".tif"):
            continue

        # Extract ID from filename and check
        for tile_id in selected_ids:
            if tile_id in file:
                src_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, src_root)
                dst_folder_path = os.path.join(dst_root, rel_path)
                os.makedirs(dst_folder_path, exist_ok=True)
                dst_file_path = os.path.join(dst_folder_path, file)

                shutil.copy2(src_file_path, dst_file_path)
                print(f"Copied {src_file_path} → {dst_file_path}")
                break  # Avoid redundant matches for the same file

print("🎉 Done copying all relevant Southeast Asia files.")