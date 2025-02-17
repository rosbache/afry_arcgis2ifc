import geopandas as gpd
import ifcopenshell
import ifcopenshell.api
import afry_bimshape_lib
import time
from datetime import datetime
import re

start_time = time.time()
start_time_readable = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
print(f'Start time: {start_time_readable}')

# Create a new IFC file using library
ifc_file, context, owner_history, building, storey = afry_bimshape_lib.create_new_ifc_file()



# Create a blank model
# model = run("project.create_file", version="IFC4")
# project = run("root.create_entity", model, ifc_class="IfcProject", name="My Project")
# run("unit.assign_unit", model)
# context = run("context.add_context", model, context_type="Model")
# body = run("context.add_context", model, context_type="Model",
#     context_identifier="Body", target_view="MODEL_VIEW", parent=context)

# site = run("root.create_entity", model, ifc_class="IfcSite", name="My Site")
# run("aggregate.assign_object", model, relating_object=project, product=site)







### MAIN CODE ###
# shapefile_path = 'KulturminneBygning_PUNKT.shp'
# gdf = gpd.read_file(shapefile_path)


# Read the shapefile with point geometry
shapefile_paths =  ['Bygning_FLATE_utvalg.shp']#, ['KulturminneBygning_PUNKT.shp']
for shapefile_path in shapefile_paths:
    gdf = gpd.read_file(shapefile_path)
    for idx, row in gdf.iterrows():
        geometry = row.geometry
        attributes = row.drop('geometry').to_dict()
        if geometry.geom_type == 'Point':
            afry_bimshape_lib.create_volume_from_point(ifc_file, context, owner_history, storey, geometry, size=5, attributes=attributes)
        # elif geometry.geom_type == 'LineString':
            # afry_bimshape_lib.create_volume_from_linestring(ifc_file, context, owner_history, building, storey, geometry, depth=0.1, attributes=attributes)
        elif geometry.geom_type == 'Polygon':
            afry_bimshape_lib.create_volume_from_polygon(ifc_file, context, owner_history, storey, geometry, depth=0.1, attributes=attributes)
        else:
            print(f"Geometry type {geometry.geom_type} not supported")
            continue
# Save the IFC file
output_filename = re.sub(r'_(PUNKT|KURVE|FLATE|TEKST)', '', shapefile_path).replace('.shp', '.ifc')
ifc_file.write(output_filename)
print(f"IFC file saved as {output_filename}")

end_time = time.time()
elapsed_time = end_time - start_time
