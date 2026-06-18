import tkinter as tk
from tkinter import filedialog, messagebox
import geopandas as gpd
import pandas as pd
import os

class FusionadorQGISApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fusión de Mapas del Delito - QGIS Essen")
        self.root.geometry("600x400")
        
        # Lista para almacenar las rutas de los 5 archivos seleccionados
        self.archivos_seleccionados = [tk.StringVar() for _ in range(5)]
        
        # Título de la aplicación
        titulo = tk.Label(root, text="Fusionar 5 Archivos Shapefile (.shp)", font=("Arial", 14, "bold"))
        titulo.pack(pady=10)

        # Crear 5 filas para seleccionar cada archivo
        for i in range(5):
            frame = tk.Frame(root)
            frame.pack(pady=5, fill="x", padx=20)
            
            lbl = tk.Label(frame, text=f"Archivo {i+1}:", width=10, anchor="w")
            lbl.pack(side="left")
            
            entrada = tk.Entry(frame, textvariable=self.archivos_seleccionados[i], width=50, state="readonly")
            entrada.pack(side="left", padx=5)
            
            btn_buscar = tk.Button(frame, text="Buscar", command=lambda idx=i: self.seleccionar_archivo(idx))
            btn_buscar.pack(side="left")

        # Botón para iniciar la fusión
        btn_fusionar = tk.Button(root, text="FUSIONAR Y CREAR INFORME", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.fusionar_archivos)
        btn_fusionar.pack(pady=30)

    def seleccionar_archivo(self, indice):
        """Abre un cuadro de diálogo para seleccionar un archivo .shp en la unidad Z:"""
        # Directorio inicial sugerido basado en tus requerimientos
        directorio_inicial = "Z:/MAPA DEL DELITO/MAPAS DEL DELITO POR JURISDICCIONES/"
        if not os.path.exists(directorio_inicial):
            directorio_inicial = "C:/"  # Alternativa si no está conectado al servidor en ese momento

        ruta = filedialog.askopenfilename(
            initialdir=directorio_inicial,
            title=f"Seleccionar Archivo {indice+1}",
            filetypes=(("Archivos Shapefile", "*.shp"), ("Todos los archivos", "*.*"))
        )
        
        if ruta:
            self.archivos_seleccionados[indice].set(ruta)

    def fusionar_archivos(self):
        """Lee los 5 archivos como copias, los une y guarda un nuevo archivo llamado 'informe.shp'"""
        rutas = [var.get() for var in self.archivos_seleccionados]
        
        # Validar que se hayan seleccionado exactamente 5 archivos
        if any(ruta == "" for ruta in rutas):
            messagebox.showwarning("Faltan archivos", "Por favor, asegúrate de seleccionar los 5 archivos antes de fusionar.")
            return
            
        try:
            mapas_geograficos = []
            crs_referencia = None
            
            # Leer cada archivo. GeoPandas lee el archivo sin modificarlo (es seguro)
            for i, ruta in enumerate(rutas):
                gdf = gpd.read_file(ruta)
                
                # Verificar consistencia de CRS entre archivos
                if i == 0:
                    crs_referencia = gdf.crs
                elif gdf.crs != crs_referencia:
                    messagebox.showerror(
                        "Error de CRS",
                        f"El archivo {i+1} tiene un sistema de coordenadas diferente.\n\n"
                        f"CRS esperado: {crs_referencia}\n"
                        f"CRS encontrado: {gdf.crs}\n\n"
                        "Todos los archivos deben tener el mismo CRS para fusionarse correctamente."
                    )
                    return
                
                mapas_geograficos.append(gdf)
                
            # Fusionar todos los archivos en un solo GeoDataFrame
            mapa_fusionado = gpd.GeoDataFrame(pd.concat(mapas_geograficos, ignore_index=True))
            mapa_fusionado.set_crs(crs_referencia, inplace=True)
            
            # Pedir al usuario dónde guardar el archivo, usando 'informe' como defecto
            ruta_guardado = filedialog.asksaveasfilename(
                defaultextension=".shp",
                initialfile="informe",
                title="Guardar archivo fusionado como...",
                filetypes=(("Archivos Shapefile", "*.shp"),)
            )
            
            if ruta_guardado:
                # Guardar el nuevo archivo
                mapa_fusionado.to_file(ruta_guardado, driver="ESRI Shapefile")
                messagebox.showinfo("Éxito", f"Los archivos se han fusionado correctamente en:\n{ruta_guardado}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al fusionar los archivos:\n{str(e)}")

# Punto de inicio de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = FusionadorQGISApp(root)
    root.mainloop()
