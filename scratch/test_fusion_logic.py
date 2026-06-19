import geopandas as gpd
import pandas as pd
import shapely.geometry as geom
import os
import shutil

def test_merge_logic():
    # 1. Create a temporary folder
    temp_dir = "scratch/temp_test"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # 2. Create 3 simple geodataframes with the same CRS but different columns
        crs = "EPSG:4326"
        
        # GDF 1: Columns A, B
        gdf1 = gpd.GeoDataFrame({
            "col_A": ["valA1", "valA2"],
            "col_B": ["valB1", "valB2"],
            "geometry": [geom.Point(0, 0), geom.Point(1, 1)]
        }, crs=crs)
        
        # GDF 2: Columns A, C
        gdf2 = gpd.GeoDataFrame({
            "col_A": ["valA3"],
            "col_C": ["valC3"],
            "geometry": [geom.Point(2, 2)]
        }, crs=crs)
        
        # GDF 3: Columns B, D
        gdf3 = gpd.GeoDataFrame({
            "col_B": ["valB4"],
            "col_D": ["valD4"],
            "geometry": [geom.Point(3, 3)]
        }, crs=crs)
        
        # Save them as shapefiles
        gdf1.to_file(os.path.join(temp_dir, "group1.shp"), encoding="iso-8859-1")
        gdf2.to_file(os.path.join(temp_dir, "group2.shp"), encoding="iso-8859-1")
        gdf3.to_file(os.path.join(temp_dir, "group3.shp"), encoding="iso-8859-1")
        
        # 3. Simulate the fusion logic in fusionador.py
        grupos = [
            {"nombre_base": "group1", "archivos": {".shp": os.path.join(temp_dir, "group1.shp")}},
            {"nombre_base": "group2", "archivos": {".shp": os.path.join(temp_dir, "group2.shp")}},
            {"nombre_base": "group3", "archivos": {".shp": os.path.join(temp_dir, "group3.shp")}},
        ]
        
        # Replicated logic:
        gdfs = []
        for g in grupos:
            path_shp = g["archivos"][".shp"]
            gdf = gpd.read_file(path_shp, engine="fiona", encoding="iso-8859-1")
            gdfs.append((g["nombre_base"], gdf))
            
        primer_nombre, primer_gdf = gdfs[0]
        ref_crs = primer_gdf.crs
        
        # Columnas del primer shapefile como base
        columnas_base = [c for c in primer_gdf.columns if c != "geometry"]
        
        # Ajustar columnas de todos los dataframes
        gdfs_ajustados = []
        for nombre, gdf in gdfs:
            for col in columnas_base:
                if col not in gdf.columns:
                    gdf[col] = ""
            gdfs_ajustados.append(gdf[columnas_base + ["geometry"]])
            
        # Concatenar todos los GeoDataFrames
        fusionado = gpd.GeoDataFrame(
            pd.concat(gdfs_ajustados, ignore_index=True)
        )
        fusionado.set_crs(ref_crs, inplace=True)
        
        # Write merged shapefile
        out_shp = os.path.join(temp_dir, "INFORME.shp")
        
        # Detect type of geometry
        tipo_geom = primer_gdf.geometry.geom_type.iloc[0]
        
        import fiona
        propiedades = {col: "str:254" for col in columnas_base}
        schema = {
            "geometry": tipo_geom,
            "properties": propiedades
        }
        
        with fiona.open(out_shp, "w",
                        driver="ESRI Shapefile",
                        schema=schema,
                        crs=fusionado.crs.to_wkt(),
                        encoding="iso-8859-1") as dst:
            for _, row in fusionado.iterrows():
                props = {}
                for col in columnas_base:
                    val = row[col]
                    if pd.isna(val) or val is None:
                        props[col] = ""
                    else:
                        props[col] = str(val)[:254]
                
                feature = {
                    "geometry": row.geometry.__geo_interface__,
                    "properties": props
                }
                dst.write(feature)
                
        # 4. Read back the merged shapefile and verify
        merged_gdf = gpd.read_file(out_shp, engine="fiona", encoding="iso-8859-1")
        
        print("Merged GDF contents:")
        print(merged_gdf)
        
        # Assertions
        assert len(merged_gdf) == 4, f"Expected 4 rows, got {len(merged_gdf)}"
        assert list(merged_gdf.columns) == ["col_A", "col_B", "geometry"], f"Expected cols ['col_A', 'col_B', 'geometry'], got {list(merged_gdf.columns)}"
        
        # Row 1 (from gdf1):
        assert merged_gdf.loc[0, "col_A"] == "valA1"
        assert merged_gdf.loc[0, "col_B"] == "valB1"
        
        # Row 2 (from gdf1):
        assert merged_gdf.loc[1, "col_A"] == "valA2"
        assert merged_gdf.loc[1, "col_B"] == "valB2"
        
        # Row 3 (from gdf2): has col_A but not col_B (should be empty/None)
        assert merged_gdf.loc[2, "col_A"] == "valA3"
        assert pd.isna(merged_gdf.loc[2, "col_B"]) or merged_gdf.loc[2, "col_B"] == ""
        
        # Row 4 (from gdf3): has neither col_A nor col_B (col_A should be empty/None, col_B should be valB4)
        assert pd.isna(merged_gdf.loc[3, "col_A"]) or merged_gdf.loc[3, "col_A"] == ""
        assert merged_gdf.loc[3, "col_B"] == "valB4"
        
        print("\nAll assertions passed successfully! The multi-merge logic works perfectly.")
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_merge_logic()
