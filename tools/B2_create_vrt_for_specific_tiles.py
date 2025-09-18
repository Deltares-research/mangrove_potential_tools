import os
from collections import defaultdict
from osgeo import gdal

root = "/p/11211992-tki-mangrove-restoration/01_data/0_Workflow/areas_of_interest"

gdal.UseExceptions()
groups = defaultdict(list)

# Recorrer los archivos y agrupar
for dirpath, _, filenames in os.walk(root):
    for filename in filenames:
        if not filename.lower().endswith((".tif")):
            continue

        prefix = filename.split("_")[0]  # primer bloque antes del "_"

        if filename.startswith("GMW_"):
            continue  # ignorar archivos que empiezan con GMW

        if prefix == "R25":
            if not filename.endswith("_2020.tif"):
                continue  # solo archivos R25 de 2020
        # para otros prefijos no aplicamos restricciones

        full_path = os.path.join(dirpath, filename)
        groups[prefix].append(full_path)

# Crear VRTs usando GDAL Python API
for prefix, files in groups.items():
    if files:
        print(f"\nCreating VRT for prefix '{prefix}' with {len(files)} files:")
        for f in files:
            print(f"  {f}")

        output_vrt = os.path.join(root, f"{prefix}.vrt")
        vrt_options = gdal.BuildVRTOptions(separate=False)  # cada banda se mezcla
        gdal.BuildVRT(output_vrt, files, options=vrt_options)

        print(f"VRT created at: {output_vrt}")
    else:
        print(f"No matching .tif files found for prefix '{prefix}'.")
