import fiona
from shapely.geometry import Point
import os

schema = {
    'geometry': 'Point',
    'properties': {
        'ID_N_SRIO': 'str:254'
    }
}

try:
    os.makedirs('scratch', exist_ok=True)
    with fiona.open('scratch/test.shp', 'w',
                    driver='ESRI Shapefile',
                    schema=schema,
                    crs='EPSG:4326',
                    encoding='latin-1') as dst:
        dst.write({
            'geometry': {'type': 'Point', 'coordinates': (0, 0)},
            'properties': {'ID_N_SRIO': 'test'}
        })
    print("Success with latin-1!")
except Exception as e:
    print("Failed with latin-1:")
    import traceback
    traceback.print_exc()
