import json
import copy
from pathlib import Path

import obanalyser.analyse_build as analyse_build
import obanalyser.analyse_obp as analyse_obp
import obanalyser.heat_model_lumped as heat_model_lumped
import obanalyser.plotters.plot_temp as plot_temp

def lumped_heat_model_compensation(build_info_path, thermal_mass, obp_path_heating, obp_path_cooling):
    """
    input:  build_info_path is a string with path to the build info in json format
            thermal mass is a list with thermal masses for each layer [mass_layer1, mass_layer2, ..]
            obp_path_heating is a string with a link to the file which is used to add additional energy
            obp_path_cooling is a string with a link to the file which is used to cool of the build
    return: new_build a json format with compensated heat_balance
    """
    # Get correct paths for the new build file
    base_dir = Path(build_info_path).parent
    obp_path_heating_rel = str(Path(obp_path_heating).relative_to(base_dir))
    obp_path_cooling_rel = str(Path(obp_path_cooling).relative_to(base_dir))

    temp_tolerance = 3 # degrees C
    build = analyse_build.analyse_build(build_info_path) #data_classes.BuildInfo
    start_temp = build.start_temp + 273.15 #degrees Kelvin
    heating_info = analyse_obp.analyse_obp_file((obp_path_heating,1)) #data_classes.FileStats
    cooling_info = analyse_obp.analyse_obp_file((obp_path_cooling,1)) #data_classes.FileStats
    with open(build_info_path) as f:
        new_build = json.load(f)
    for i, layer in enumerate(build.layers):
        temp = heat_model_lumped.build_temp(build, thermal_mass, up_to_layer=i)
        layer_temp = temp[-1][1]
        if layer_temp < start_temp-temp_tolerance:
            ii = 0
            while layer_temp < start_temp-temp_tolerance:
                build.layers[i].files.append(copy.deepcopy(heating_info))
                temp = heat_model_lumped.build_temp(build, thermal_mass, up_to_layer=i)
                layer_temp = temp[-1][1]
                ii += 1
            new_build = add_heat_balance(new_build, i, obp_path_heating_rel, ii)
        elif layer_temp > start_temp+temp_tolerance:
            ii = 0
            while layer_temp > start_temp+temp_tolerance:
                build.layers[i].files.append(copy.deepcopy(cooling_info))
                temp = heat_model_lumped.build_temp(build, thermal_mass, up_to_layer=i)
                layer_temp = temp[-1][1]
                ii += 1
            new_build = add_heat_balance(new_build, i, obp_path_cooling_rel, ii)
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