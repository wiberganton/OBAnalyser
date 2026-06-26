from pathlib import Path

from obanalyser.analyse_obf_geometry import write_obf_image_stack

"""Example for rasterizing every build layer to a colored image stack."""
build_path = r"tests\input\cubes_test\buildInfo.json"
output_dir = r"tests\output\layer_image_stack"
#output_dir.mkdir(parents=True, exist_ok=True)

write_obf_image_stack(
    build_path,
    output_dir,
    pixel_um=200,
    close_gap_um=50,
)
