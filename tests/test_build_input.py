import unittest
import obanalyser.analyse_build as analyse_build

class TestMain(unittest.TestCase):
    def test_main(self):
        # build info
        path = r"tests\input\cubes_test\buildInfo.json"
        build = analyse_build.analyse_build(path)
        build.to_json(r"tests\output\build_info.json")
        
        #plot_csv_file.plot_csv(out)
        print("test_build_input works")
if __name__ == "__main__":
    unittest.main()



