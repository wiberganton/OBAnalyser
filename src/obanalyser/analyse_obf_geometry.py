import math
import colorsys

import cv2
import numpy as np
import obplib as obp

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
    build_json: str,
    pixel_um: float = 100,
    close_gap_um: float = 100,
    sintered_rgb: tuple[int, int, int] = DEFAULT_SINTERED_RGB,
    background_rgb: tuple[int, int, int] = DEFAULT_BACKGROUND_RGB,
    part_colors: tuple[tuple[int, int, int], ...] | None = None,
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
    build_sequence, _ = get_build_order.get_layer_execution_sequence(build_json)
    file_cache, bounds = _prepare_file_cache(build_sequence, pixel_um, close_gap_um)

    if bounds is None:
        layer_count = len(build_sequence)
        empty_stack = np.empty((layer_count, 1, 1, 3), dtype=np.uint8)
        empty_stack[...] = background_rgb
        return empty_stack, (0.0, 0.0), pixel_um

    file_masks, canvas_shape = _rasterize_cached_files(file_cache, bounds, pixel_um, close_gap_um)
    image_stack = np.empty(
        (len(build_sequence), canvas_shape[0], canvas_shape[1], 3),
        dtype=np.uint8,
    )
    image_stack[...] = background_rgb

    part_palette = tuple(part_colors or DEFAULT_PART_COLORS)

    for layer_index, layer_sequence in enumerate(build_sequence):
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


def _prepare_file_cache(build_sequence, pixel_um: float, close_gap_um: float):
    file_cache = {}
    bounds = None

    for layer_sequence in build_sequence:
        for obp_path, _ in layer_sequence:
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


def _rasterize_cached_files(file_cache, bounds, pixel_um: float, close_gap_um: float):
    canvas_shape = analyse_obp_geometry.rasterize_coverage_to_bounds(
        [],
        pixel_um=pixel_um,
        bounds_xyxy=bounds,
        close_gap_um=None,
    )[0].shape
    file_masks = {}

    for obp_path, file_data in file_cache.items():
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
