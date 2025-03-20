#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Description:
This script processes two IFC files: one containing 2D footprints of buildings and another containing 3D models of buildings. It performs the following tasks:

1. Opens the IFC files.
2. Loads style settings from a JSON file.
3. Extracts bounding boxes from the 2D footprints and centroids from the 3D models.
4. Finds overlapping geometries between the 2D and 3D data.
5. Copies properties from the 2D footprints to the corresponding 3D models based on the overlapping geometries.
6. Applies styles to the 3D models based on the copied properties.
7. Saves the modified 3D model to a new IFC file.

The script uses the `ifcopenshell` library for handling IFC files and the `afry_bimshape_lib` for style management.

Example usage:
python copy_properties.py -f path/to/footprint.ifc -v path/to/volume.ifc -o path/to/output.ifc -s path/to/styles.json
python copy_properties.py -f gjonnes_footprint.ifc -v gjonnes_3d.ifc -o gjonnes_combined.ifc -s fkb-bygning_style.json

'''

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.style
import ifcopenshell.util.shape
import numpy as np
from typing import Dict, Tuple, List, Union
import json
import time
import argparse
from datetime import datetime

import afry_bimshape_lib

def get_geometry_bounds(shape):
    """Get bounding box from shape geometry"""

    verts = np.array(shape.geometry.verts).reshape(-1, 3)
    mins = verts.min(axis=0)
    maxs = verts.max(axis=0)
    return [mins[0], mins[1], mins[2], maxs[0], maxs[1], maxs[2]]

def get_geometry_and_location(ifc_file) -> Dict[str, Tuple[np.ndarray, any, np.ndarray]]:
    """Get geometry data for all products"""

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    # settings.set(settings.SEW_SHELLS, True)
    
    geometry_data = {}
    for product in ifc_file.by_type('IfcProduct'):
        if product.is_a('IfcOpeningElement'):
            continue
            
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            verts = np.array(shape.geometry.verts).reshape(-1, 3)
            center = verts.mean(axis=0)
            bounds = get_geometry_bounds(shape)
            
            geometry_data[product.GlobalId] = (center, shape, bounds)
            
        except RuntimeError as e:
            print(f"Failed to process {product.is_a()}: {e}")
            
    return geometry_data

def get_shape_bbox_centroid(ifc_file) -> Dict[str, Tuple[np.ndarray, any, np.ndarray]]:
    """Get bounding box and centroid of shapes"""

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    geometry_data = {}
    for product in ifc_file.by_type('IfcProduct'):
        if product.is_a('IfcOpeningElement'):
            continue
            
        try:
            # Create shape from product
            shape = ifcopenshell.geom.create_shape(settings, product)
            verts = np.array(shape.geometry.verts).reshape(-1, 3)
            
            # Calculate centroid and bounds
            centroid = verts.mean(axis=0)
            bounds = get_geometry_bounds(shape)
            
            geometry_data[product.GlobalId] = (centroid, shape, bounds)
            # print(f'Product: {product.is_a()}, Centroid: {centroid}')

        except RuntimeError as e:
            print(f"Failed to process {product.is_a()}: {e}")
            
    return geometry_data

def find_overlapping_bbox(bboxes, centroids):
    """Find overlapping bounding boxes and return mapping"""
    # centroids of volume and bounding box of footprint is used to find overlapping geometries
    overlapping = {}
    for bbox_id, (_, _, bbox) in bboxes.items():
        overlapping[bbox_id] = []
        for cent_id, (centroid, _, _) in centroids.items():
            if bbox[0] < centroid[0] < bbox[3] and bbox[1] < centroid[1] < bbox[4]:
                dist = np.linalg.norm(centroid[:2] - np.array([(bbox[0] + bbox[3])/2, (bbox[1] + bbox[4])/2]))
                overlapping[bbox_id].append((cent_id, dist))
    
    # Sort matches by distance
    for bbox_id in overlapping:
        overlapping[bbox_id].sort(key=lambda x: x[1])
    
    return overlapping

def copy_properties(source_elem, target_elem, ifc_target_file, owner_history):
    """Copy properties from source element to target element, ignoring certain property sets"""
    # Define property sets to ignore
    ignored_psets = [
        'BaseQuantities',
        'Qto_',  # Prefix for all quantity sets
        'GSA_',  # Prefix for GSA property sets
        'Pset_',  # Prefix for common property sets
        'Common'
    ]

    # Get all property sets from source element
    for rel in source_elem.IsDefinedBy:
        if not rel.is_a('IfcRelDefinesByProperties'):
            continue

        source_pset = rel.RelatingPropertyDefinition
        if not source_pset.is_a('IfcPropertySet'):
            continue

        # Skip ignored property sets
        if any(source_pset.Name.startswith(ignore) for ignore in ignored_psets):
            print(f"Skipping property set: {source_pset.Name}")
            continue

        try:
            # Create new property set with ifcopenshell.guid.new()
            new_props = []
            for prop in source_pset.HasProperties:
                if prop.is_a('IfcPropertySingleValue'):
                    new_prop = ifc_target_file.createIfcPropertySingleValue(
                        prop.Name,
                        prop.Description,
                        prop.NominalValue,
                        prop.Unit
                    )
                    new_props.append(new_prop)
            
            if new_props:  # Only create property set if we have properties
                new_pset = ifc_target_file.createIfcPropertySet(
                    ifcopenshell.guid.new(),  # Use correct GUID generator
                    owner_history,
                    source_pset.Name,
                    source_pset.Description,
                    new_props
                )
                
                # Assign property set to target element
                ifc_target_file.createIfcRelDefinesByProperties(
                    ifcopenshell.guid.new(),  # Use correct GUID generator
                    owner_history,
                    None,
                    None,
                    [target_elem],
                    new_pset
                )                
        except Exception as e:
            print(f"Warning: Failed to copy property set {source_pset.Name}: {e}")

def copy_matching_properties(source_file, target_file, overlapping, styles):
    """Copy properties and apply styles for all matching pairs"""

    owner_history = target_file.by_type("IfcOwnerHistory")[0]
    styled_count = 0
    
    for source_id, matches in overlapping.items():
        source_elem = source_file.by_guid(source_id)
        if not source_elem:
            continue
            
        if not matches:
            print(f"No matching elements found for {source_id}")
            continue
            
        # Process all matches for this source element
        for target_id, dist in matches:
            target_elem = target_file.by_guid(target_id)
            if not target_elem:
                continue
                
            # Copy properties
            copy_properties(source_elem, target_elem, target_file, owner_history)
            # Apply style based on copied properties
            if apply_style_to_element(target_elem, target_file, styles):
                styled_count += 1

    print(f"\nApplied styles to {styled_count} elements")

def apply_style_to_element(element, ifc_file, styles):
    """Apply style to element based on its properties"""
    
    # Get attributes from element's properties
    attributes = {}
    for rel in element.IsDefinedBy:
        if rel.is_a('IfcRelDefinesByProperties'):
            pset = rel.RelatingPropertyDefinition
            if pset.is_a('IfcPropertySet'):
                for prop in pset.HasProperties:
                    if prop.is_a('IfcPropertySingleValue') and prop.NominalValue:
                        attributes[prop.Name] = prop.NominalValue.wrappedValue

    # Find matching style
    matching_style = afry_bimshape_lib.get_matching_style(attributes, styles)
    if matching_style and matching_style in styles:
        style = styles[matching_style]
        try:
            # Get the shape representation directly from element
            if element.Representation and element.Representation.Representations:
                shape_representation = element.Representation.Representations[0]
                
                # Create styled item
                ifcopenshell.api.style.assign_representation_styles(
                ifc_file,
                shape_representation=shape_representation,
                styles=[style['style']]  # Use the actual style object from the dictionary
            )
                return True
        except Exception as e:
            print(f"Failed to apply style: {e}")

    return False

def parse_arguments():
    """Parse command line arguments"""
      
    parser = argparse.ArgumentParser(description='Copy properties from 2D footprints to 3D objects in IFC file')
    parser.add_argument('--input-footprint-file', '-f', 
                       type=str, 
                       required=True,
                       help='Input IFC file containing 2D footprints')
    parser.add_argument('--input-target-file', '-v', 
                       type=str, 
                       required=True,
                       help='Input IFC file containing 3D volumes to be updated')
    parser.add_argument('--output-file', '-o',
                       type=str,
                       required=True,
                       help='Output IFC file name')
    parser.add_argument('--style-file', '-s',
                       type=str,
                       required=True,
                       help='JSON file containing styling information')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    start_time = time.time()
    start_time_readable = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f'Start time: {start_time_readable}')
    
    # Open IFC files
    print("\nOpening IFC files...")
    # file_footprint = ifcopenshell.open('Bygning.ifc') # 2D footprint of buildings
    # file_target = ifcopenshell.open('bygninger_Stakkevollvegen.ifc') # 3D model of buildings

    file_footprint = ifcopenshell.open(args.input_footprint_file) # 2D footprint of buildings
    file_target = ifcopenshell.open(args.input_target_file) # 3D model of buildings
    
    # Load styles
    print("\nLoading styles...")
    styles_raw = afry_bimshape_lib.load_style_settings(args.style_file)
    styles = afry_bimshape_lib.create_styles2(file_target, styles_raw)
    print(f"Loaded {len(styles)} styles")
    # print(styles['Bolig'])

    # Get bounding boxes of the 2D footprints
    bboxes = get_geometry_and_location(file_footprint) # 2D footprints
    print(f"Found {len(bboxes)} bounding boxes")
    
    # Get centroids of the 3D buildings
    centroids = get_shape_bbox_centroid(file_target) # 3D buildings
    print(f"Found {len(centroids)} centroids")

    # Find overlapping geometries
    print("\nFinding overlapping geometries...")
    overlapping = find_overlapping_bbox(bboxes, centroids)
    total_matches = sum(len(matches) for matches in overlapping.values())
    print(f"Found {len(overlapping)} source geometries with {total_matches} total matches")
    
    # Copy properties and apply styles
    print("\nCopying properties and applying styles...")
    copy_matching_properties(file_footprint, file_target, overlapping, styles)

    # Save modified file
    output_path = args.output_file
    file_target.write(output_path)
    print(f"\nSaved modified file as: {output_path}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
    
    # Example usage:
    # python copy_properties.py -f path/to/footprint.ifc -v path/to/volume.ifc -o path/to/output.ifc -s path/to/styles.json
    # python copy_properties.py -f gjonnes_footprint.ifc -v gjonnes_3d.ifc -o gjonnes_combined.ifc -s fkb-bygning_style.json