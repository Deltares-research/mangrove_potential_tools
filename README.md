# Mangrove Potential Map (MPM) Tools

This repository contains geospatial tools for processing the mangrove potential map from digishape project. The workflow processes various geospatial datasets to create mangrove potential maps and underlying layers that assess the suitability of areas for mangrove growth.

## Objectives

The tools in this repository are designed to:
- Create mangrove potential maps that identify areas suitable for mangrove growth
- Generate underlying layers that contribute to the potential assessment, including:
  - Pond classification (aquaculture areas)
  - Accommodation space based on elevation and highest astronocimal tides
  - Historical and recruitment mangrove presence
  - Proximity to existing mangroves, coastlines, and rivers
  - Subsidence rates
  - Land cover (urban areas)
  - Permanent water bodies
  - Exclusion masks

## Installation

This workflow requires two conda environments to be installed. The environments are defined in the `environment/` directory:

### 1. QGIS Environment (`qgis_env.yml`)

This environment contains QGIS and related geospatial processing libraries. Install it using:

```bash
conda env create -f environment/qgis_env.yml
conda activate qgis_env
```

### 2. Rasterio Environment (`mrpm_env.yml`)

This environment contains rasterio and other raster processing libraries. Install it using:

```bash
conda env create -f environment/mrpm_env.yml
conda activate mrpm_env
```

## Running the Workflow

The workflow can be executed using either of two shell scripts:

1. **`run_processing.sh`** - For interactive/local execution
2. **`script.sh`** - For SLURM cluster execution (includes SLURM directives)

Both scripts require a configuration JSON file as an argument. The configuration file (`config.json`) contains all paths, parameters, and settings needed for the processing.

### Usage

```bash
# For local/interactive execution
bash run_processing.sh config.json

# For SLURM cluster execution
sbatch script.sh config.json
```

The scripts automatically switch between the two conda environments (`qgis_env` and `mrpm_env`) as needed for each processing step.

## Workflow Steps

The workflow consists of 15 sequential processing steps, each implemented as a Python script. Below is a detailed explanation of each step:

### Step 01: Create VRT Files

#### `01_create_clark_vrt.py`
Creates a Virtual Raster Table (VRT) from Clark aquaculture classification data stored in ZIP files. The script:
- Scans a directory for ZIP files containing Clark classification TIFF files
- Filters files matching the specified year (e.g., 2022) and version (v1exp or v2exp)
- Creates a global VRT file (`clark_data_global.vrt`) that references all matching TIFF files without extracting them from the ZIP archives
- Uses GDAL's `/vsizip/` virtual file system to access files within ZIP archives

#### `01_create_deltadtm_vrt.py`
Creates a VRT from DeltaDTM elevation data stored in ZIP files. The script:
- Scans a directory for ZIP files containing DeltaDTM TIFF files
- Excludes mask tiles from processing
- Creates a global VRT file (`deltadtm_globe.vrt`) referencing all elevation TIFF files

#### `01_create_gmw_vrt.py`
Creates VRT files for Global Mangrove Watch (GMW) data for multiple years. The script:
- Processes each year specified in the configuration
- Creates a separate VRT file for each year (e.g., `gmw_v3_2020_gtiff.vrt`)
- References all TIFF files within the corresponding year's ZIP archive

### Step 02: Processing Tiles

#### `02_processing_tiles.py`
Prepares the tile structure for processing. The script:
- Filters Clark tiles to obtain tiles within GMW latitude range
- Matches tiles with SRTM IDs and overlapping countries
- Creates tile geometries with 0m, 10km, and 200km buffers for different analysis purposes
- Generates vector files (GeoJSON) for each tile with country information
- Outputs are saved in the `1_Tiles` directory

### Step 03: Process Clark Classification

#### `03_process_clark.py`
Processes Clark aquaculture classification data to identify pond areas. The script:
- Clips and reprojects Clark VRT data to each tile's extent and target resolution
- Creates binary and filled rasters identifying pond areas
- Outputs normalized pond classification rasters (`PON_{tile_id}.tif`) used as a factor in potential assessment

