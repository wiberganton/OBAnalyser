import json
import math
import colorsys
from pathlib import Path

import cv2
import numpy as np
import obplib as obp

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None

from obanalyser.data_classes import GeometryLayerInfo, GeometryInfo
import obanalyser.get_build_order as get_build_order
import obanalyser.analyse_obp_geometry as analyse_obp_geometry
from obanalyser.config import config

DEFAULT_SINTERED_RGB = (190, 190, 190)
DEFAULT_BACKGROUND_RGB = (255, 255, 255)
DEFAULT_PART_COLORS = (
    (230, 57, 70),
    (29, 185, 84),
    (0, 95, 184),
    (244, 162, 97),
    (42, 157, 143),
    (255, 190, 11),
    (131, 56, 236),
    (109, 76, 65),
)

def analyse_obf_geometry(build_json):
    """
    Reads an build_json inside an obf folder and returns a dictionary with the geometry information
    """
    (build_sequence, start_heat_path)= get_build_order.get_layer_execution_sequence(build_json)
    layer_info = get_build_order.get_other_layer_info(build_json)
    layers = []
    
    for i in range(len(layer_info)):
        #obp_info = analyse_obp.analyse_obp_files(build_sequence[i])
        melt_area, files = analyse_obp_geometry.analyse_obp_files_area(build_sequence[i]) # in mm2
        total_area_mm2 = (config.build_plate_diameter/2)**2*math.pi*1000000
        layer_info_object = GeometryLayerInfo(
            layer_index = i,
            melt_area_mm2 = melt_area*0.000001,
            melt_portion = melt_area*0.000001/total_area_mm2,
            files= files
        )
        layers.append(layer_info_object)

    geometry_info = GeometryInfo(
        layers = layers 
    )
    return geometry_info


def analyse_obf_geom(
    build_json: str | Path,
    pixel_um: float = 100,
    close_gap_um: float = 100,
    sintered_rgb: tuple[int, int, int] = DEFAULT_SINTERED_RGB,
    background_rgb: tuple[int, int, int] = DEFAULT_BACKGROUND_RGB,
    part_colors: tuple[tuple[int, int, int], ...] | None = None,
    show_progress: bool = True,
):
    """
    Create a layer image stack for the full build.

    Each image in the stack represents one layer and uses:
      - white for untouched areas
      - one fixed color for sintered but not melted areas
      - one distinct color per melted part

    Returns:
        image_stack: ndarray [layer, row, col, rgb]
        origin_xy_um: (minx, miny) origin in micrometers
        pixel_um: raster resolution in micrometers
    """
    build_json = str(build_json)
    build_sequence, _ = get_build_order.get_layer_execution_sequence(build_json)
    file_cache, bounds = _prepare_file_cache(
        build_sequence,
        pixel_um,
        close_gap_um,
        show_progress=show_progress,
    )

    if bounds is None:
        layer_count = len(build_sequence)
        empty_stack = np.empty((layer_count, 1, 1, 3), dtype=np.uint8)
        empty_stack[...] = background_rgb
        return empty_stack, (0.0, 0.0), pixel_um

    file_masks, canvas_shape = _rasterize_cached_files(
        file_cache,
        bounds,
        pixel_um,
        close_gap_um,
        show_progress=show_progress,
    )
    image_stack = np.empty(
        (len(build_sequence), canvas_shape[0], canvas_shape[1], 3),
        dtype=np.uint8,
    )
    image_stack[...] = background_rgb

    part_palette = tuple(part_colors or DEFAULT_PART_COLORS)

    for layer_index, layer_sequence in enumerate(
        _progress_iter(build_sequence, show_progress, desc="Composing layers")
    ):
        sintered_mask = np.zeros(canvas_shape, dtype=bool)
        melt_mask = np.zeros(canvas_shape, dtype=bool)

        for obp_path, _ in layer_sequence:
            file_data = file_cache[obp_path]
            mask = file_masks[obp_path]
            if file_data["is_melt"]:
                melt_mask |= mask
            else:
                sintered_mask |= mask

        sintered_mask &= ~melt_mask
        layer_img = image_stack[layer_index]
        layer_img[sintered_mask] = sintered_rgb

        n_labels, label_map, _, centroids = cv2.connectedComponentsWithStats(
            melt_mask.astype(np.uint8),
            connectivity=8,
        )
        for part_index, label in enumerate(_sorted_component_labels(n_labels, centroids)):
            layer_img[label_map == label] = _part_color(part_index, part_palette)

    return image_stack, (bounds[0], bounds[1]), pixel_um


