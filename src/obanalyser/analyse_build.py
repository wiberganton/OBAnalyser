import json
import yaml
import os

from src.obanalyser import get_build_order
from src.obanalyser import analyse_obp
from src.obanalyser.data_classes import LayerInfo, BuildInfo

def analyse_build(build_file_path):
    """
    Reads an build_info file from an obf folder or yaml file with build info
    Returns an analyse_data_classes.BuildInfo object with basic information about the build
    """
    build_sequence = get_build_order.get_layer_execution_sequence(build_file_path)
    layer_info = get_build_order.get_other_layer_info(build_file_path)
    layers = []
    
    for i in range(len(layer_info)):
        obp_info = analyse_obp.analyse_obp_files(build_sequence[i])
        layer_info_object = LayerInfo(
            layer_index = i,
            layer_height = layer_info[i][1],
            recoate_time = layer_info[i][0],
            files = obp_info
        )
        layers.append(layer_info_object)
    
    if build_file_path.endswith(".json"):
        with open(build_file_path) as f:
            data = json.load(f)
        #print("data ", data)
        start_temp = float(data["startHeat"]["targetTemperature"])
    elif build_file_path.endswith((".yaml", ".yml")):
        with open(build_file_path, 'r') as f:
            data = yaml.safe_load(f)
        start_temp = float(data["build"]["start_heat"]["target_temperature"])
    else:
        print("Not supported file type in build input")
    
    build_info = BuildInfo(
        start_temp = start_temp,
        layers = layers
    )
    
    return build_info