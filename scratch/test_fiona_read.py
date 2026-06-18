import geopandas as gpd
import fiona
import os

# Clean environment
os.environ.pop('SHAPE_ENCODING', None)

schema = {
    'geometry': 'Point',
    'properties': {
        'ID_N_SRIO': 'str:254',
        'Detalle': 'str:254'
    }
}

# 1. Write a shapefile using fiona with Latin-1 encoding
shp_path = 'scratch/test_latin.shp'
try:
    with fiona.open(shp_path, 'w',
                    driver='ESRI Shapefile',
                    schema=schema,
                    crs='EPSG:4326',
                    encoding='iso-8859-1') as dst:
        dst.write({
            'geometry': {'type': 'Point', 'coordinates': (0, 0)},
            # 0xe9 is 'é' in latin-1. Let's put a latin-1 string
            'properties': {'ID_N_SRIO': '123', 'Detalle': 'José'}
        })
    print("Successfully wrote Latin-1 shapefile.")
except Exception as e:
    print("Failed writing:", e)

# 2. Try to read it back using geopandas with fiona engine and encoding
try:
    gdf = gpd.read_file(shp_path, engine='fiona', encoding='iso-8859-1')
    print("Successfully read with fiona engine!")
    print("Detalle value:", gdf['Detalle'].iloc[0])
except Exception as e:
    print("Failed reading with fiona engine:", e)

# 3. Try to read it back using geopandas with pyogrio engine and encoding
try:
    gdf = gpd.read_file(shp_path, engine='pyogrio', encoding='iso-8859-1')
    print("Successfully read with pyogrio engine!")
    print("Detalle value:", gdf['Detalle'].iloc[0])
except Exception as e:
    print("Failed reading with pyogrio engine:", e)
