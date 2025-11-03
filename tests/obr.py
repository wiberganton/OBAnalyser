import obanalyser.obr.analyse_obr as analyse_obr

obr_file = r"C:\Users\antwi87\Documents\Freemelt_heat_model_test\print1\Tungsten_tiles_1\data\mqtt.txt"
obf_file = r"C:\Users\antwi87\Documents\Freemelt_heat_model_test\print1\UKAEAp3_60_tiles_5_objects_8\buildInfo.json"


analyse_obr.analyse_obr(r"C:\Users\antwi87\Documents\Freemelt_heat_model_test\print1\Tungsten_tiles_1\data\mqtt.txt")
analyse_obr.analyse_obr(obr_file,db_path=r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\SeedAMFreemelt2025\training_data\train1\obr_analysis.db",
        temp_sensors=[
            ('freemelt/0/ChamberService/0/BuildTemperature/Name/Sensor1', 'Temperature'),
            ('freemelt/0/PyrometerService/0/BuildTemperature/Name/Pyrometer',"Temperature")
        ])

import obanalyser.analyse_obf_geometry as analyse_obf_geometry
geometry_info = analyse_obf_geometry.analyse_obf_geometry(obf_file)
geometry_info.to_json_file(r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\SeedAMFreemelt2025\training_data\train1\geometry_info.json")

import obanalyser.analyse_build as analyse_build
build = analyse_build.analyse_build(obf_file)
build.to_json(r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\SeedAMFreemelt2025\training_data\train1\build_info.json")