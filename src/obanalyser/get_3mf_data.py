import math 

import py3mf_slicer
import py3mf_slicer.get_items

from src.config import config

def analyse_3mf(model):
    layer_height = py3mf_slicer.get_items.get_layer_height(model)
    numb_mesh_objects = py3mf_slicer.get_items.get_number_of_mesh_objects(model)
    part_areas, total_areas = get_3mf_areas(model)
    plate_radius = config.build_plate_diameter/2
    plate_thickness = config.build_plate_thickness
    plate_mass = plate_radius**2*math.pi*plate_thickness*config.build_plate_density
    powder_area = (config.build_plate_diameter/2)**2*math.pi
    density_part = config.build_material_density
    density_powder = density_part*config.powder_material_density
    c_part = config.build_material_heat_capacity
    c_plate = c_part*config.powder_material_heat_capacity
    current_mass = plate_mass*c_plate
    thermal_mass = []
    for area in total_areas:
        layer_part_area = area/1000000
        layer_powder_area = powder_area-layer_part_area
        current_mass = current_mass + layer_part_area*layer_height/1000*c_part*density_part + layer_powder_area*layer_height/1000*c_part*density_powder+c_part*1.08
        thermal_mass.append(current_mass)
    return thermal_mass


def get_3mf_areas(model):
    nmb_layers = py3mf_slicer.get_items.get_number_layers(model)
    max_layer = max(nmb_layers)
    part_areas = []
    total_areas = []
    for layer in range(max_layer):
        layer_areas = []
        shapely_slice = py3mf_slicer.get_items.get_shapely_slice(model, layer)
        for shape in shapely_slice:
            if shape is not None:
                layer_areas.append(shape.area)
            else:
                layer_areas.append(0)
        part_areas.append(layer_areas)
        total_areas.append(sum(layer_areas))
    return (part_areas, total_areas)

