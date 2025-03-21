# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
This script converts GIS shapefiles to IFC (Industry Foundation Classes) files with styling information.
The styling information is read from a JSON file. The script utilizes the AFRY BIMShape library to create
and style the IFC elements.

It handles points, lines and polygons from the GIS shapefiles and creates corresponding IFC volume elements with
specific styles. The script supports multiple shapefiles and can process them in a batch.

Modules:
    - geopandas: For reading and handling GIS shapefiles.
    - ifcopenshell: For creating and manipulating IFC files.
    - afry_bimshape_lib: Custom library for creating IFC elements with specific styles.
    - time, datetime: For tracking the script execution time.
    - re, json: For handling regular expressions and JSON data.
    - argparse: For parsing command line arguments.
    - os, pathlib: For handling file system paths.
    
Functions:
    - parse_arguments(): Parses command line arguments for input folder, output file, and style file.
    - get_shapefiles(folder_path: str) -> List[str]: Retrieves all shapefiles in the specified folder.
    - main(): Main function that orchestrates the conversion process from GIS shapefiles to IFC files.

    Usage:
    Run the script from the command line with the required arguments:
    python gis2bim.py -i <input_folder> -o <output_file> -s <style_file>

"""

import geopandas as gpd
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.style
import afry_bimshape_lib
import time
import re
import json
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Union

# TODO add fucntionality to turn on or off z-values, this is currently hardcoded in the afry_bimshape_lib
    # TODO add functionality to turn on or off the creation of a centroid for polygons
    # TODO add fucntionality to give the user the option to set the size of the centroid
    # TODO add functionality to give the user the option to set the radius of the linestring
    # TODO add functionality to give the user the option to set the depth of the polygon
    # TODO add functionality to give the user the option to set the size of the point

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
def process_shapefiles(ifc_file, context, owner_history, storey, shapefile_paths, styles):
    """Process each shapefile and add volumes to the IFC file"""
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
                # centroid = geometry.centroid
                # afry_bimshape_lib.create_volume_from_point(
                #     ifc_file, context, owner_history, storey,
                #     centroid, size=2, attributes=attributes, styles=styles
                # )
            else:
                print(f"Geometry type {geometry.geom_type} not supported")
                continue
    return ifc_file

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
    print(f"Loaded {len(styles)} styles")

    # Get all shapefiles in the input folder
    shapefile_paths = get_shapefiles(args.input_folder)
    print(f"Found {len(shapefile_paths)} shapefiles in {args.input_folder}")

    # Process shapefiles and add volumes to the IFC file
    ifc_file = process_shapefiles(ifc_file, context, owner_history, storey, shapefile_paths, styles)

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

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Samferdsel2.ifc" -s "fkb-vei_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Stakk_01_gm-eks_GIS_Gatenavn.ifc" -s "fkb-adresse_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Stakk_01_gm-eks_GIS_GNR-BNR.ifc" -s "fkb-matrikkel_style.json"

    # python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Bygning_gjonnes.ifc" -s "fkb-bygning_style.json"
    