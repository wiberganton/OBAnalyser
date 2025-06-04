import unittest
import py3mf_slicer.load
import py3mf_slicer.slice
import json

from obanalyser import get_3mf_data
import obanalyser.analyse_build as analyse_build
import obanalyser.heat_model_lumped as heat_model_lumped
from obanalyser.plotters.plot_temp import plot_lump_temp
import obanalyser.data_classes as data_classes


class TestMain(unittest.TestCase):
    def test_main(self):
        build = data_classes.BuildInfo.from_json(r"tests\input\screw_test\build_info.json")
        with open(r"tests\input\screw_test\thermal_mass.json", 'r') as f:
            thermal_mass = json.load(f)
        # thermal model
        data = heat_model_lumped.build_temp(build, thermal_mass)
        #plot_lump_temp(data)
        print("test_heat_model works")
        
if __name__ == "__main__":
    unittest.main()