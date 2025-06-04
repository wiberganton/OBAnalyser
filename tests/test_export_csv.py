import unittest
import csv

import obanalyser.extract_obp_elements as extract_obp_elements
import obanalyser.plotters.plot_csv as plot_csv

class TestMain(unittest.TestCase):
    def test_main(self):
        path1 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\TEEM02_R_Plate.obp"
        path2 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\LowCurrentPreheat_PT_V_left_half.obp"
        path3 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\TEEM02_L_Powder.obp"

        paths = [[(path1, 1), ("", 8), (path2, 10), (path3, 1)]]
        out_file = r"tests\output\test_export_csv.csv"
        extract_obp_elements.extract_multiple_files(paths, out_file, t0=0, plot_info=False)
        
if __name__ == "__main__":
    unittest.main()