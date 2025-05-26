import unittest
import csv

import src.obanalyser.extract_obp_elements as extract_obp_elements
import src.obanalyser.plotters.plot_csv as plot_csv

class TestMain(unittest.TestCase):
    def test_main(self):
        path1 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\TEEM02_R_Plate.obp"
        path2 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\LowCurrentPreheat_PT_V_left_half.obp"
        path3 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\TEEM02_R_Plate.obp"

        out_path1 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\out1.csv"
        out_path2 = r"C:\Users\antwi87\Downloads\OneDrive_1_23-05-2025\out2.csv"
        element_data, t = extract_obp_elements.extract_from_obp_file(path1, start_time = 0)
        element_data.extend(extract_obp_elements.get_delay_elements(8, t0=t))
        t += 8
        for i in range(10):
            element_data_local, t_local = extract_obp_elements.extract_from_obp_file(path2, start_time = t)
            element_data.extend(element_data_local)
            t = t_local
        element_data_local, t_local = extract_obp_elements.extract_from_obp_file(path3, start_time = t)
        element_data.extend(element_data_local)
        
        with open(out_path1, 'w', newline='') as csvfile:
            fieldnames = element_data[0].keys()  # Automatically get column names from the first dict
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()   # Write column names
            writer.writerows(element_data) # Write all rows

        plot_csv.plot_power_vs_time(out_path1)
        plot_csv.plot_xy_path(out_path1)
        extract_obp_elements.split_csv_files(out_path1)

        
        
if __name__ == "__main__":
    unittest.main()