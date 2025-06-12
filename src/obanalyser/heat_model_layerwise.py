import math
import pandas as pd
import numpy as np

import obanalyser.data_classes as data_classes

config_layer_heat = {
    # Overall properties
    "build_radius": 0.05,  # m
    "emissivity": 0.75,
    "beam_efficiency": 1.0,
    "sigma": 5.67e-8,  # W/m^2/K^4

    # Build material
    "solid_conductivity": 14,  # W/m/K
    "solid_density": 7990,     # kg/m^3
    "powder_conductivity": 2,  # W/m/K
    "powder_cp": 500,          # J/kg/K
    "powder_density": 7990 * 0.5,  # kg/m^3

    # Build plate
    "plate_conductivity": 14,  # W/m/K
    "plate_thickness": 0.015,  # m
    "plate_cp": 500,           # J/kg/K
    "plate_density": 7990,     # kg/m^3
    "plate_num_layers": 10,

    # Powder under plate
    "beneath_plate_powder_conductivity": 1,
    "beneath_plate_powder_thickness": 0.05,
    "beneath_plate_powder_cp": 500,
    "beneath_plate_powder_density": 7990 * 0.3,

    # Cylinder
    "cylinder_thickness": 0.003,
    "cylinder_conductivity": 14,
    "cylinder_length": 0.2,
    "cylinder_cp": 500,
    "cylinder_density": 7990,

    # Piston
    "piston_conductivity": 14,
    "piston_cp": 500,
    "piston_density": 7990,
    "piston_plate_thickness": 0.0001,

    # Constants
    "time_step": 0.001,

    # Temperatures
    "T_wall": 100 + 273.15,
    "T_powder_feed": 700 + 273.15,
    "T_piston_plate": 500 + 273.15,
    "T_beneath_plate": 800 + 273.15,
}

# Constants
pi = math.pi
build_area_total = pi * config_layer_heat["build_radius"]**2
build_circumference = 2 * pi * config_layer_heat["build_radius"]

