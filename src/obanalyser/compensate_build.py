import json

import src.obanalyser.analyse_build as analyse_build
import src.obanalyser.analyse_obp as analyse_obp
import src.obanalyser.heat_model_lumped as heat_model_lumped

def lumped_heat_model_compensation(build_info_path, thermal_mass, obp_path_heating, obp_path_cooling):
    """
    input:  build_info_path is a string with path to the build info in json format
            thermal mass is a list with thermal masses for each layer [mass_layer1, mass_layer2, ..]
            obp_path_heating is a string with a link to the file which is used to add additional energy
            obp_path_cooling is a string with a link to the file which is used to cool of the build
    return: new_build a json format with compensated heat_balance
    """
    temp_tolerance = 3
    build = analyse_build.analyse_build(build_info_path) #data_classes.BuildInfo
    start_temp = build.start_temp + 273.15 #degrees Kelvin
    heating_info = analyse_obp.analyse_obp_file((obp_path_heating,1)) #data_classes.FileStats
    cooling_info = analyse_obp.analyse_obp_file((obp_path_cooling,1)) #data_classes.FileStats
    print("heating_info ", heating_info)
    with open(build_info_path) as f:
        new_build = json.load(f)
    for i, layer in enumerate(build.layers):
        layer_temp = heat_model_lumped.layer_temp(layer, start_temp, thermal_mass)[-1][1]
        print("layer_temp ", layer_temp)
        print("start_temp ", start_temp)
        if layer_temp < start_temp:
            ii = 0
            while layer_temp < start_temp-temp_tolerance:
                #print("1")
                #print("layer_temp ", layer_temp)
                #print("start_temp-temp_tolerance ", start_temp-temp_tolerance)
                layer.files.append(heating_info)
                print("layer ", layer)
                layer_temp = heat_model_lumped.layer_temp(layer, start_temp, thermal_mass)[-1][1]
                ii += 1
            new_build = add_heat_balance(new_build, i, obp_path_heating, ii)
        elif layer_temp > start_temp:
            ii = 0
            while layer_temp > start_temp+temp_tolerance:
                print("2")
                print("layer_temp ", layer_temp)
                print("start_temp-temp_tolerance ", start_temp-temp_tolerance)
                layer.files.append(cooling_info)
                layer_temp = heat_model_lumped.layer_temp(layer, start_temp, thermal_mass)[-1][1]
                ii += 1
            new_build = add_heat_balance(new_build, i, obp_path_cooling, ii)
    return new_build

def add_heat_balance(build, layer_index, file_path, repetitions):
    # Get the layers list
    layers = build["layers"]
    # Ensure the layer index is valid
    if layer_index >= len(layers):
        raise IndexError(f"Layer index {layer_index} is out of range.")
    layer = layers[layer_index]
    # Create the heatBalance entry
    new_entry = {
        "file": file_path,
        "repetitions": repetitions
    }
    # Add or update heatBalance
    if "heatBalance" in layer:
        layer["heatBalance"].append(new_entry)
    else:
        layer["heatBalance"] = [new_entry]
    return build