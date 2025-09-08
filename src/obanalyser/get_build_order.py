import json
import yaml
import os

from obanalyser.config import config

def get_layer_execution_sequence(path):
    """
    Reads an build_info file from an obf folder or yaml file with build info
    Returns the sequense of which obp files should be run
    """
    if path.endswith(".json"):
        return get_layer_execution_sequence_obf(path)
    elif path.endswith((".yaml", ".yml")):
        return get_layer_execution_sequence_boss(path)
    else:
        print("Not supported file type in build input")
        return None

def get_layer_execution_sequence_obf(path):
    with open(path) as f:
        data = json.load(f)
    # Extract the base directory from the input path
    base_dir = os.path.dirname(path)
    layer_defaults = data.get("layerDefaults", {})
    default_spatter_safe = layer_defaults.get("spatterSafe", [])
    default_jump_safe = layer_defaults.get("jumpSafe", [])
    default_heat_balance = layer_defaults.get("heatBalance", [])
    sequence_per_layer = []

    for layer in data.get("layers", []):
        layer_sequence = []

        jump_safe_ops = layer.get("jumpSafe", default_jump_safe)
        spatter_safe_ops = layer.get("spatterSafe", default_spatter_safe)
        melt_ops = layer.get("melt", [])
        heat_balance_ops = layer.get("heatBalance", default_heat_balance)

        for op in jump_safe_ops:
            full_path = os.path.join(base_dir, op["file"])
            layer_sequence.append((full_path, op["repetitions"]))

        for op in spatter_safe_ops:
            full_path = os.path.join(base_dir, op["file"])
            layer_sequence.append((full_path, op["repetitions"]))

        for op in melt_ops:
            full_path = os.path.join(base_dir, op["file"])
            layer_sequence.append((full_path, op["repetitions"]))

        for op in heat_balance_ops:
            full_path = os.path.join(base_dir, op["file"])
            layer_sequence.append((full_path, op["repetitions"]))

        sequence_per_layer.append(layer_sequence)

        start_heat_full_path = os.path.join(base_dir, data["startHeat"]["file"])
        start_heat_info = (start_heat_full_path, 1)

    return (sequence_per_layer, start_heat_info)

def get_layer_execution_sequence_boss(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    build_data = data.get('build', {})
    preheat = build_data['preheat']
    postheat = build_data['postheat']
    layer_sets = build_data['build']['files']
    total_layers = build_data['build']['layers']

    preheat_file = preheat['file']
    preheat_reps = preheat['repetitions']
    postheat_file = postheat['file']
    postheat_reps = postheat['repetitions']

    sequence_per_layer = []

    for i in range(total_layers):
        current_layer_set = layer_sets[i % len(layer_sets)]  # repeat layer sets as needed
        layer_sequence = []

        # Preheat (maps to spatterSafe)
        layer_sequence.append((preheat_file, preheat_reps))

        # Melt files (each file in the current set, 1 repetition each)
        for melt_file in current_layer_set:
            layer_sequence.append((melt_file, 1))

        # Postheat (maps to heatBalance)
        layer_sequence.append((postheat_file, postheat_reps))

        sequence_per_layer.append(layer_sequence)
    
    start_heat_info = (data["build"]["start_heat"]["file"], 1)
    
    return (sequence_per_layer, start_heat_info)


def get_other_layer_info(path):
    if path.endswith(".json"):
        return get_other_layer_info_obf(path)
    elif path.endswith((".yaml", ".yml")):
        return get_other_layer_info_yaml(path)
    else:
        print("Not supported file type in build input")
        return None

def get_other_layer_info_obf(path):
    with open(path) as f:
        data = json.load(f)
    layer_defaults = data.get("layerDefaults", {}).get("layerFeed", [])
    layer_data = []
    for layer in data.get("layers", []):
        layerfeed = layer.get("layerFeed", layer_defaults)
        layer_data.append((calc_layerfeed(layerfeed), -float(layerfeed["buildPistonDistance"])))
    return layer_data

def get_other_layer_info_yaml(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    layerfeed = data.get('build', {})['layerfeed']
    layer_height = -float(layerfeed["build_piston_distance"])
    layer_time = calc_layerfeed(layerfeed)
    nmb_of_layers = int(data['build']['build']['layers'])
    return [(layer_time, layer_height)]*nmb_of_layers

def calc_layerfeed(layerfeed):
    feed_time = config.transition_time
    advance_speed = layerfeed.get("recoater_advance_speed") or layerfeed.get("recoaterAdvanceSpeed")
    retract_speed = layerfeed.get("recoater_retract_speed") or layerfeed.get("recoaterRetractSpeed")
    speed = (advance_speed + retract_speed)/200
    if "recoater_full_repeats" in layerfeed:
        full_repeats = layerfeed["recoater_full_repeats"]
    elif "recoaterFullRepeats" in layerfeed:
        full_repeats = layerfeed["recoaterFullRepeats"]
    else:
        full_repeats = None  # or a default value
    if "recoater_dwell_time" in layerfeed:
        dwell_time = layerfeed["recoater_dwell_time"]
    elif "recoaterDwellTime" in layerfeed:
        dwell_time = layerfeed["recoaterDwellTime"]
    else:
        dwell_time = None  # or a default value
    new_feed_time = (full_repeats+1)*speed*feed_time+dwell_time
    return new_feed_time