### Step 04: Process Accommodation Space

#### `04_process_gtsm.py`
Processes Global Tide and Surge Model (GTSM) data to extract tidal indicators. The script:
- Creates Voronoi polygons from GTSM point data (tidal indicators)
- Clips Voronoi polygons to tile boundaries with a 200km buffer
- Rasterizes the clipped polygons using the Highest Astronomical Tide (HAT) values
- Outputs tidal indicator rasters (`GTS_{tile_id}.tif`) for each tile

#### `04_process_elevation.py`
Processes elevation data from DeltaDTM. The script:
- Clips and reprojects DeltaDTM VRT data to each tile
- Fills NoData values in the elevation raster
- Applies a mangrove correction factor (typically 48cm) to account for mangrove canopy height
- Outputs corrected elevation rasters (`ELE_{tile_id}.tif`)

#### `04_process_intertidal_space.py`
Calculates intertidal space categories based on elevation and tidal data. The script:
- Creates binary maps for three categories:
  - **MSL**: Areas between 0 and Mean Sea Level (accommodation space)
  - **HAT**: Areas above Highest Astronomical Tide
  - **BEY**: Areas between HAT and HAT+1m (intertidal space with sea-level rise correction)
- Uses elevation and tidal data with mangrove and sea-level rise corrections
- Outputs three rasters per tile: `MSL_{tile_id}.tif`, `HAT_{tile_id}.tif`, `BEY_{tile_id}.tif`

#### `04_process_accommodation_space.py`
Combines intertidal space categories into a normalized accommodation space score. The script:
- Combines MSL and BEY categories with different weights
- Normalizes the combined values using multipliers to create a 0-1 score
- Higher scores indicate better accommodation space for mangroves
- Outputs normalized accommodation space rasters (`ACC_{tile_id}.tif`)

### Step 05: Process GMW Historical and Recruitment

#### `05_process_gmw.py`
Processes Global Mangrove Watch (GMW) data for multiple years. The script:
- Clips and reprojects GMW VRT data for each specified year to each tile
- Fills NoData values and compresses the output
- Outputs annual mangrove presence rasters (`GMW_{tile_id}_{year}.tif`) for each year

#### `05_process_historical_gmw.py`
Creates a historical mangrove presence score based on GMW time series. The script:
- Analyzes GMW data across multiple years to identify areas that were mangroves in the past
- Assigns higher scores to more recent historical mangrove presence
- Uses multipliers to normalize scores (0-1) based on the year of mangrove presence
- Outputs historical mangrove presence rasters (`HIS_{tile_id}.tif`)

#### `05_process_recruitment_gmw.py`
Creates a recruitment score based on GMW time series. The script:
- Similar to historical processing but focuses on areas that became mangroves over time
- Identifies areas where mangroves appeared in earlier years (indicating recruitment potential)
- Uses multipliers to normalize scores based on the year of first appearance
- Outputs recruitment potential rasters (`REC_{tile_id}.tif`)

### Step 06: Process GMW Proximity

#### `06_decrease_gmw_resolution.py`
Prepares GMW data at lower resolution for proximity analysis. The script:
- Clips and reprojects the most recent GMW data to a coarser resolution (approximately 100m)
- Uses tiles with 10km buffers for seed dispersal analysis
- Outputs lower-resolution GMW rasters (`PRM_{tile_id}.tif`) for proximity calculations

#### `06_process_gmw_proximity.py`
Calculates proximity to existing mangroves using morphological dilation. The script:
- Applies dilation operations at multiple distances (500m, 2500m, 10000m) to simulate seed dispersal
- Creates binary rasters indicating areas within each distance threshold
- Outputs dilated rasters (`DIL_{tile_id}_{distance}.tif`) for each distance

