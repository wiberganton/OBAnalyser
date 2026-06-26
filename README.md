# OBAnalyser
OBAnalyser is a Python package for analysing open beam build data, with support for OBF and OBP workflows.

It can be used to:
- extract build-level information such as layer timing, recoating data, and energy-related summaries
- analyse OBP geometry and melt area information
- rasterize full builds into colored per-layer image stacks
- export JSON outputs that can be used in downstream processing pipelines

## Installation

Install from PyPI:
```
pip install OBPAnalyser
```

For local development in a virtual environment:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Minimum example

```
import obanalyser.analyse_build as analyse_build
import obanalyser.plotters.plot_build_data as plot_build_data

path = r"tests\input\cubes_test\buildInfo.json"
build = analyse_build.analyse_build(path)
build.to_json(r"tests\output\build_info.json")

plot_build_data.plot_build_data(build)
```

This reads the build structure, analyses the layer content, writes a JSON summary, and plots the build data.

## Export a colored layer image stack

The package can also rasterize the full build into colored layer images and write a `metadata.json` sidecar file.

```python
from obanalyser.analyse_obf_geometry import write_obf_image_stack

build_path = r"tests\input\cubes_test\buildInfo.json"
output_dir = r"tests\output\layer_image_stack"

write_obf_image_stack(
	build_path,
	output_dir,
	pixel_um=200,
	close_gap_um=50,
)
```

The exported PNG slices are colored images. The metadata file includes:
- stack axis and spatial unit
- pixel size in mm
- slice thickness in mm
- origin
- RGB color codes for empty, sintered, and melt regions


## Example scripts

The repository includes runnable examples in the `docs` folder:
- `docs/examples.py`
- `docs/example_create_image_stack.py`

## Supported inputs

The main build-analysis functions accept either string paths or `Path` objects.

## Notes

- Spatial raster resolution for image stacks is controlled with `pixel_um`.
- Gap closing during rasterization is controlled with `close_gap_um`.
- The image stack export uses white for empty space and a fixed gray color for sintered-but-not-melted areas by default.
