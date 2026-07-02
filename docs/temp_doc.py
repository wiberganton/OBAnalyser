from pathlib import Path

from obanalyser.analyse_obf_geometry import write_obf_image_stack

"""Example for rasterizing every build layer to a colored image stack."""
build_path = r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\FreemeltMLdata\OBF_OBR\F4E_Casting_only_250µm_31_3_2026\F4E_Casting_only_250µm_1\buildInfo.json"
output_dir = r"C:\Users\antwi87\OneDrive - Linköpings universitet\Projekt\FreemeltMLdata\OBF_OBR\F4E_Casting_only_250µm_31_3_2026\imagestack"
#output_dir.mkdir(parents=True, exist_ok=True)

write_obf_image_stack(
    build_path,
    output_dir,
    pixel_um=200,
    close_gap_um=50,
)