#### `06_normalization_gmw_proximity.py`
Normalizes proximity rasters into a single seed availability score. The script:
- Combines the three distance-based proximity rasters
- Applies multipliers to normalize the combined values (closer = higher score)
- Reprojects to target resolution and compresses
- Outputs normalized proximity to mangroves rasters (`PRM_{tile_id}.tif`)

### Step 07: Process Coastline and Rivers Proximity

#### `07_process_coastline_rivers_distance.py`
Calculates distance-based proximity to coastlines and rivers. The script:
- Creates buffered geometries around coastlines (500m, 2500m, 5000m, 7500m) and rivers (250m, 500m, 2500m)
- Clips coastline and river geometries to tile boundaries
- Rasterizes the buffered geometries at appropriate resolutions
- Outputs proximity rasters for coastlines (`COA_{tile_id}_{distance}.tif`) and rivers (`OVE_{tile_id}_{distance}.tif`)

#### `07_normalization_coastline.py`
Normalizes coastline proximity rasters into a single score. The script:
- Combines multiple distance-based coastline proximity rasters
- Applies multipliers to create a normalized score (closer to coast = higher score)
- Outputs normalized coastline proximity rasters (`PRC_{tile_id}.tif`)

#### `07_normalization_rivers.py`
Normalizes river proximity rasters into a single score. The script:
- Combines multiple distance-based river proximity rasters
- Applies multipliers to create a normalized score (closer to rivers = higher score)
- Outputs normalized river proximity rasters (`PRR_{tile_id}.tif`)

### Step 08: Process Subsidence

#### `08_clip_subsidence.py`
Clips subsidence data to tile boundaries. The script:
- Clips global subsidence rasters (2010 and 2040 projections) to each tile's extent
- Outputs clipped subsidence rasters (`CLI_{tile_id}_{year}.tif`) for further processing

#### `08_process_subsidence.py`
Processes and normalizes subsidence data. The script:
- Fills NoData values using extrapolation
- Normalizes subsidence values using multipliers (lower subsidence = higher score)
- Combines 2010 and 2040 projections using a weighted average
- Reprojects to target resolution and compresses
- Outputs normalized subsidence rasters (`SUB_{tile_id}.tif`)

### Step 09: Process Land Cover

#### `09_process_landcover.py`
Identifies urban areas from ESA WorldCover data. The script:
- Accesses ESA WorldCover data via Microsoft Planetary Computer STAC API
- Downloads and processes land cover data for each tile
- Creates binary masks identifying urban areas (class 50)
- Outputs urban area rasters (`LAN_{tile_id}.tif`) used as exclusion areas

### Step 10: Process Permanent Water

#### `10_process_permanent_water.py`
Identifies permanent water bodies excluding aquaculture ponds. The script:
- Clips and reprojects permanent water occurrence data (GSWO) to each tile
- Creates binary masks for areas with water occurrence above a threshold (typically 90%)
- Excludes areas already classified as aquaculture ponds
- Outputs permanent water rasters (`WAT_{tile_id}.tif`) used as exclusion areas

### Step 11: Process Exclusion Masks

#### `11_process_empty_areas.py`
Identifies empty areas in GMW data. The script:
- Creates binary masks for areas with NoData values in GMW 2020 data
- Outputs empty area rasters (`EMA_{tile_id}.tif`) used as templates for missing data

#### `11_process_no_valid_areas.py`
Creates a comprehensive exclusion mask combining multiple exclusion criteria. The script:
- Combines multiple exclusion layers:
  - Areas far from coastlines and rivers
  - Existing mangrove areas (2020)
  - Urban areas
  - Permanent water bodies
  - Areas with low mangrove proximity
- Creates a binary mask (`NVA_{tile_id}.tif`) where 1 = excluded, 0 = valid for potential assessment

### Step 12: Process Mangrove Potential Areas

