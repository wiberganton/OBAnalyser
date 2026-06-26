from pathlib import Path

import cv2

import obanalyser.analyse_build as analyse_build
import obanalyser.plotters.plot_build_data as plot_build_data
from obanalyser.analyse_obf_geometry import analyse_obf_geom

"""Example for rasterizing every build layer to a colored image stack."""
build_path = r"tests\input\cubes_test\buildInfo.json"
build_path = r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\FreemeltMLdata\OBF_OBR\F4E_23x23x13mm_1_4_2026\F4E_23x23x13mm_5\buildInfo.json"
output_dir = Path(r"tests\output\layer_image_stack")
output_dir = Path(r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\FreemeltMLdata\OBF_OBR\F4E_23x23x13mm_1_4_2026\imageslices")
output_dir.mkdir(parents=True, exist_ok=True)

image_stack, origin_xy_um, pixel_um = analyse_obf_geom(
    build_path,
    pixel_um=200,
    close_gap_um=50,
)

print(f"Created {image_stack.shape[0]} layer images")
print(f"Image size: {image_stack.shape[2]} x {image_stack.shape[1]} pixels")
print(f"Origin in um: {origin_xy_um}")
print(f"Pixel size in um: {pixel_um}")

for layer_index, layer_img in enumerate(image_stack):
    output_path = output_dir / f"layer_{layer_index:04d}.png"
    # analyse_obf_geom returns RGB; OpenCV writes BGR.
    cv2.imwrite(str(output_path), cv2.cvtColor(layer_img, cv2.COLOR_RGB2BGR))