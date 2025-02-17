#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Description

'''

import os
import json
import tomllib
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.pset
import ifcopenshell.api.pset
import ifcopenshell.api.owner
import ifcopenshell.api.material
import time

def create_new_ifc_file(person_given_name="Eirik", person_family_name="Rosbach", organization_name="AFRY Norway AS"):
    """
    Creates a new IFC file with a basic structure including project, site, building, and building storey.
    Args:
        person_given_name (str): Given name of the person. Default is "Eirik".
        person_family_name (str): Family name of the person. Default is "Rosbach".
        organization_name (str): Name of the organization. Default is "AFRY Norway AS".
    Returns:
        tuple: A tuple containing the following elements:
            - ifc_file (ifcopenshell.file): The created IFC file.
            - context (ifcopenshell.entity_instance): The geometric representation context.
            - owner_history (ifcopenshell.entity_instance): The owner history of the IFC file.
            - building (ifcopenshell.entity_instance): The created building entity.
            - storey (ifcopenshell.entity_instance): The created building storey entity.
    """
    
    # Create new empty ifc file using version 2x3 schema
    ifc_file = ifcopenshell.file(schema="IFC2X3")

    # Create owner history
    person = ifc_file.createIfcPerson(GivenName=person_given_name, FamilyName=person_family_name)
    organization = ifc_file.createIfcOrganization(Name=organization_name)
    person_and_org = ifc_file.createIfcPersonAndOrganization(person, organization)
    application = ifcopenshell.api.owner.add_application(ifc_file)
    owner_history = ifc_file.createIfcOwnerHistory(
        OwningUser=person_and_org,
        OwningApplication=application,
        State="READWRITE",
        ChangeAction="NOCHANGE",
        LastModifiedDate=None,
        LastModifyingUser=None,
        CreationDate=int(time.time())
    )

    # Set up project units
    units = ifc_file.createIfcUnitAssignment([
        ifc_file.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE"),
        ifc_file.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE"),
        ifc_file.createIfcSIUnit(None, "VOLUMEUNIT", None, "CUBIC_METRE"),
    ])

    # Create geometric context
    context = ifc_file.createIfcGeometricRepresentationContext(None, "Model", 3, 1.0E-05, 
        ifc_file.createIfcAxis2Placement3D(ifc_file.createIfcCartesianPoint((0., 0., 0.))), None)

    # Create IfcProject
    project = ifc_file.createIfcProject(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="My Project",
        Description="Description of my project",
        ObjectType=None,
        LongName=None,
        Phase=None,
        RepresentationContexts=[context],
        UnitsInContext=units
    )

    # Create IfcSite
    site = ifc_file.createIfcSite(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Site",
        Description="Site Description",
        ObjectPlacement=ifc_file.createIfcLocalPlacement(),
        CompositionType="ELEMENT",
        RefLatitude=None,
        RefLongitude=None
    )

    # Create IfcBuilding
    building = ifc_file.createIfcBuilding(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Building",
        Description="Building Description",
        ObjectPlacement=ifc_file.createIfcLocalPlacement(),
        CompositionType="ELEMENT",
        ElevationOfRefHeight=None,
        ElevationOfTerrain=None
    )

    # Create IfcBuildingStorey
    storey = ifc_file.createIfcBuildingStorey(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Building Storey",
        Description="Building Storey Description",
        ObjectPlacement=ifc_file.createIfcLocalPlacement(),
        CompositionType="ELEMENT",
        Elevation=0.0
    )

    # Create spatial structure relationships
    # IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey
    ifc_file.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Project Container",
        Description=None,
        RelatingObject=project,
        RelatedObjects=[site]
    )

    ifc_file.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Site Container",
        Description=None,
        RelatingObject=site,
        RelatedObjects=[building]
    )

    ifc_file.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Building Container",
        Description=None,
        RelatingObject=building,
        RelatedObjects=[storey]
    )

    # Create geometric context
    # context = ifc_file.createIfcGeometricRepresentationContext(None, "Model", 3, 1.0E-05,
        # ifc_file.createIfcAxis2Placement3D(ifc_file.createIfcCartesianPoint((0., 0., 0.))), None)

    # Set the geometric representation context
    project.RepresentationContexts = [context]

    return ifc_file, context, owner_history, building, storey

# def create_style(ifc_file):
#     style = ifc_file.createIfcSurfaceStyle(
#         "Building Style", "BOTH",
#         [
#             ifc_file.createIfcSurfaceStyleRendering(
#                 ifc_file.createIfcColourRgb("color", 0.6, 0.369, 0.141),
#                 0.0,  # Transparency
#                 None, None, None, None, None, None, 
#                 ifc_file.createIfcNormalizedRatioMeasure(0.5)
#             )
#         ]
#     )
#     return style

# def create_styled_item(ifc_file, shape, style):
#     return ifc_file.createIfcStyledItem(
#         shape,
#         [style],
#         None
#     )

def create_property_set(ifc_file, owner_history, attributes):
    """
    Creates an IFC property set with the given attributes.
    Args:
        ifc_file (ifcopenshell.file): The IFC file object where the property set will be created.
        owner_history (ifcopenshell.entity_instance): The owner history for the property set.
        attributes (dict): A dictionary of attribute names and their corresponding values.
    Returns:
        ifcopenshell.entity_instance: The created IFC property set.
    """

    # Create property set
    property_values = []
    for key, value in attributes.items():
        if value is not None:
            prop = ifc_file.createIfcPropertySingleValue(
                key, None,
                ifc_file.create_entity("IfcLabel", str(value)),
                None
            )
            property_values.append(prop)

    property_set = ifc_file.createIfcPropertySet(
        ifcopenshell.guid.new(),
        owner_history,
        "FKB egenskaper",
        None,
        property_values
    )

    return property_set

def create_building_element_proxy(ifc_file, owner_history, attributes, local_placement, product_shape, storey):
        # Create building element proxy
        element = ifc_file.createIfcBuildingElementProxy(
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name=str(attributes),
            ObjectPlacement=local_placement,
            Representation=product_shape
        )

        # After element creation, create containment relationship
        ifc_file.createIfcRelContainedInSpatialStructure(
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name="Storey Container",
            Description=None,
            RelatingStructure=storey,  # Storey, lowest level in ifc hierarchy
            RelatedElements=[element]
        )

        return element

def assign_property_set(ifc_file, owner_history, element, property_set):
        ifc_file.createIfcRelDefinesByProperties(
            ifcopenshell.guid.new(),
            owner_history,
            None,
            None,
            [element],
            property_set
        )
        return ifc_file

def create_volume_from_point(ifc_file, context, owner_history, storey, geometry, size=10.0, attributes={}):
    """
    Creates a cube in an IFC file from a given point.
    Args:
        ifc_file: The IFC file object where the cube will be created.
        geometry: A point geometry object with x and y attributes.
        size (float, optional): The size of the cube. Defaults to 10.0.
        attributes (dict, optional): A dictionary of attributes to be assigned to the cube. Defaults to {}.
    Returns:
        None
    """
    # Create placement for the cube
    point_coords = (geometry.x, geometry.y, 0.0) # Assuming z=0 for simplicity
    origin = ifc_file.createIfcCartesianPoint(point_coords) # TODO should be possible to set an origin point
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    ref_direction = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    placement = ifc_file.createIfcAxis2Placement3D(origin, axis, ref_direction)
    local_placement = ifc_file.createIfcLocalPlacement(None, placement)

    # Create a cube profile
    half_size = size / 2.0
    profile = ifc_file.createIfcRectangleProfileDef(
        "AREA", None,
        ifc_file.createIfcAxis2Placement2D(ifc_file.createIfcCartesianPoint((0.0, 0.0))),
        size, size
    )

    # Create the extruded solid
    extruded_solid = ifc_file.createIfcExtrudedAreaSolid(
        profile,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0)),
            ifc_file.createIfcDirection((0.0, 0.0, 1.0)),
            ifc_file.createIfcDirection((1.0, 0.0, 0.0))
        ),
        ifc_file.createIfcDirection((0.0, 0.0, 1.0)),
        size
    )

    # Create shape representation
    shape_representation = ifc_file.createIfcShapeRepresentation(
        context, "Body", "SweptSolid", [extruded_solid]
    )
    product_shape = ifc_file.createIfcProductDefinitionShape(
        None, None, [shape_representation]
    )

    # Create property set
    property_set = create_property_set(ifc_file, owner_history, attributes)

    # Create building element proxy
    element = create_building_element_proxy(ifc_file, owner_history, attributes, local_placement, product_shape, storey)
    
    # Assign property set to the element
    ifc_file = assign_property_set(ifc_file, owner_history, element, property_set)

def create_volume_from_polygon(ifc_file, context, owner_history, storey, geometry, depth=0.1, attributes={}):
    """
    Creates a volume from a given polygon geometry and adds it to an IFC file.
    Args:
        ifc_file: The IFC file to which the volume will be added.
        context: The IFC context for the shape representation.
        owner_history: The owner history for the IFC elements.
        storey: The building storey to which the volume belongs.
        geometry: The polygon geometry used to create the volume.
        depth (float, optional): The depth of the extruded volume. Defaults to 0.1.
        attributes (dict, optional): Additional attributes for the building element proxy. Defaults to {}.
    Returns:
        None
    """

    # Create GIS geometry portion
    
    exterior_coords = list(geometry.exterior.coords)
    point_coords = [ifc_file.createIfcCartesianPoint((x, y, 0.)) for x, y in exterior_coords[:-1]]
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    ref_direction = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    origin = ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0))
    placement = ifc_file.createIfcAxis2Placement3D(origin, axis, ref_direction)
    local_placement = ifc_file.createIfcLocalPlacement(None, placement)
    
    # Create swept area solid
    gis_profile = ifc_file.createIfcArbitraryClosedProfileDef(
        "AREA", None,
        ifc_file.createIfcPolyline(point_coords)
    )
    extruded_solid = ifc_file.createIfcExtrudedAreaSolid(
        SweptArea=gis_profile,
        Position=ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint((0.0, 0., 0.0))
        ),
        ExtrudedDirection=axis,
        Depth=depth
    )

    # Create shape representation
    shape_representation = ifc_file.createIfcShapeRepresentation(
        context, "Body", "SweptSolid", [extruded_solid])

    product_shape = ifc_file.createIfcShapeRepresentation(
        ContextOfItems=context, RepresentationIdentifier="Body", RepresentationType="SweptSolid", 
        Items=[shape_representation]
    )

    # Create property set
    property_set = create_property_set(ifc_file, owner_history, attributes)

    # Create building element proxy
    element = create_building_element_proxy(ifc_file, owner_history, attributes, local_placement, product_shape, storey)
    
    # Assign property set to the element
    ifc_file = assign_property_set(ifc_file, owner_history, element, property_set)

def create_volume_from_linestring(ifc_file, context, owner_history, storey, geometry, radius=0.1, attributes={}):
# Get line coordinates
    line_coords = list(geometry.coords)
    line_points = [ifc_file.createIfcCartesianPoint((x, y, 0.)) for x, y in line_coords]
    
    # Create polyline curve
    polyline = ifc_file.createIfcPolyline(line_points)
    # Create placement
    origin = ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0))
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    ref_direction = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    placement = ifc_file.createIfcAxis2Placement3D(origin, axis, ref_direction)
    local_placement = ifc_file.createIfcLocalPlacement(None, placement)

    # Create swept disk solid
    swept_disk = ifc_file.createIfcSweptDiskSolid(
        Directrix=polyline,
        Radius=radius,  
        InnerRadius=None,
        StartParam=0.0,  # Required start parameter
        EndParam=1.0    # Required end parameter
    )
    
    # Create shape representation
    shape_representation = ifc_file.createIfcShapeRepresentation(
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[swept_disk]
    )

    product_shape = ifc_file.createIfcShapeRepresentation(
    ContextOfItems=context, RepresentationIdentifier="Body", RepresentationType="SweptSolid", 
    Items=[shape_representation]
    )

    # Create property set
    property_set = create_property_set(ifc_file, owner_history, attributes)

    # Create building element proxy
    element = create_building_element_proxy(ifc_file, owner_history, attributes, local_placement, product_shape, storey)
    
    # Assign property set to the element
    ifc_file = assign_property_set(ifc_file, owner_history, element, property_set)