def analyse_obf_layer_image_stack(*args, **kwargs):
    return analyse_obf_geom(*args, **kwargs)


def write_obf_image_stack(
    build_json: str | Path,
    output_dir: str | Path,
    pixel_um: float = 100,
    close_gap_um: float = 100,
    sintered_rgb: tuple[int, int, int] = DEFAULT_SINTERED_RGB,
    background_rgb: tuple[int, int, int] = DEFAULT_BACKGROUND_RGB,
    part_colors: tuple[tuple[int, int, int], ...] | None = None,
    image_prefix: str = "layer_",
    metadata_filename: str = "metadata.json",
    show_progress: bool = True,
):
    """
        Write a colored layer stack as PNG slices plus a metadata sidecar.

        The metadata stores the RGB color codes used in the images.
    """
    build_json = str(build_json)
    image_stack, _, pixel_um = analyse_obf_geom(
        build_json,
        pixel_um=pixel_um,
        close_gap_um=close_gap_um,
        sintered_rgb=sintered_rgb,
        background_rgb=background_rgb,
        part_colors=part_colors,
        show_progress=show_progress,
    )
    layer_info = get_build_order.get_other_layer_info(build_json)
    slice_thickness_mm = abs(layer_info[0][1]) if layer_info else 0.0
    return write_image_stack_with_metadata(
        image_stack=image_stack,
        output_dir=output_dir,
        pixel_size_mm=pixel_um / 1000.0,
        slice_thickness_mm=slice_thickness_mm,
        background_rgb=background_rgb,
        sintered_rgb=sintered_rgb,
        image_prefix=image_prefix,
        metadata_filename=metadata_filename,
        show_progress=show_progress,
    )


