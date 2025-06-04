import math

class Config:
    def __init__(self):
        # Parameters for build simulation
        self.transition_time = 8.5 #time [s] for recoter and transition between layers
        self.time_step = 50 # ref number for time step [us]
        self.length_step = 500 # ref length step [um]
        # Geometrical build setup
        self.build_plate_diameter = 0.1 # diameter of build plate [m]
        self.build_plate_thickness = 0.015 # thickness of build plate [m]
        self.build_plate_density = 7990 # density of the material in the build plate [kg/m3]
        # Heat parameters
        self.environment_temp_wall = 100 # temp of the wall in the build chamber [C]
        self.environment_temp_piston = 30 # temp of the wall in the build chamber [C]
        self.radiation_emissivity = 0.8 # emissitivity constant for the radiation
        self.thermal_conductivity = 16.0 # W/m·K
        self.conduction_area_lumped = 0.005 # Area of the conductive material (m2)
        self.conduction_length_lumped = 0.05 # Height which the conductivity happens (m)
        # Parameters for build material
        self.build_material_density = 7990 # density of the material in the build material (solid) [kg/m3]
        self.build_material_heat_capacity = 500 # Specific Heat Capacity of the material in the build material (solid) [J/kg·K]
        self.powder_material_density = 0.5 # relative density of the powder compared to bulk properties [-]
        self.powder_material_heat_capacity = 1 # relative heat capacity of the powder compared to bulk properties [-]
        # Parameters for heat simulation
        self.beam_efficiency = 0.95 # Efficiency of the beam

config = Config()