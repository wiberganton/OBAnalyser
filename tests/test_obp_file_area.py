import unittest

import obanalyser.analyse_obp_geometry as analyse_obp_geometry
import obanalyser.plotters.plot_obp_img as plot_obp_img


class TestMain(unittest.TestCase):
    def test_main(self):
        # build info
        path1 = r"tests\input\cubes_test\obp\new_preheat.obp"
        path2 = r"tests\input\cubes_test\obp\layer_melt.obp"

        img1, area1, geo_file_info = analyse_obp_geometry.rasterize_file(path1, pixel_um=10, close_gap_um=50)
        img2, area2, geo_file_info = analyse_obp_geometry.rasterize_file(path2, pixel_um=10, close_gap_um=50)
        
        print("Analysation of area works")
        print("Area 2 (mm²): ", area2 / 1e6)
        plot_obp_img.plot_obp_img(img1)
        plot_obp_img.plot_obp_img(img2)


if __name__ == "__main__":
    unittest.main()



