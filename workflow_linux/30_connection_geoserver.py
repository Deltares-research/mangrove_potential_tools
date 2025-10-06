# Import the library
from geo.Geoserver import Geoserver

# Initialize the library
geo = Geoserver('https://digishape.openearth.nl/geoserver/', username='admin', password='6#3XN3u7yB#a9nvfy$jePst!#FRIR4')

# For creating workspace
# geo.create_workspace(workspace='demo')

# For uploading raster data to the geoserver
geo.create_coveragestore(layer_name='layer1', path = '/opt/mangrove-potential/TEST_API/MPM_S01E117.tif', workspace='mangrove_potential')





