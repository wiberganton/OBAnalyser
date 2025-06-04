import unittest
import py3mf_slicer.load
import py3mf_slicer.slice

from obanalyser import get_3mf_data


class TestMain(unittest.TestCase):
    def test_main(self):
        geometries = [
            r'tests\input\geometries\test_geometry1.stl', 
            r'tests\input\geometries\test_geometry2.stl', 
            r'tests\input\geometries\test_geometry3.stl']
        model = py3mf_slicer.load.load_files(geometries)
        self.assertIsNotNone(model, "Model failed to load")
        # Step 2: Slice the model
        sliced_model = py3mf_slicer.slice.slice_model(model, 1)
        self.assertIsNotNone(sliced_model, "sliced 3mf model failed")
        thermal_mass = get_3mf_data.analyse_3mf(sliced_model)
        self.assertIsNotNone(thermal_mass, "obp analyse failed")
        print("test_3mf works!")

if __name__ == "__main__":
    unittest.main()