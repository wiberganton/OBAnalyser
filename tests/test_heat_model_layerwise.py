import unittest

import numpy as np
import matplotlib.pyplot as plt
import py3mf_slicer.load
import py3mf_slicer.slice

import obanalyser.data_classes as data_classes
import obanalyser.heat_model_layerwise as heat_model_layerwise
from obanalyser import get_3mf_data

class TestMain(unittest.TestCase):
    def test_main(self):

        build_info = data_classes.BuildInfo.from_json(r"tests\input\thermal_models\build_info.json")
        build_areas = [4*10*10, 4*10*10]
        
        history = heat_model_layerwise.heat_model_layerwise(build_info, build_areas)
        """
        plt.figure(figsize=(10, 6))
        for col in history.columns:
            if col != 'time':
                plt.plot(history['time'], history[col], label=col)

        plt.xlabel("Time [s]")
        plt.ylabel("Temperature [C]")
        plt.title("Heat Transfer in Powder Bed Fusion System")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        """
if __name__ == "__main__":
    unittest.main()