#### `12_process_mangrove_potential_areas.py`
Calculates the final mangrove potential score. The script:
- Combines all normalized factor layers with configurable weights:
  - **PON**: Pond classification (negative factor)
  - **ACC**: Accommodation space
  - **HIS**: Historical mangrove presence
  - **PRM**: Proximity to mangroves (seed availability)
  - **PRC_PRR**: Maximum of coastline and river proximity
  - **SUB**: Subsidence (negative factor)
- Applies the exclusion mask (NVA) to set excluded areas to 0
- Calculates weighted average: `(PON×w1 + ACC×w2 + HIS×w3 + PRM×w4 + max(PRC,PRR)×w5 + SUB×w6) / sum(weights)`
- Outputs final mangrove potential maps (`MPM_{tile_id}.tif`) with scores ranging from 0-1

### Step 13: Calculate Statistics

#### `13_calculate_statistics.py`
Calculates descriptive statistics for each tile's mangrove potential map. The script:
- Computes statistics including: min, max, mean, median, standard deviation
- Calculates percentiles: 5th, 25th, 50th, 75th, 95th, 33rd, 67th (terciles)
- Counts valid pixels (non-zero values)
- Outputs a CSV file (`MPM_statistics.csv`) with statistics for each tile

### Step 14: Create Visualization

#### `14_create_visualization.py`
Creates a GeoJSON file for visualization of results. The script:
- Merges tile geometries with statistics data
- Calculates tile areas and coverage percentages
- Computes MRPM indices (median × coverage and mean × coverage)
- Removes unnecessary columns and reorders for visualization
- Outputs a GeoJSON file (`tiles_visualization.geojson`) suitable for mapping applications

### Step 15: Process COG Files

#### `15_process_cog_files.py`
Converts output rasters to Cloud-Optimized GeoTIFF (COG) format for web serving. The script:
- Processes three categories of outputs:
  - **Underlying layers**: GMW, subsidence, landcover, permanent water
  - **Subscores**: Individual factor layers (PON, ACC, HIS, PRM, PRR, PRC, SUB)
  - **Mangrove potential score**: Final MPM and exclusion mask (NVA)
- Converts all rasters to COG format with appropriate compression
- Organizes outputs into subdirectories for GeoServer or similar web mapping services
- Outputs are saved in the GeoServer folder specified in the configuration

## Output Structure

The workflow generates outputs organized in numbered directories:

- `1_Tiles/` - Tile geometries and metadata
- `2_Clark_classification/` - Pond classification rasters
- `3_Tides/` - Tidal indicator rasters
- `4_Elevation/` - Elevation rasters
- `5_Accommodation_space/` - Accommodation space rasters
- `6_GMW/` - Global Mangrove Watch rasters and proximity
- `7_Rivers/` - River proximity rasters
- `8_Coastline/` - Coastline proximity rasters
- `9_Subsidence/` - Subsidence rasters
- `10_Landcover/` - Urban area rasters
- `11_Permanent_water/` - Permanent water rasters
- `12_Empty_areas/` - Empty area masks
- `13_Mask/` - Exclusion masks
- `14_Mangrove_potential/` - Final mangrove potential maps and statistics
- `15_COG/` - Cloud-Optimized GeoTIFF files for web serving

## Configuration

The `config.json` file contains all parameters, paths, and settings. Key configuration sections include:

- **Paths**: Data directories, input files, output locations
- **Tiles**: Tile IDs to process, tiles to add/skip
- **Parameters**: Resolution, multipliers, thresholds, weights
- **Years**: GMW years to process, Clark data year
- **Environments**: QGIS environment path

Refer to the example `config.json` in the `workflow_linux/` directory for detailed parameter descriptions.

## Notes

- The workflow alternates between `qgis_env` and `mrpm_env` conda environments as different steps require different libraries
- Processing is tile-based, allowing parallel processing of multiple tiles
- Intermediate files are automatically cleaned up after each step
- The workflow includes error handling and logging for missing data or processing failures
- Processing time is logged for performance monitoring