def write_image_stack_with_metadata(
    image_stack: np.ndarray,
    output_dir: str | Path,
    pixel_size_mm: float,
    slice_thickness_mm: float,
    background_rgb: tuple[int, int, int] = DEFAULT_BACKGROUND_RGB,
    sintered_rgb: tuple[int, int, int] = DEFAULT_SINTERED_RGB,
    image_prefix: str = "layer_",
    metadata_filename: str = "metadata.json",
    show_progress: bool = True,
):
    """Write a colored RGB stack as PNG slices and metadata."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    value_meaning = _rgb_stack_to_rgb_value_meaning(
        image_stack,
        background_rgb=background_rgb,
        sintered_rgb=sintered_rgb,
    )

    for layer_index, layer_img in enumerate(
        _progress_iter(image_stack, show_progress, desc="Writing image slices")
    ):
        slice_path = output_path / f"{image_prefix}{layer_index:04d}.png"
        _write_png(slice_path, layer_img)

    metadata = {
        "axis": "z",
        "unit": "mm",
        "pixel_size_x": pixel_size_mm,
        "pixel_size_y": pixel_size_mm,
        "slice_thickness": slice_thickness_mm,
        "origin": [0, 0, 0],
        "value_meaning": value_meaning,
    }
    metadata_path = output_path / metadata_filename
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    return image_stack, metadata_path


def _prepare_file_cache(build_sequence, pixel_um: float, close_gap_um: float, show_progress: bool = True):
    file_cache = {}
    bounds = None

    unique_paths = []
    seen_paths = set()
    for layer_sequence in build_sequence:
        for obp_path, _ in layer_sequence:
            if obp_path in seen_paths:
                continue
            seen_paths.add(obp_path)
            unique_paths.append(obp_path)

    for obp_path in _progress_iter(unique_paths, show_progress, desc="Caching OBP files"):
        if obp_path in file_cache:
            continue

        elements = list(obp.read_obp(obp_path))
        padded_bounds = analyse_obp_geometry.get_padded_bounds(elements)
        file_cache[obp_path] = {
            "elements": elements,
            "padded_bounds": padded_bounds,
            "is_melt": False,
        }

        if padded_bounds is None:
            continue

        _, _, _, averages = analyse_obp_geometry.rasterize_coverage(
            elements,
            pixel_um=pixel_um,
            close_gap_um=close_gap_um,
        )
        file_cache[obp_path]["is_melt"] = analyse_obp_geometry.is_melt_scan(*averages)
        bounds = _merge_bounds(bounds, padded_bounds)

    return file_cache, bounds


def _rasterize_cached_files(file_cache, bounds, pixel_um: float, close_gap_um: float, show_progress: bool = True):
    canvas_shape = analyse_obp_geometry.rasterize_coverage_to_bounds(
        [],
        pixel_um=pixel_um,
        bounds_xyxy=bounds,
        close_gap_um=None,
    )[0].shape
    file_masks = {}

    for obp_path, file_data in _progress_iter(file_cache.items(), show_progress, desc="Rasterizing files"):
        if file_data["padded_bounds"] is None:
            file_masks[obp_path] = np.zeros(canvas_shape, dtype=bool)
            continue

        mask_img, _, _, _ = analyse_obp_geometry.rasterize_coverage_to_bounds(
            file_data["elements"],
            pixel_um=pixel_um,
            bounds_xyxy=bounds,
            close_gap_um=close_gap_um,
        )
        file_masks[obp_path] = mask_img.astype(bool)

    return file_masks, canvas_shape


def _progress_iter(iterable, show_progress: bool, desc: str):
    if not show_progress or tqdm is None:
        return iterable
    return tqdm(iterable, desc=desc, unit="item")


def _merge_bounds(current_bounds, new_bounds):
    if current_bounds is None:
        return new_bounds

    return (
        min(current_bounds[0], new_bounds[0]),
        min(current_bounds[1], new_bounds[1]),
        max(current_bounds[2], new_bounds[2]),
        max(current_bounds[3], new_bounds[3]),
    )


def _sorted_component_labels(n_labels: int, centroids):
    labels = range(1, n_labels)
    return sorted(labels, key=lambda label: (float(centroids[label][0]), float(centroids[label][1])))


def _part_color(part_index: int, palette: tuple[tuple[int, int, int], ...]):
    if part_index < len(palette):
        return palette[part_index]

    hue = (part_index * 0.6180339887498949) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.75, 0.95)
    return (
        int(round(red * 255)),
        int(round(green * 255)),
        int(round(blue * 255)),
    )


def _rgb_stack_to_rgb_value_meaning(
    image_stack: np.ndarray,
    background_rgb: tuple[int, int, int],
    sintered_rgb: tuple[int, int, int],
):
    background_color = tuple(int(channel) for channel in background_rgb)
    sintered_color = tuple(int(channel) for channel in sintered_rgb)
    unique_colors = [tuple(int(channel) for channel in color) for color in np.unique(image_stack.reshape(-1, 3), axis=0)]

    ordered_colors = [background_color, sintered_color] + [
        color for color in unique_colors
        if color not in {background_color, sintered_color}
    ]

    value_meaning = {}
    for index, color in enumerate(ordered_colors):
        if color == background_color:
            meaning = "empty"
        elif color == sintered_color:
            meaning = "sintered"
        else:
            meaning = f"melt{index - 1}"
        value_meaning[_rgb_code(color)] = meaning

    return value_meaning


def _rgb_code(color: tuple[int, int, int]) -> str:
    return f"{color[0]},{color[1]},{color[2]}"


def _write_png(path: Path, image: np.ndarray):
    """Write PNG files robustly, including unicode paths on Windows."""
    encoded_ok, encoded = cv2.imencode(".png", image)
    if not encoded_ok:
        raise RuntimeError(f"Failed to encode image data for '{path}'")

    try:
        encoded.tofile(str(path))
    except Exception as exc:
        raise RuntimeError(f"Failed to write image file '{path}'") from exc
