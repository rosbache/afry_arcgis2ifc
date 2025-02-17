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

def create_styled_item(ifc_file, shape, style):
    return ifc_file.createIfcStyledItem(
        shape,
        [style],
        None
    )
