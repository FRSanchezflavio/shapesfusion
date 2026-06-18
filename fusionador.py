import tkinter as tk
from tkinter import filedialog, messagebox
import geopandas as gpd
import pandas as pd
import os
import shutil
from collections import defaultdict

class FusionadorQGISApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fusión de Mapas del Delito - QGIS Essen")
        self.root.geometry("750x500")
        self.root.configure(bg="#2b2b2b")

        # Almacenar archivos de cada grupo
        # Estructura: { ".shp": ruta, ".dbf": ruta, ".prj": ruta, ".qpj": ruta, ".shx": ruta }
        self.grupo_a = {}
        self.grupo_b = {}
        self.nombre_base_a = ""
        self.nombre_base_b = ""

        # Título
        titulo = tk.Label(root, text="Fusionar Shapefiles (5 + 5 → 5)",
                          font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
        titulo.pack(pady=10)

        subtitulo = tk.Label(root,
                             text="Seleccioná los 5 archivos (.shp, .dbf, .prj, .qpj, .shx) de cada shapefile",
                             font=("Arial", 9), bg="#2b2b2b", fg="#888888")
        subtitulo.pack()

        # --- GRUPO A ---
        lbl_a = tk.Label(root, text="Grupo A — Primer shapefile (5 archivos)",
                         font=("Arial", 10), bg="#2b2b2b", fg="#2196F3")
        lbl_a.pack(anchor="w", padx=20, pady=(10, 0))

        btn_grupo_a = tk.Button(root, text="SELECCIONAR GRUPO A (5 archivos)",
                                bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                command=lambda: self.seleccionar_grupo("A"), cursor="hand2")
        btn_grupo_a.pack(pady=5)

        self.lista_a = tk.Listbox(root, height=5, font=("Consolas", 9),
                                  bg="#1e1e1e", fg="#00ff88", selectbackground="#3a3a3a")
        self.lista_a.pack(fill="x", padx=20, pady=(0, 5))

        # --- GRUPO B ---
        lbl_b = tk.Label(root, text="Grupo B — Segundo shapefile (5 archivos)",
                         font=("Arial", 10), bg="#2b2b2b", fg="#FF9800")
        lbl_b.pack(anchor="w", padx=20, pady=(5, 0))

        btn_grupo_b = tk.Button(root, text="SELECCIONAR GRUPO B (5 archivos)",
                                bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                                command=lambda: self.seleccionar_grupo("B"), cursor="hand2")
        btn_grupo_b.pack(pady=5)

        self.lista_b = tk.Listbox(root, height=5, font=("Consolas", 9),
                                  bg="#1e1e1e", fg="#ffcc00", selectbackground="#3a3a3a")
        self.lista_b.pack(fill="x", padx=20, pady=(0, 5))

        # --- Estado ---
        self.lbl_estado = tk.Label(root, text="Seleccioná ambos grupos para fusionar",
                                   font=("Arial", 10), bg="#2b2b2b", fg="#aaaaaa")
        self.lbl_estado.pack(pady=5)

        # --- Botón FUSIONAR ---
        btn_fusionar = tk.Button(root, text="FUSIONAR (A + B → 5 archivos nuevos)",
                                 bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                 command=self.fusionar_archivos, cursor="hand2")
        btn_fusionar.pack(pady=10)

    def obtener_ruta_inicial(self):
        """Devuelve la ruta UNC por defecto o C:/ de fallback si no está accesible."""
        ruta = r"\\ANALISIS-3\Analisis-3\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES"
        if os.path.exists(ruta):
            return os.path.normpath(ruta)
        return "C:/"

    def seleccionar_grupo(self, grupo):
        """Seleccionar los 5 archivos componentes de UN shapefile (.shp, .dbf, .prj, .qpj, .shx)."""
        directorio_inicial = self.obtener_ruta_inicial()

        rutas = filedialog.askopenfilenames(
            initialdir=directorio_inicial,
            title=f"Seleccionar los 5 archivos del Grupo {grupo} (.shp, .dbf, .prj, .qpj, .shx)",
            filetypes=(("Archivos Shapefile", "*.shp *.dbf *.prj *.qpj *.shx"),
                        ("Todos los archivos", "*.*"))
        )

        if not rutas:
            return

        # Normalizar rutas (corrige problemas con rutas de red UNC)
        rutas = [os.path.normpath(r) for r in rutas]

        if len(rutas) != 5:
            messagebox.showwarning(
                "Cantidad incorrecta",
                f"Debes seleccionar exactamente 5 archivos (.shp, .dbf, .prj, .qpj, .shx).\n"
                f"Seleccionaste: {len(rutas)}"
            )
            return

        # Verificar que todos pertenecen al mismo shapefile (mismo nombre base)
        nombres_base = set()
        archivos = {}
        for ruta in rutas:
            nombre = os.path.basename(ruta)
            base, ext = os.path.splitext(nombre)
            nombres_base.add(base)
            archivos[ext.lower()] = ruta

        if len(nombres_base) != 1:
            messagebox.showwarning(
                "Nombres diferentes",
                f"Todos los archivos deben pertenecer al mismo shapefile "
                f"(mismo nombre, distinta extensión).\n\n"
                f"Se detectaron {len(nombres_base)} nombres distintos:\n" +
                "\n".join(f"  • {n}" for n in sorted(nombres_base))
            )
            return

        nombre_base = nombres_base.pop()

        # Verificar que tenga el .shp
        if ".shp" not in archivos:
            messagebox.showwarning(
                "Falta .shp",
                f"No se encontró el archivo .shp para '{nombre_base}'.\n"
                "Asegurate de incluirlo en la selección."
            )
            return

        # Guardar y mostrar
        if grupo == "A":
            self.grupo_a = archivos
            self.nombre_base_a = nombre_base
            self._mostrar_archivos_en_lista(self.lista_a, nombre_base, archivos)
        else:
            self.grupo_b = archivos
            self.nombre_base_b = nombre_base
            self._mostrar_archivos_en_lista(self.lista_b, nombre_base, archivos)

        # Actualizar estado
        exts = ", ".join(sorted(archivos.keys()))
        if self.grupo_a and self.grupo_b:
            self.lbl_estado.config(
                text=f"✔ Ambos grupos listos. Podés fusionar.",
                fg="#00ff88")
        elif grupo == "A":
            self.lbl_estado.config(
                text=f"Grupo A listo: {nombre_base} [{exts}]. Falta Grupo B.",
                fg="#FF9800")
        else:
            self.lbl_estado.config(
                text=f"Grupo B listo: {nombre_base} [{exts}]. Falta Grupo A.",
                fg="#2196F3")

    def _mostrar_archivos_en_lista(self, listbox, nombre_base, archivos):
        """Muestra los 5 archivos componentes en el listbox."""
        listbox.delete(0, tk.END)
        for i, (ext, ruta) in enumerate(sorted(archivos.items())):
            nombre_archivo = os.path.basename(ruta)
            listbox.insert(tk.END, f"  {i+1}. {nombre_archivo}")

    def fusionar_archivos(self):
        """Fusiona dos shapefiles (A + B) generando 5 archivos nuevos.
        Los archivos originales NO se modifican."""

        if not self.grupo_a or not self.grupo_b:
            messagebox.showwarning(
                "Faltan archivos",
                "Debes seleccionar los 5 archivos de cada grupo antes de fusionar."
            )
            return

        try:
            # Eliminar la variable de entorno SHAPE_ENCODING para evitar conflictos con Fiona/GDAL
            os.environ.pop('SHAPE_ENCODING', None)

            # Leer ambos shapefiles con el motor Fiona y codificación explícita (solo lectura)
            gdf_a = gpd.read_file(self.grupo_a[".shp"], engine="fiona", encoding="iso-8859-1")
            gdf_b = gpd.read_file(self.grupo_b[".shp"], engine="fiona", encoding="iso-8859-1")

            # Verificar CRS
            if gdf_a.crs != gdf_b.crs:
                messagebox.showerror(
                    "Error de CRS",
                    f"Los shapefiles tienen sistemas de coordenadas diferentes.\n\n"
                    f"Grupo A ({self.nombre_base_a}): {gdf_a.crs}\n"
                    f"Grupo B ({self.nombre_base_b}): {gdf_b.crs}\n\n"
                    "Ambos deben tener el mismo CRS."
                )
                return

            # Fusionar usando solo las columnas del Grupo A (evita conflictos de campos)
            columnas_a = [c for c in gdf_a.columns if c != "geometry"]

            # Agregar columnas faltantes al Grupo B (rellenar con vacío)
            for col in columnas_a:
                if col not in gdf_b.columns:
                    gdf_b[col] = ""

            # Quedarse solo con las columnas de A + geometry
            gdf_b_ajustado = gdf_b[columnas_a + ["geometry"]]

            fusionado = gpd.GeoDataFrame(
                pd.concat([gdf_a[columnas_a + ["geometry"]], gdf_b_ajustado], ignore_index=True)
            )
            fusionado.set_crs(gdf_a.crs, inplace=True)

            # Pedir carpeta de destino
            carpeta_destino = filedialog.askdirectory(
                initialdir=self.obtener_ruta_inicial(),
                title="Seleccionar carpeta donde guardar el shapefile fusionado"
            )
            if not carpeta_destino:
                return

            # Nombre del archivo de salida por defecto: INFORME
            nombre_salida = "INFORME"
            ruta_salida_shp = os.path.join(carpeta_destino, nombre_salida + ".shp")

            # Eliminar archivos de salida previos si existen (evita conflictos)
            for ext in [".shp", ".dbf", ".shx", ".prj", ".cpg", ".qpj"]:
                archivo_previo = os.path.join(carpeta_destino, nombre_salida + ext)
                if os.path.exists(archivo_previo):
                    os.remove(archivo_previo)

            # Escribir usando fiona directamente con schema explícito
            import fiona
            from fiona.crs import CRS as FionaCRS

            # Detectar tipo de geometría
            tipo_geom = gdf_a.geometry.geom_type.iloc[0]

            # Construir schema: todas las propiedades como str para evitar errores
            propiedades = {col: "str:254" for col in columnas_a}
            schema = {
                "geometry": tipo_geom,
                "properties": propiedades
            }

            with fiona.open(ruta_salida_shp, "w",
                            driver="ESRI Shapefile",
                            schema=schema,
                            crs=fusionado.crs.to_wkt(),
                            encoding="iso-8859-1") as dst:
                for _, row in fusionado.iterrows():
                    props = {}
                    for col in columnas_a:
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

            # Copiar archivos adicionales que fiona no genera (ej: .qpj)
            extensiones_generadas = {".shp", ".dbf", ".shx", ".prj", ".cpg"}
            for ext, ruta_original in self.grupo_a.items():
                if ext not in extensiones_generadas:
                    ruta_destino = os.path.join(carpeta_destino, nombre_salida + ext)
                    shutil.copy2(ruta_original, ruta_destino)

            # Listar archivos creados
            archivos_generados = []
            for archivo in os.listdir(carpeta_destino):
                base, _ = os.path.splitext(archivo)
                if base == nombre_salida:
                    archivos_generados.append(archivo)

            lista_generados = "\n".join(f"  • {a}" for a in sorted(archivos_generados))
            messagebox.showinfo(
                "Éxito",
                f"Shapefile fusionado creado en:\n{carpeta_destino}\n\n"
                f"Archivos generados:\n{lista_generados}\n\n"
                "Los archivos originales NO fueron modificados.\n"
                "Ya podés abrirlo en QGIS."
            )
            self.lbl_estado.config(text="✔ Fusión completada exitosamente", fg="#00ff88")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al fusionar:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FusionadorQGISApp(root)
    root.mainloop()
