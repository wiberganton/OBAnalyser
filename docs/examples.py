# Example for exporting build info to JSON
import obanalyser.analyse_build as analyse_build
import obanalyser.plotters.plot_build_data as plot_build_data
path = r"tests\input\cubes_test\buildInfo.json"
build = analyse_build.analyse_build(path)
build.to_json(r"tests\output\build_info.json")

plot_build_data.plot_build_data(build)