def heat_model_layerwise(build_info, build_areas):
    """
    Simulate the heat transfer in a powder bed fusion system layerwise.
    
    Parameters:
    None
    Returns:
    pandas dataframe: DataFrame containing the temperature history of the system.
    """
    # Temperatures which will be modified
    layer_data_list = [] #Temp (Kelvin), thickness (m), conductivity (W/m/K), mass term (kg*m^2/s^2)
    # Add piston plate layer
    layer_data_list.append([
        config_layer_heat["T_piston_plate"],
        config_layer_heat["piston_plate_thickness"],
        config_layer_heat["piston_conductivity"],
        config_layer_heat["piston_plate_thickness"] * build_area_total * config_layer_heat["piston_density"] * config_layer_heat["piston_cp"]
    ])
    # Add layers beneath the piston plate
    layer_data_list.append([
        config_layer_heat["T_beneath_plate"],
        config_layer_heat["beneath_plate_powder_thickness"],
        config_layer_heat["beneath_plate_powder_conductivity"],
        config_layer_heat["beneath_plate_powder_thickness"] * build_area_total * config_layer_heat["beneath_plate_powder_density"] * config_layer_heat["beneath_plate_powder_cp"]
    ])
    # Add plate layers
    plate_thickness_per_layer = config_layer_heat["plate_thickness"] / config_layer_heat["plate_num_layers"]
    plate_mass_term = plate_thickness_per_layer * build_area_total * config_layer_heat["plate_density"] * config_layer_heat["plate_cp"]
    for _ in range(config_layer_heat["plate_num_layers"]):
        layer_data_list.append([
            build_info.start_temp + 273.15,
            plate_thickness_per_layer,
            config_layer_heat["plate_conductivity"],
            plate_mass_term
        ])
    numb_non_layers = len(layer_data_list)
    log_interval = 1.0  # seconds
    last_log_time = 0.0
    # Add build layers
    for layer in build_info.layers:
        height_m = layer.layer_height / 1000
        solid_fraction = build_areas[layer.layer_index] / (build_area_total * 1000000)
        powder_fraction = 1.0 - solid_fraction
        conductivity = solid_fraction * config_layer_heat["solid_conductivity"] + powder_fraction * config_layer_heat["powder_conductivity"]
        density = solid_fraction * config_layer_heat["solid_density"] + powder_fraction * config_layer_heat["powder_density"]
        mass_term = height_m * build_area_total * density * config_layer_heat["powder_cp"]
        layer_data_list.append([
            config_layer_heat["T_powder_feed"],
            height_m,
            conductivity,
            mass_term
        ])
    # Convert to NumPy array at the end
    layer_data = np.array(layer_data_list)
    n = len(layer_data)
    losses = np.zeros(n)
    # Cylinder data
    T_cylinder = np.array([500 + 273.15, 200 + 273.15]) #K, temperature of the cylinder
    r_outer = config_layer_heat["build_radius"] + config_layer_heat["cylinder_thickness"]
    r_inner = config_layer_heat["build_radius"]
    volume = pi * config_layer_heat["cylinder_length"] * (r_outer**2 - r_inner**2)
    thermal_mass_cylinder = volume * config_layer_heat["cylinder_density"] * config_layer_heat["cylinder_cp"]
    t = 0 # time in seconds - Start time
    log_temp = []
    log_temp.append({
        'time': t,
        'top': layer_data[-1,0],
        'plate_under': layer_data[numb_non_layers-config_layer_heat["plate_num_layers"],0],
        'cylinder': T_cylinder[1]
    })
    for layer in build_info.layers:
        recoatefile = data_classes.FileStats(
            nmb_repetitions=1,  # number of repetitions for the recoate file
            time=layer.recoate_time,  # time for the recoate file in seconds
            energy=0,  # energy input for the recoate file in Joules
            nmb_spots=0,  # number of spots for the recoate file
            line_length=0  # line length for the recoate file in meters
        )
        layer.files.insert(0, recoatefile)  # Add recoate file to the layer files
       
        
        for file in layer.files:
            nmb_repetitions= file.nmb_repetitions # number of repetitions for the file
            file_time= file.time # time for the file in seconds
            energy= file.energy * config_layer_heat["beam_efficiency"] # energy input for the file in Joules
            duration = file_time*nmb_repetitions # seconds, total duration of the simulation
            n_steps = int(np.ceil(duration / config_layer_heat["time_step"]))
            T = layer_data[:numb_non_layers+layer.layer_index+1, 0]
            d = layer_data[:numb_non_layers+layer.layer_index+1, 1]
            k = layer_data[:numb_non_layers+layer.layer_index+1, 2]
            m = layer_data[:numb_non_layers+layer.layer_index+1, 3]
            
            for _ in range(n_steps):
                # Calculation of losses
                conduction_layer = k[:-1] * build_area_total * (T[:-1] - T[1:]) / d[:-1] # Conduction between layers (n-1 values)
                conduction_cylinder = k * build_circumference * d * (T - T_cylinder[0]) / (config_layer_heat["build_radius"] / 2) *0.5    # Conduction to cylinder wall (n values)
                losses = np.zeros_like(T)   # Initialize losses array
                losses[1:-1] = -conduction_layer[1:] + conduction_layer[:-1] - conduction_cylinder[1:-1]   # Interior layers (1 to n-2)
                losses[0] = -conduction_layer[0] - conduction_cylinder[0]   # First layer (i=0)
                losses[-1] = conduction_layer[-1] - conduction_cylinder[-1]
                losses[-1] -= - energy/file_time + config_layer_heat["emissivity"] * config_layer_heat["sigma"] * (T[-1]**4 - config_layer_heat["T_wall"]**4) * build_area_total*0.5
                #losses[0] -= emissivity * sigma * (T[0]**4 - T_wall**4) * build_area_total
                within_cylinder_conduction = (2 * pi * config_layer_heat["cylinder_length"] * config_layer_heat["cylinder_conductivity"] * (T_cylinder[0] - T_cylinder[1])) / math.log((config_layer_heat["build_radius"]+config_layer_heat["cylinder_thickness"]) / config_layer_heat["build_radius"])  # Conduction within cylinder wall
                cylinder_radiation = 0.5 * config_layer_heat["emissivity"] * config_layer_heat["sigma"] * (T_cylinder[1]**4 - config_layer_heat["T_wall"]**4) * (2 * pi * config_layer_heat["cylinder_length"] * (config_layer_heat["build_radius"] + config_layer_heat["cylinder_thickness"]))  # Radiation from cylinder wall
                cylinder_losses = np.array([
                    np.sum(conduction_cylinder) - within_cylinder_conduction,
                    within_cylinder_conduction - cylinder_radiation
                ])
                
                # Update temperatures
                delta_T_layer = losses*config_layer_heat["time_step"] / m # Calculate temperature change for each layer
                T += delta_T_layer
                delta_T_cylinder = cylinder_losses * config_layer_heat["time_step"] / thermal_mass_cylinder/2
                T_cylinder += delta_T_cylinder
                if any(math.isnan(x) for x in T):
                    return None

                # Log results
                t += config_layer_heat["time_step"]
                if t - last_log_time >= log_interval:
                    log_temp.append({
                        'time': t,
                        'top': T[-1],
                        'plate_under': layer_data[numb_non_layers - config_layer_heat["plate_num_layers"], 0],
                        'cylinder': T_cylinder[1]
                    })
                    last_log_time = t
            
            layer_data[:len(T),0] = T
            log_temp.append({
                'time': t,
                'top': T[-1],
                'plate_under': layer_data[numb_non_layers-config_layer_heat["plate_num_layers"],0],
                'cylinder': T_cylinder[1]
            })
        print("Done layer: ", layer.layer_index)
    df = pd.DataFrame(log_temp)
    columns_to_exclude = ['time']
    columns_to_modify = df.columns.difference(columns_to_exclude)
    df[columns_to_modify] = df[columns_to_modify] - 273.15
    return df

