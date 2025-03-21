import geopandas as gpd
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.style
import afry_bimshape_lib
import time
from datetime import datetime
import re
import json
from typing import Dict, List, Union
import argparse
import os
from pathlib import Path

# start_time = time.time()
# start_time_readable = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
# print(f'Start time: {start_time_readable}')

# # Create a new IFC file using library
# ifc_file, context, owner_history, building, storey = afry_bimshape_lib.create_new_ifc_file()

# # Load styles from JSON file
# styles_raw = afry_bimshape_lib.load_style_settings('fkb-bygning_style.json')

# # Create styles from JSON file
# styles = afry_bimshape_lib.create_styles(ifc_file, styles_raw)

# # Read the shapefile with point geometry
# shapefile_paths = ['Bygning_FLATE_utvalg.shp', 'Bygning_PUNKT.shp']
# for shapefile_path in shapefile_paths:
#     gdf = gpd.read_file(shapefile_path)
#     for idx, row in gdf.iterrows():
#         geometry = row.geometry
#         # print(f"Processing row {idx} with geometry type {geometry.geom_type}")
#         attributes = row.drop('geometry').to_dict()
#         if geometry.geom_type == 'Point':
#             afry_bimshape_lib.create_volume_from_point(ifc_file, context, owner_history, storey, geometry, size=2, attributes=attributes, styles=styles)
#         elif geometry.geom_type == 'LineString':
#             # create_ifc_polyline(ifc_file, context, owner_history, geometry, attributes=attributes)
#             afry_bimshape_lib.create_volume_from_linestring(ifc_file, context, owner_history, storey, geometry, radius=0.1, attributes=attributes)
#         elif geometry.geom_type == 'Polygon':
#             afry_bimshape_lib.create_volume_from_polygon(ifc_file, context, owner_history, storey, geometry, depth=0.1, attributes=attributes, styles=styles)
#         else:
#             print(f"Geometry type {geometry.geom_type} not supported")
#             continue

# # Save the IFC file
# output_filename = re.sub(r'_(PUNKT|KURVE|FLATE|TEKST)', '', shapefile_path).replace('.shp', '.ifc')
# ifc_file.write(output_filename)
# print(f"IFC file saved as {output_filename}")

# end_time = time.time()
# elapsed_time = end_time - start_time

# print(f"Elapsed time: {elapsed_time} seconds")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Convert GIS shapefiles to IFC with styling')
    parser.add_argument('--input-folder', '-i', 
                       type=str, 
                       required=True,
                       help='Input folder containing shapefiles')
    parser.add_argument('--output-file', '-o',
                       type=str,
                       required=True,
                       help='Output IFC file name')
    parser.add_argument('--style-file', '-s',
                       type=str,
                       required=True,
                       help='JSON file containing styling information')
    return parser.parse_args()

def get_shapefiles(folder_path: str) -> List[str]:
    """Get all shapefiles in the specified folder"""
    return list(Path(folder_path).glob('*.shp'))

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    start_time = time.time()
    start_time_readable = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f'Start time: {start_time_readable}')

    # Create a new IFC file using library
    ifc_file, context, owner_history, building, storey = afry_bimshape_lib.create_new_ifc_file()

    # Load styles from JSON file
    styles_raw = afry_bimshape_lib.load_style_settings(args.style_file)

    # Create styles from JSON file
    styles = afry_bimshape_lib.create_styles(ifc_file, styles_raw)

    # Get all shapefiles in the input folder
    shapefile_paths = get_shapefiles(args.input_folder)
    print(f"Found {len(shapefile_paths)} shapefiles in {args.input_folder}")

    # Process each shapefile
    for shapefile_path in shapefile_paths:
        print(f"Processing {shapefile_path}")
        gdf = gpd.read_file(shapefile_path)
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            attributes = row.drop('geometry').to_dict()
            
            if geometry.geom_type == 'Point':
                afry_bimshape_lib.create_volume_from_point(
                    ifc_file, context, owner_history, storey, 
                    geometry, size=2, attributes=attributes, styles=styles
                )
            elif geometry.geom_type == 'LineString':
                afry_bimshape_lib.create_volume_from_linestring(
                    ifc_file, context, owner_history, storey,
                    geometry, radius=0.1, attributes=attributes, styles=styles
                )
            elif geometry.geom_type == 'Polygon':
                afry_bimshape_lib.create_volume_from_polygon(
                    ifc_file, context, owner_history, storey,
                    geometry, depth=0.1, attributes=attributes, styles=styles
                )
            else:
                print(f"Geometry type {geometry.geom_type} not supported")
                continue

    # Save the IFC file
    output_path = args.output_file
    if not output_path.lower().endswith('.ifc'):
        output_path += '.ifc'
    
    ifc_file.write(output_path)
    print(f"IFC file saved as {output_path}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Bygning.ifc" -s "fkb-bygning_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Matrikkel.ifc" -s "fkb-matrikkel_style.json"

<<<<<<< Updated upstream
=======
    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Samferdsel2.ifc" -s "fkb-vei_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Stakk_01_gm-eks_GIS_Gatenavn.ifc" -s "fkb-adresse_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Stakk_01_gm-eks_GIS_GNR-BNR.ifc" -s "fkb-matrikkel_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Bygning_gjonnes.ifc" -s "fkb-bygning_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\Downloads\stakkevollvegen" -o "stakkevoll.ifc" -s "fkb-bygning_style.json"
>>>>>>> Stashed changes
    