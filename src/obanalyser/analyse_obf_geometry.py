import math

from obanalyser.data_classes import GeometryLayerInfo, GeometryInfo
import obanalyser.get_build_order as get_build_order
import obanalyser.analyse_obp_geometry as analyse_obp_geometry
from obanalyser.config import config

def analyse_obf_geometry(build_json):
    """
    Reads an build_json inside an obf folder and returns a dictionary with the geometry information
    """
    (build_sequence, start_heat_path)= get_build_order.get_layer_execution_sequence(build_json)
    layer_info = get_build_order.get_other_layer_info(build_json)
    layers = []
    
    for i in range(len(layer_info)):
        #obp_info = analyse_obp.analyse_obp_files(build_sequence[i])
        total_area = analyse_obp_geometry.analyse_obp_files_area(build_sequence[i])*0.000001 # in mm2
        layer_info_object = GeometryLayerInfo(
            layer_index = i,
            melt_area_mm2 = total_area,
            melt_portion = total_area/((config.build_plate_diameter/2)**2*math.pi*1000000)
        )
        layers.append(layer_info_object)

    geometry_info = GeometryInfo(
        layers = layers 
    )
    return geometry_info