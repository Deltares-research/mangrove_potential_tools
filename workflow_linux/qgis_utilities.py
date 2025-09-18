import os
import sys
from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem
)
from qgis.analysis import QgsNativeAlgorithms
import processing
from processing.core.Processing import Processing

def initialize_qgis(qgis_env_path: str):
    """
    Initializes the QGIS environment given the path to the QGIS installation inside the conda environment.
    This function can be safely called from any script using QGIS and processing tools.
    """
    print("\n>>> Initializing QGIS")
    # Add QGIS Python paths
    sys.path.append(os.path.join(qgis_env_path, "python"))
    sys.path.append(os.path.join(qgis_env_path, "python", "plugins"))

    # Set environment variables
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QGIS_PREFIX_PATH"] = qgis_env_path

    # Initialize QGIS
    QgsApplication.setPrefixPath(qgis_env_path, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    print("QGIS initialized successfully.")
    return qgs  # Return qgs instance so you can later call `qgs.exitQgis()` if needed

def initialize_qgis_linux(qgis_env_path: str):
    """
    Initializes the QGIS environment given the path to the QGIS installation inside the conda environment.
    This function can be safely called from any script using QGIS and processing tools.
    """
    print("\n>>> Initializing QGIS")
    # Add QGIS Python paths
    sys.path.append(os.path.join(qgis_env_path, "share/qgis/python"))
    sys.path.append(os.path.join(qgis_env_path, "share/qgis/python/plugins"))

    # Set environment variables
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QGIS_PREFIX_PATH"] = qgis_env_path
    os.environ["PYTHONPATH"] = os.path.join(qgis_env_path, "share/qgis/python")

    # Initialize QGIS
    QgsApplication.setPrefixPath(qgis_env_path, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    print("QGIS initialized successfully.")
    return qgs  # Return qgs instance so you can later call `qgs.exitQgis()` if needed

def initialize_processing():
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    print("Processing native algorithms initialized successfully.")

def get_projwin(tile_path, rounding=True):
    vlayer = QgsVectorLayer(tile_path, "tile", "ogr")
    if not vlayer.isValid():
        print(f"⚠️ Could not load: {tile_path}")
    
    extent = vlayer.extent()
    if rounding:
        xmin = round(extent.xMinimum())
        xmax = round(extent.xMaximum())
        ymin = round(extent.yMinimum())
        ymax = round(extent.yMaximum())
    else:
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()            
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()    
        
    projwin = f"{xmin},{xmax},{ymax},{ymin} [EPSG:4326]"
    print(projwin)
    return projwin

def reproject_raster(input_raster, output_raster, resolution, extent):
    processing.run("gdal:warpreproject", {
        'INPUT': input_raster,
        'SOURCE_CRS': None,  # Or use QgsCoordinateReferenceSystem('EPSG:xxxx') if needed
        'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
        'RESAMPLING': 0,  # Nearest neighbor
        'NODATA': None,
        'TARGET_RESOLUTION': resolution, # (25m) - 0.0002777777777777778 (30 m)
        'OPTIONS': '',
        'DATA_TYPE': 0,  # Same as input
        'TARGET_EXTENT': extent,
        'TARGET_EXTENT_CRS': 'EPSG:4326',
        'MULTITHREADING': False,
        'EXTRA': '',
        'OUTPUT': output_raster
    })

def raster_calculator(expression, input_rasters, output_raster):
    print(f"📐 Raster calculator expression:\n{expression}")
    processing.run("qgis:rastercalculator", {
        'EXPRESSION': expression,
        'LAYERS': input_rasters,
        'CELLSIZE':None, #0.000222222222222,
        'CRS': None, #QgsCoordinateReferenceSystem('EPSG:4326'),
        'EXTENT': None,
        'OUTPUT': output_raster
    })

def fill_and_compress(input_raster, filled_raster, compressed_raster, extra):
    # Fill no data
    processing.run("native:fillnodata", {
        'INPUT': input_raster,
        'BAND': 1,
        'FILL_VALUE': 0,
        'OUTPUT': filled_raster
    })

    # Compress raster
    processing.run("gdal:translate", {
        'INPUT': filled_raster,
        'TARGET_CRS': None,
        'NODATA': None,
        'COPY_SUBDATASETS': False,
        'OPTIONS': 'COMPRESS=LZW',
        'EXTRA': extra,
        'DATA_TYPE': 0,
        'OUTPUT': compressed_raster
    })

def fill_raster(input_raster, filled_raster):
    # Fill no data
    processing.run("native:fillnodata", {
        'INPUT': input_raster,
        'BAND': 1,
        'FILL_VALUE': 0,
        'OUTPUT': filled_raster
    })

def compress_raster(input_raster, compressed_raster):
    # Compress raster
    processing.run("gdal:translate", {
        'INPUT': input_raster,
        'TARGET_CRS': None,
        'NODATA': None,
        'COPY_SUBDATASETS': False,
        'OPTIONS': 'COMPRESS=LZW',
        'EXTRA': '',
        'DATA_TYPE': 0,
        'OUTPUT': compressed_raster
    })

def rasterize_vector(input_vector, field, target_res_deg, projwin, output_raster):
    # Rasterize using the 'FIELD' attribute
    processing.run("gdal:rasterize", {
        'INPUT': input_vector,
        'FIELD': field,
        'BURN': 0,
        'USE_Z': False,
        'UNITS': 1,
        'WIDTH': target_res_deg, 
        'HEIGHT':  target_res_deg, 
        'EXTENT': projwin,
        'NODATA': 0,
        'OPTIONS': '',
        'DATA_TYPE': 5,  # Float32
        'INIT': None,
        'INVERT': False,
        'EXTRA': '',
        'OUTPUT': output_raster
    })

def get_qgis_layer(raster_layer, raster_name):
    # Load rasters as layers with appropriate names
    qgis_layer = QgsRasterLayer(raster_layer, raster_name)
    if not qgis_layer.isValid():
        print(f"⚠️ Invalid raster: {raster_layer}")
    return qgis_layer

def clip_vrt(input_vrt, input_tile, output_vrt):
    processing.run(
        "gdal:cliprasterbymasklayer",
        {
            'INPUT': input_vrt,
            'MASK': input_tile,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'NODATA': None,
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': False,
            'SET_RESOLUTION': False,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'MULTITHREADING': False,
            'OPTIONS': '',
            'DATA_TYPE': 0,
            'EXTRA': '',
            'OUTPUT': output_vrt
        }
    )

def fill_extrapolation(input_raster, output_raster, distance):
    processing.run(
        "gdal:fillnodata",
        {
            'INPUT': input_raster,
            'BAND': 1,
            'DISTANCE': distance,
            'ITERATIONS': 0,
            'MASK_LAYER': None,
            'OPTIONS': '',
            'EXTRA': '',
            'OUTPUT': output_raster
        }
    )

def get_voronoi_from_gtsm(gtsm_points, tiles_path, til_vector, gts_vector, vor_vector, cli_vector):
    # Clip GTSM data to tile extent
    processing.run("native:clip", {
        'INPUT': gtsm_points,
        'OVERLAY': tiles_path,
        'OUTPUT': gts_vector
    })

    # Create Voronoi polygons
    processing.run("native:voronoipolygons", {
        'INPUT': gts_vector,
        'BUFFER': 100,
        'TOLERANCE': 0,
        'COPY_ATTRIBUTES': True,
        'OUTPUT': vor_vector
    })

    # Clip Voronoi polygons to tile shape
    processing.run("native:clip", {
        'INPUT': vor_vector,
        'OVERLAY': til_vector,
        'OUTPUT': cli_vector
    })