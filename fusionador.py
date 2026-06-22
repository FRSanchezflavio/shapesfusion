import tkinter as tk
from tkinter import filedialog, messagebox
import geopandas as gpd
import pandas as pd
import os
import re
import shutil
from collections import defaultdict

REGIONALES = {
    "URE": "Regional Este",
    "URO": "Regional Oeste",
    "URN": "Regional Norte",
    "URS": "Regional Sur",
    "URC": "Regional Capital",
}

ARCHIVOS_SHAPE = [".shp", ".dbf", ".prj", ".qpj", ".shx"]

class FusionadorQGISApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fusión de Mapas del Delito - QGIS Essen")
        self.root.geometry("1100x760")
        self.root.configure(bg="#2b2b2b")

        # Almacenar lista de grupos cargados
        # Cada elemento: { "nombre_base": str, "archivos": { ".shp": path, ".dbf": path, ... } }
        self.grupos = []
        self.catalogo_shp = defaultdict(list)
        self.catalogo_vars = {}
        self.catalogo_frame = None
        self.lbl_catalogo_estado = None

        # Título
        titulo = tk.Label(root, text="Fusionar Múltiples Shapefiles (Grupos de 5 archivos)",
                          font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
        titulo.pack(pady=(15, 5))

        subtitulo = tk.Label(root,
                             text="Agregá grupos de 5 archivos (.shp, .dbf, .prj, .qpj, .shx) para fusionarlos",
                             font=("Arial", 9), bg="#2b2b2b", fg="#888888")
        subtitulo.pack(pady=(0, 15))

        self.crear_panel_catalogo()

        # --- CONTENEDOR PRINCIPAL ---
        main_frame = tk.Frame(root, bg="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20)

        # Columna Izquierda: Lista de grupos
        frame_izq = tk.Frame(main_frame, bg="#2b2b2b")
        frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        lbl_grupos = tk.Label(frame_izq, text="Grupos cargados para fusionar:",
                              font=("Arial", 10, "bold"), bg="#2b2b2b", fg="#2196F3")
        lbl_grupos.pack(anchor="w", pady=(0, 5))

        # Listbox de grupos con scrollbar
        frame_listbox = tk.Frame(frame_izq, bg="#2b2b2b")
        frame_listbox.pack(fill="both", expand=True)

        self.listbox_grupos = tk.Listbox(frame_listbox, height=8, font=("Arial", 10),
                                         bg="#1e1e1e", fg="#00ff88", selectbackground="#3a3a3a")
        self.listbox_grupos.pack(side="left", fill="both", expand=True)

        scroll_grupos = tk.Scrollbar(frame_listbox, orient="vertical", command=self.listbox_grupos.yview)
        scroll_grupos.pack(side="right", fill="y")
        self.listbox_grupos.config(yscrollcommand=scroll_grupos.set)

        # Bind del evento de selección
        self.listbox_grupos.bind("<<ListboxSelect>>", self.on_grupo_seleccionado)

        # Columna Derecha: Botones de gestión
        frame_der = tk.Frame(main_frame, bg="#2b2b2b")
        frame_der.pack(side="right", fill="y", padx=(10, 0))

        lbl_acciones = tk.Label(frame_der, text="Acciones:",
                                font=("Arial", 10, "bold"), bg="#2b2b2b", fg="white")
        lbl_acciones.pack(anchor="w", pady=(0, 5))

        btn_agregar = tk.Button(frame_der, text="AGREGAR GRUPO (+)",
                                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=22,
                                 command=self.agregar_grupo, cursor="hand2")
        btn_agregar.pack(pady=5)

        btn_quitar = tk.Button(frame_der, text="QUITAR SELECCIONADO (-)",
                               bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=22,
                               command=self.quitar_grupo, cursor="hand2")
        btn_quitar.pack(pady=5)

        btn_limpiar = tk.Button(frame_der, text="LIMPIAR TODOS",
                                bg="#d32f2f", fg="white", font=("Arial", 10, "bold"), width=22,
                                command=self.limpiar_grupos, cursor="hand2")
        btn_limpiar.pack(pady=5)

        # --- DETALLES DEL GRUPO SELECCIONADO ---
        frame_detalles = tk.Frame(root, bg="#2b2b2b")
        frame_detalles.pack(fill="x", padx=20, pady=15)

        lbl_detalles = tk.Label(frame_detalles, text="Componentes del grupo seleccionado:",
                                font=("Arial", 10, "bold"), bg="#2b2b2b", fg="#ffcc00")
        lbl_detalles.pack(anchor="w", pady=(0, 5))

        self.listbox_detalles = tk.Listbox(frame_detalles, height=5, font=("Consolas", 9),
                                           bg="#1e1e1e", fg="#ffcc00", selectbackground="#1e1e1e",
                                           highlightthickness=0)
        self.listbox_detalles.pack(fill="x")

        # --- SECCIÓN INFERIOR: ESTADO Y FUSIONAR ---
        frame_inferior = tk.Frame(root, bg="#2b2b2b")
        frame_inferior.pack(fill="x", side="bottom", padx=20, pady=(0, 20))

        self.lbl_estado = tk.Label(frame_inferior, text="Agregá al menos 2 grupos para fusionar",
                                   font=("Arial", 10), bg="#2b2b2b", fg="#aaaaaa")
        self.lbl_estado.pack(pady=5)

        self.btn_fusionar = tk.Button(frame_inferior, text="FUSIONAR (0 grupos → 5 archivos nuevos)",
                                      bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                      command=self.fusionar_archivos, cursor="hand2")
        self.btn_fusionar.pack(pady=10)

        self.cargar_catalogo_por_defecto()

    def crear_panel_catalogo(self):
        """Crea el panel de seleccion rapida por regional y comisaria."""
        panel = tk.LabelFrame(
            self.root,
            text="Seleccion rapida desde rutas_shp",
            font=("Arial", 10, "bold"),
            bg="#2b2b2b",
            fg="#ffffff",
            padx=10,
            pady=8
        )
        panel.pack(fill="both", padx=20, pady=(0, 12))

        barra = tk.Frame(panel, bg="#2b2b2b")
        barra.pack(fill="x", pady=(0, 8))

        tk.Button(
            barra,
            text="CARGAR TXT DE RUTAS",
            bg="#455A64",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.seleccionar_txt_rutas,
            cursor="hand2"
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            barra,
            text="AGREGAR SELECCIONADOS",
            bg="#1976D2",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.agregar_catalogo_seleccionado,
            cursor="hand2"
        ).pack(side="left", padx=6)

        tk.Button(
            barra,
            text="MARCAR TODO",
            bg="#2E7D32",
            fg="white",
            font=("Arial", 9, "bold"),
            command=lambda: self.marcar_catalogo(True),
            cursor="hand2"
        ).pack(side="left", padx=6)

        tk.Button(
            barra,
            text="DESMARCAR",
            bg="#6D4C41",
            fg="white",
            font=("Arial", 9, "bold"),
            command=lambda: self.marcar_catalogo(False),
            cursor="hand2"
        ).pack(side="left", padx=6)

        self.lbl_catalogo_estado = tk.Label(
            barra,
            text="Buscando rutas_shpbac.txt o rutas_shp.txt...",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#aaaaaa"
        )
        self.lbl_catalogo_estado.pack(side="left", padx=12)

        canvas_frame = tk.Frame(panel, bg="#2b2b2b")
        canvas_frame.pack(fill="both", expand=True)

        self.catalogo_canvas = tk.Canvas(
            canvas_frame,
            height=190,
            bg="#242424",
            highlightthickness=1,
            highlightbackground="#3a3a3a"
        )
        self.catalogo_canvas.pack(side="left", fill="both", expand=True)

        scroll_y = tk.Scrollbar(canvas_frame, orient="vertical", command=self.catalogo_canvas.yview)
        scroll_y.pack(side="right", fill="y")
        self.catalogo_canvas.configure(yscrollcommand=scroll_y.set)

        self.catalogo_frame = tk.Frame(self.catalogo_canvas, bg="#242424")
        self.catalogo_canvas.create_window((0, 0), window=self.catalogo_frame, anchor="nw")
        self.catalogo_frame.bind(
            "<Configure>",
            lambda event: self.catalogo_canvas.configure(scrollregion=self.catalogo_canvas.bbox("all"))
        )

    def cargar_catalogo_por_defecto(self):
        """Carga automaticamente el primer TXT de rutas disponible junto al script."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidatos = ["rutas_shpbac.txt", "rutas_shp.txt"]
        for nombre in candidatos:
            ruta = os.path.join(base_dir, nombre)
            if os.path.exists(ruta):
                self.cargar_catalogo_desde_txt(ruta)
                return

        self.actualizar_catalogo_ui()
        self.lbl_catalogo_estado.config(
            text="No encontre rutas_shpbac.txt ni rutas_shp.txt junto al programa.",
            fg="#ffcc00"
        )

    def seleccionar_txt_rutas(self):
        """Permite elegir manualmente el TXT que contiene rutas .shp."""
        ruta = filedialog.askopenfilename(
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            title="Seleccionar archivo TXT con rutas .shp",
            filetypes=(("Archivos TXT", "*.txt"), ("Todos los archivos", "*.*"))
        )
        if ruta:
            self.cargar_catalogo_desde_txt(ruta)

    def leer_lineas_txt(self, ruta_txt):
        """Lee el TXT probando codificaciones comunes en Windows."""
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                with open(ruta_txt, "r", encoding=encoding) as archivo:
                    return archivo.readlines()
            except UnicodeDecodeError:
                continue
        with open(ruta_txt, "r", encoding="latin-1", errors="ignore") as archivo:
            return archivo.readlines()

    def cargar_catalogo_desde_txt(self, ruta_txt):
        """Carga shapefiles desde un TXT y los agrupa por regional."""
        self.catalogo_shp.clear()
        self.catalogo_vars.clear()

        lineas = self.leer_lineas_txt(ruta_txt)
        vistos = set()
        omitidos = 0

        for linea in lineas:
            ruta_shp = self.normalizar_linea_ruta(linea)
            if not ruta_shp:
                omitidos += 1
                continue

            clave = os.path.normcase(os.path.normpath(ruta_shp))
            if clave in vistos:
                continue
            vistos.add(clave)

            grupo = self.crear_grupo_desde_shp(ruta_shp)
            codigo = self.obtener_codigo_regional(f"{grupo['nombre_base']} {ruta_shp}")
            regional = REGIONALES.get(codigo, "Sin regional detectada")
            comisaria = self.obtener_nombre_comisaria(grupo["nombre_base"], codigo)

            self.catalogo_shp[regional].append({
                "codigo": codigo,
                "comisaria": comisaria,
                "grupo": grupo
            })

        for regional in self.catalogo_shp:
            self.catalogo_shp[regional].sort(key=lambda item: item["comisaria"])

        self.actualizar_catalogo_ui()
        total = sum(len(items) for items in self.catalogo_shp.values())
        estado = f"{total} comisarias precargadas desde {os.path.basename(ruta_txt)}"
        if omitidos:
            estado += f" ({omitidos} lineas omitidas)"
        self.lbl_catalogo_estado.config(text=estado, fg="#00ff88" if total else "#ffcc00")

    def normalizar_linea_ruta(self, linea):
        """Extrae una ruta .shp desde una linea simple del TXT."""
        texto = linea.strip().strip('"').strip("'")
        if not texto or texto.startswith("#"):
            return None

        match = re.search(r"([A-Za-z]:\\.*?\.shp|\\\\.*?\.shp)", texto, re.IGNORECASE)
        if match:
            texto = match.group(1)

        if not texto.lower().endswith(".shp"):
            return None
        return os.path.normpath(texto)

    def crear_grupo_desde_shp(self, ruta_shp):
        """Reconstruye el grupo de archivos hermanos a partir de una ruta .shp."""
        ruta_shp = os.path.normpath(ruta_shp)
        carpeta = os.path.dirname(ruta_shp)
        nombre_base = os.path.splitext(os.path.basename(ruta_shp))[0]
        archivos = {
            ext: os.path.join(carpeta, nombre_base + ext)
            for ext in ARCHIVOS_SHAPE
        }
        return {
            "nombre_base": nombre_base,
            "archivos": archivos
        }

    def obtener_codigo_regional(self, texto):
        """Detecta URE/URO/URN/URS/URC en el nombre o en la ruta completa."""
        match = re.search(r"(?<![A-Z0-9])(URE|URO|URN|URS|URC)(?![A-Z0-9])", texto.upper())
        return match.group(1) if match else ""

    def obtener_nombre_comisaria(self, nombre_base, codigo):
        """Limpia el nombre para mostrar solo la comisaria o dependencia."""
        nombre = re.sub(r"(?i)^MAPA\s+DELICTUAL\s+", "", nombre_base).strip()
        if codigo:
            nombre = re.sub(rf"(?i)\s*[-_/]?\s*\b{codigo}\b(?:[-_\s]*\d{{4}})?", "", nombre).strip()
        return nombre.strip(" -_") or nombre_base

    def actualizar_catalogo_ui(self):
        """Dibuja los checks por regional."""
        for widget in self.catalogo_frame.winfo_children():
            widget.destroy()

        self.catalogo_vars.clear()
        if not self.catalogo_shp:
            tk.Label(
                self.catalogo_frame,
                text="Sin comisarias precargadas. Carga un TXT con rutas .shp.",
                font=("Arial", 10),
                bg="#242424",
                fg="#bbbbbb"
            ).pack(anchor="w", padx=10, pady=10)
            return

        orden = ["Regional Capital", "Regional Norte", "Regional Sur", "Regional Este", "Regional Oeste"]
        regionales = [r for r in orden if r in self.catalogo_shp]
        regionales += sorted(r for r in self.catalogo_shp if r not in regionales)

        for columna, regional in enumerate(regionales):
            frame_regional = tk.LabelFrame(
                self.catalogo_frame,
                text=f"{regional} ({len(self.catalogo_shp[regional])})",
                font=("Arial", 9, "bold"),
                bg="#242424",
                fg="#ffffff",
                padx=6,
                pady=4
            )
            frame_regional.grid(row=0, column=columna, sticky="nw", padx=8, pady=6)

            acciones = tk.Frame(frame_regional, bg="#242424")
            acciones.pack(fill="x", pady=(0, 3))
            tk.Button(
                acciones,
                text="Todo",
                width=7,
                bg="#37474F",
                fg="white",
                command=lambda r=regional: self.marcar_regional(r, True),
                cursor="hand2"
            ).pack(side="left", padx=(0, 3))
            tk.Button(
                acciones,
                text="Nada",
                width=7,
                bg="#4E342E",
                fg="white",
                command=lambda r=regional: self.marcar_regional(r, False),
                cursor="hand2"
            ).pack(side="left")

            for item in self.catalogo_shp[regional]:
                var = tk.BooleanVar(value=False)
                grupo = item["grupo"]
                clave = os.path.normcase(os.path.normpath(grupo["archivos"][".shp"]))
                self.catalogo_vars[clave] = var
                chk = tk.Checkbutton(
                    frame_regional,
                    text=item["comisaria"],
                    variable=var,
                    anchor="w",
                    justify="left",
                    width=32,
                    bg="#242424",
                    fg="#dddddd",
                    activebackground="#242424",
                    activeforeground="#ffffff",
                    selectcolor="#1e1e1e"
                )
                chk.pack(anchor="w")

    def marcar_catalogo(self, valor):
        for var in self.catalogo_vars.values():
            var.set(valor)

    def marcar_regional(self, regional, valor):
        for item in self.catalogo_shp.get(regional, []):
            shp = item["grupo"]["archivos"][".shp"]
            clave = os.path.normcase(os.path.normpath(shp))
            if clave in self.catalogo_vars:
                self.catalogo_vars[clave].set(valor)

    def agregar_catalogo_seleccionado(self):
        """Agrega a la fusion los grupos marcados en el catalogo."""
        seleccionados = []
        for items in self.catalogo_shp.values():
            for item in items:
                grupo = item["grupo"]
                shp = grupo["archivos"][".shp"]
                clave = os.path.normcase(os.path.normpath(shp))
                if self.catalogo_vars.get(clave) and self.catalogo_vars[clave].get():
                    seleccionados.append(grupo)

        if not seleccionados:
            messagebox.showwarning("Sin seleccion", "Marca al menos una comisaria del catalogo.")
            return

        existentes = {
            os.path.normcase(os.path.normpath(g["archivos"][".shp"]))
            for g in self.grupos
            if ".shp" in g["archivos"]
        }

        agregados = 0
        duplicados = 0
        faltantes = []

        for grupo in seleccionados:
            shp_clave = os.path.normcase(os.path.normpath(grupo["archivos"][".shp"]))
            if shp_clave in existentes:
                duplicados += 1
                continue

            faltan = [ext for ext, ruta in grupo["archivos"].items() if not os.path.exists(ruta)]
            if faltan:
                faltantes.append(f"{grupo['nombre_base']}: {', '.join(faltan)}")
                continue

            self.grupos.append(grupo)
            existentes.add(shp_clave)
            agregados += 1

        self.actualizar_interfaz_grupos()
        if self.grupos:
            self.listbox_grupos.selection_clear(0, tk.END)
            self.listbox_grupos.selection_set(tk.END)
            self.listbox_grupos.see(tk.END)
            self.on_grupo_seleccionado()

        mensaje = f"Agregados: {agregados}"
        if duplicados:
            mensaje += f"\nDuplicados ignorados: {duplicados}"
        if faltantes:
            mensaje += "\n\nNo se agregaron por archivos faltantes:\n" + "\n".join(faltantes[:12])
            if len(faltantes) > 12:
                mensaje += f"\n... y {len(faltantes) - 12} mas"

        messagebox.showinfo("Seleccion rapida", mensaje)

    def obtener_ruta_inicial(self):
        """Devuelve la ruta UNC por defecto o C:/ de fallback si no está accesible."""
        ruta = r"\\ANALISIS-3\Analisis-3\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES"
        if os.path.exists(ruta):
            return os.path.normpath(ruta)
        return "C:/"

    def agregar_grupo(self):
        """Selecciona y agrega un grupo de 5 archivos componentes de un shapefile."""
        directorio_inicial = self.obtener_ruta_inicial()

        rutas = filedialog.askopenfilenames(
            initialdir=directorio_inicial,
            title="Seleccionar los 5 archivos del Grupo (.shp, .dbf, .prj, .qpj, .shx)",
            filetypes=(("Archivos Shapefile", "*.shp *.dbf *.prj *.qpj *.shx"),
                        ("Todos los archivos", "*.*"))
        )

        if not rutas:
            return

        # Normalizar rutas
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

        # Guardar en la lista de grupos
        self.grupos.append({
            "nombre_base": nombre_base,
            "archivos": archivos
        })

        # Actualizar listbox
        self.actualizar_interfaz_grupos()
        
        # Seleccionar el último agregado
        self.listbox_grupos.selection_clear(0, tk.END)
        self.listbox_grupos.selection_set(tk.END)
        self.listbox_grupos.see(tk.END)
        self.on_grupo_seleccionado()

    def on_grupo_seleccionado(self, event=None):
        """Se activa al seleccionar un grupo de la lista principal."""
        seleccion = self.listbox_grupos.curselection()
        self.listbox_detalles.delete(0, tk.END)
        
        if not seleccion:
            return
            
        indice = seleccion[0]
        if 0 <= indice < len(self.grupos):
            grupo = self.grupos[indice]
            archivos = grupo["archivos"]
            for i, (ext, ruta) in enumerate(sorted(archivos.items())):
                nombre_archivo = os.path.basename(ruta)
                self.listbox_detalles.insert(tk.END, f"  {i+1}. {nombre_archivo}")

    def quitar_grupo(self):
        """Quita el grupo actualmente seleccionado."""
        seleccion = self.listbox_grupos.curselection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor, selecciona un grupo para quitar.")
            return
            
        indice = seleccion[0]
        if 0 <= indice < len(self.grupos):
            del self.grupos[indice]
            self.actualizar_interfaz_grupos()
            self.listbox_detalles.delete(0, tk.END)
            
            # Seleccionar el elemento anterior o posterior si existe
            if len(self.grupos) > 0:
                nuevo_indice = min(indice, len(self.grupos) - 1)
                self.listbox_grupos.selection_set(nuevo_indice)
                self.on_grupo_seleccionado()

    def limpiar_grupos(self):
        """Elimina todos los grupos agregados."""
        if not self.grupos:
            return
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas eliminar todos los grupos agregados?"):
            self.grupos.clear()
            self.actualizar_interfaz_grupos()
            self.listbox_detalles.delete(0, tk.END)

    def actualizar_interfaz_grupos(self):
        """Actualiza el listbox de grupos, la etiqueta de estado y el texto del botón de fusionar."""
        self.listbox_grupos.delete(0, tk.END)
        for i, g in enumerate(self.grupos):
            self.listbox_grupos.insert(tk.END, f"  {i+1}. {g['nombre_base']} ({len(g['archivos'])} archivos)")
            
        cant = len(self.grupos)
        self.btn_fusionar.config(text=f"FUSIONAR ({cant} grupos → 5 archivos nuevos)")
        
        if cant >= 2:
            self.lbl_estado.config(text=f"✔ {cant} grupos listos. Podés fusionar.", fg="#00ff88")
        else:
            self.lbl_estado.config(text=f"Agregá al menos 2 grupos para fusionar. Cargados: {cant}", fg="#aaaaaa")

    def fusionar_archivos(self):
        """Fusiona todos los shapefiles agregados generando 5 archivos nuevos en la carpeta de destino.
        Los archivos originales NO se modifican."""

        cant = len(self.grupos)
        if cant < 2:
            messagebox.showwarning(
                "Faltan archivos",
                f"Debes seleccionar al menos 2 grupos antes de fusionar. Actualmente hay {cant}."
            )
            return

        try:
            # Eliminar la variable de entorno SHAPE_ENCODING para evitar conflictos con Fiona/GDAL
            os.environ.pop('SHAPE_ENCODING', None)

            # Leer todos los shapefiles con el motor Fiona y codificación iso-8859-1
            gdfs = []
            for g in self.grupos:
                path_shp = g["archivos"][".shp"]
                gdf = gpd.read_file(path_shp, engine="fiona", encoding="iso-8859-1")
                gdfs.append((g["nombre_base"], gdf))

            # Tomar el primer GeoDataFrame como referencia para CRS y columnas
            primer_nombre, primer_gdf = gdfs[0]
            ref_crs = primer_gdf.crs

            # Verificar que todos tengan el mismo CRS
            for nombre, gdf in gdfs[1:]:
                if gdf.crs != ref_crs:
                    messagebox.showerror(
                        "Error de CRS",
                        f"Los shapefiles tienen sistemas de coordenadas diferentes.\n\n"
                        f"Referencia ({primer_nombre}): {ref_crs}\n"
                        f"Grupo ({nombre}): {gdf.crs}\n\n"
                        "Todos deben tener el mismo CRS."
                    )
                    return

            # Columnas del primer shapefile (Grupo de referencia)
            columnas_base = [c for c in primer_gdf.columns if c != "geometry"]

            # Ajustar columnas de todos los dataframes
            gdfs_ajustados = []
            for nombre, gdf in gdfs:
                # Agregar columnas faltantes rellenando con vacío
                for col in columnas_base:
                    if col not in gdf.columns:
                        gdf[col] = ""
                # Mantener solo las columnas de la referencia + geometry en el orden exacto
                gdfs_ajustados.append(gdf[columnas_base + ["geometry"]])

            # Concatenar todos los GeoDataFrames
            fusionado = gpd.GeoDataFrame(
                pd.concat(gdfs_ajustados, ignore_index=True)
            )
            fusionado.set_crs(ref_crs, inplace=True)

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

            # Eliminar archivos de salida previos si existen
            for ext in [".shp", ".dbf", ".shx", ".prj", ".cpg", ".qpj"]:
                archivo_previo = os.path.join(carpeta_destino, nombre_salida + ext)
                if os.path.exists(archivo_previo):
                    os.remove(archivo_previo)

            # Escribir usando fiona directamente con schema explícito
            import fiona

            # Detectar tipo de geometría del primer shapefile
            tipo_geom = primer_gdf.geometry.geom_type.iloc[0]

            # Construir schema: todas las propiedades como str para evitar errores
            propiedades = {col: "str:254" for col in columnas_base}
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

            # Copiar archivos adicionales del primer grupo (ej: .qpj) que fiona no genera
            extensiones_generadas = {".shp", ".dbf", ".shx", ".prj", ".cpg"}
            primer_grupo_archivos = self.grupos[0]["archivos"]
            for ext, ruta_original in primer_grupo_archivos.items():
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
