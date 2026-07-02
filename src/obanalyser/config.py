class Config:
    def __init__(self):
        # Parameters for build simulation
        self.transition_time = 7.844617526 #time [s] for recoter and transition between layers
        self.length_step = 500 # ref length step [um]
        # Geometrical build setup
        self.build_plate_diameter = 0.1 # diameter of build plate [m]
        self.build_plate_thickness = 0.015 # thickness of build plate [m]
        self.build_plate_density = 7990 # density of the material in the build plate [kg/m3]
        # Parameters for build material
        self.build_material_density = 7990 # density of the material in the build material (solid) [kg/m3]
        self.build_material_heat_capacity = 500 # Specific Heat Capacity of the material in the build material (solid) [J/kg·K]
        self.powder_material_density = 0.5 # relative density of the powder compared to bulk properties [-]
        self.powder_material_heat_capacity = 1 # relative heat capacity of the powder compared to bulk properties [-]
        # Parameters for obp geometry analysis
        self.melt_spot_size_threshold = 510 # spot size threshold to consider for area calculation [um]
        self.melt_watt_threshold = 200.0 # min watt threshold to consider for area calculation [W]
        self.melt_speed_threshold = None # optional max scan speed for melt classification [um/s]
        self.melt_dwell_time_threshold = None # optional min dwell time for melt classification [us]
config = Config()