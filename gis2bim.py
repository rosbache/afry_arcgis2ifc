import geopandas as gpd
import ifcopenshell
import ifcopenshell.api
import afry_bimshape_lib
import time
from datetime import datetime

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

# Read the shapefile with point geometry
shapefile_path = 'KulturminneBygning_PUNKT.shp'
gdf = gpd.read_file(shapefile_path)



def create_cube_from_point(ifc_file, geometry, size=10.0, attributes={}):
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
    property_set = afry_bimshape_lib.create_property_set(ifc_file, owner_history, attributes)

    # Create building element proxy
    element = afry_bimshape_lib.create_building_element_proxy(ifc_file, owner_history, attributes, local_placement, product_shape, storey)
    
    # Assign property set to the element
    ifc_file = afry_bimshape_lib.assign_property_set(ifc_file, owner_history, element, property_set)

### MAIN CODE ###
idx = 0
# Iterate over each point in the GeoDataFrame and create a cube at its location
for idx, row in gdf.iterrows():
    # x, y = row.geometry.x, row.geometry.y
    geometry = row.geometry
    attributes = row.drop('geometry').to_dict()
    # print (geometry, attributes)
    create_cube_from_point(ifc_file, geometry, attributes=attributes)  

    idx += 1

    # if idx ==1: 
        # break3562

# Save the IFC file
ifc_file.write('output4.ifc')

print("IFC file with cubes created successfully.")