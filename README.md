## Fusionador de shapefiles

Iniciar la aplicacion:

```powershell
cd C:\Estadistica\Qgis\shapesfusion
python .\fusionador.py
```

La pantalla permite dos formas de carga:

- Seleccion rapida: lee `rutas_shpbac.txt` o `rutas_shp.txt` si esta junto a `fusionador.py`.
- Carga manual: mantiene el boton `AGREGAR GRUPO (+)` para elegir los 5 archivos de un shapefile.

El TXT debe contener una ruta `.shp` por linea. El programa arma automaticamente las rutas hermanas con el mismo nombre base:

```text
C:\Mapas\MAPA DELICTUAL CRIA AGUILARES-URS.shp
```

Para esa ruta busca:

```text
MAPA DELICTUAL CRIA AGUILARES-URS.shp
MAPA DELICTUAL CRIA AGUILARES-URS.dbf
MAPA DELICTUAL CRIA AGUILARES-URS.prj
MAPA DELICTUAL CRIA AGUILARES-URS.qpj
MAPA DELICTUAL CRIA AGUILARES-URS.shx
```

Codigos reconocidos:

- `URE`: Regional Este
- `URO`: Regional Oeste
- `URN`: Regional Norte
- `URS`: Regional Sur
- `URC`: Regional Capital
