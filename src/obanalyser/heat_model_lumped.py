import math

from obanalyser.config import config

def predict_losses(T_i, t):
    """
    input:  T_i is the inital temp (Kelvin)
            t is the duration (s)
    return: loss energy (J)
    """
    # radiation loss
    sigma = 5.67e-8  # Stefan-Boltzmann constant
    epsilon = config.radiation_emissivity    # example emissivity       
    A_surface = (config.build_plate_diameter/2)**2*math.pi #area in m²
    T_env = config.environment_temp_wall + 273.15  # environment temp in K
    Q_rad = epsilon * sigma * A_surface * (T_i**4 - T_env**4) * t
    
    # conducation loss
    delta_T = T_i - config.environment_temp_piston
    Q_con = config.thermal_conductivity*config.conduction_area_lumped*delta_T/config.conduction_length_lumped

    return Q_rad #+ Q_con

def layer_temp(layer_info, start_temp, thermal_masses):
    """
    inputs: layer_info is a data_classes.LayerInfo object
            start_temp is the intial temperature in Kelvin
            thermal_masses is a list of thermal masses for each layer
            layer is at which layer we want to evaluate
    return: List with data points [time (s), temp (K)] starting from t=0
    """
    layer = layer_info.layer_index
    data = [[0, start_temp]] # List with data points [time (s), temp (K)]
    # recoate temp
    temp_change = predict_temp_change(thermal_masses[layer], -predict_losses(start_temp, layer_info.recoate_time))
    temp = start_temp + temp_change
    t = layer_info.recoate_time
    data.append([t, temp])
    # loop for files
    for file in layer_info.files:
        for _ in range(file.nmb_repetitions):
            losses = predict_losses(temp, file.time)
            energy_input = file.energy*config.beam_efficiency
            temp_change = predict_temp_change(thermal_masses[layer], energy_input-losses)
            temp += temp_change
            t += file.time
            data.append([t, temp])
    return data

def predict_temp_change(layer_mass, delta_energy):
    return delta_energy/layer_mass


def build_temp(build_info, thermal_masses, up_to_layer=None): 
    """
    inputs: build_info is a data_classes.BuildInfo object
            thermal_masses is a list of thermal masses for each layer
    return: List with data points [time (s), temp (K)] starting from t=0
    """
        
    start_temp = build_info.start_temp + 273.15
    data = [[0, start_temp]] # List with data points [time (s), temp (K)]
    count = 0
    for layer_info in build_info.layers:
        layer_data = layer_temp(layer_info, data[-1][1], thermal_masses)
        for row in layer_data:
            row[0] += data[-1][0]
        data.extend(layer_data[1:])
        if up_to_layer is not None and count >= up_to_layer:
            #print("build_info ", len(layer_info.files))
            break
        count += 1
    return data
    

