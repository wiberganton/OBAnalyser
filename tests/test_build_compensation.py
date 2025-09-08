import unittest
import py3mf_slicer.load
import py3mf_slicer.slice
import json

import obanalyser.analyse_build as analyse_build
import obanalyser.analyse_obp as analyse_obp
import obanalyser.get_3mf_data as get_3mf_data
import obanalyser.compensate_build as compensate_build
import obanalyser.heat_model_lumped as heat_model_lumped
from obanalyser.plotters.plot_temp import plot_lump_temp


class TestMain(unittest.TestCase):
    def test_main(self):
        # prepare 3mf file
        geometries = [
            r"tests\input\cubes_test\geometry\part1.stl", 
            r"tests\input\cubes_test\geometry\part2.stl",  
            r"tests\input\cubes_test\geometry\part3.stl", 
            r"tests\input\cubes_test\geometry\part4.stl"]
        model = py3mf_slicer.load.load_files(geometries)
        sliced_model = py3mf_slicer.slice.slice_model(model, 0.1)
        thermal_mass = get_3mf_data.analyse_3mf(sliced_model)

        # build info
        path = r"tests/input/cubes_test/buildInfo.json"
        output_path = r"tests/input/cubes_test/newbuildInfo.json"
        build = analyse_build.analyse_build(path)
        
        data = heat_model_lumped.build_temp(build, thermal_mass)
        
        print("not compensated data: ")
        plot_lump_temp(data)
        
        # build compensation
        obp_path_heating = r"tests/input/cubes_test/obp/heat_compensation.obp"
        obp_path_cooling = r"tests/input/cubes_test/obp/PostMelt_IdleScan.obp"

        new_build = compensate_build.lumped_heat_model_compensation(path, thermal_mass, obp_path_heating, obp_path_cooling)
        with open(output_path, "w") as json_file:
            json.dump(new_build, json_file, indent=4)
        new_build_object = analyse_build.analyse_build(output_path)
        data = heat_model_lumped.build_temp(new_build_object, thermal_mass)
        print("compensated data: ")
        plot_lump_temp(data)
if __name__ == "__main__":
    unittest.main()



