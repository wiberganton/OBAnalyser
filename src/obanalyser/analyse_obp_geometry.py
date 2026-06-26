import cv2
import numpy as np

import obplib as obp
from obplib import Line, Point, TimedPoints

from obanalyser.config import config
from obanalyser.data_classes import GeometryFileInfo

def analyse_obp_files_area(obp_files_list):
    """
    Reads a list of obp files and returns the total area of the files
    """
    area_um2 = 0.0
    files = []
    for obp_file in obp_files_list:
        img, melt_area, file_info = rasterize_file(obp_file[0], pixel_um=10, close_gap_um=20)
        area_um2 += melt_area
        files.append(file_info)
    return area_um2, files


def is_melt_scan(average_spot_size: float, average_power: float) -> bool:
    return (
        average_spot_size < config.melt_spot_size_threshold
        and average_power > config.melt_watt_threshold
    )

def rasterize_file(obp_path: str, pixel_um: float=100, close_gap_um: float=100):
    """
    input:  obp_path string with path to obp file
            pixel_um: pixel size in µm
            close_gap_um: optional morphological closing to seal gaps up to this size (µm)
    return: img (uint8 0/255), origin (minx, miny), pixel_um
    """
    elements = obp.read_obp(obp_path)
    img, origin, px, averages = rasterize_coverage(elements, pixel_um, close_gap_um)
    average_spot_size, average_power = averages

    area = raster_area_um2(img, px)
    img = cv2.bitwise_not(img)

    if is_melt_scan(average_spot_size, average_power):
        area_melt = area
        totalt_area = area
    else:
        area_melt = 0.0
        totalt_area = area
    geo_file_info = GeometryFileInfo(
        melt_area_mm2 = area_melt * 0.000001,
        total_area_mm2 = totalt_area * 0.000001,
        spot_size_um = average_spot_size
    )

    return img, area_melt, geo_file_info

def _bounds_and_pad(elements):
    xs, ys, max_spot = [], [], 0.0
    for el in elements:
        if isinstance(el, TimedPoints) or isinstance(el, Line):
            if isinstance(el, TimedPoints):
                for p in el.points:
                    xs.append(p.x); ys.append(p.y)
                max_spot = max(max_spot, float(el.bp.spot_size))
            elif isinstance(el, Line):
                xs += [el.P1.x, el.P2.x]; ys += [el.P1.y, el.P2.y]
                max_spot = max(max_spot, float(el.bp.spot_size))
    if not xs:
        return (0,0,0,0,0)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    return minx, miny, maxx, maxy, max_spot


def get_padded_bounds(elements):
    minx, miny, maxx, maxy, max_spot = _bounds_and_pad(elements)
    if max_spot == 0:
        return None
    pad = max_spot
    return minx - pad, miny - pad, maxx + pad, maxy + pad


def _bounds_to_shape(bounds_xyxy: tuple[float, float, float, float], pixel_um: float):
    minx, miny, maxx, maxy = bounds_xyxy
    width_um = maxx - minx
    height_um = maxy - miny
    width_px = int(np.ceil(width_um / pixel_um)) + 1
    height_px = int(np.ceil(height_um / pixel_um)) + 1
    return height_px, width_px


def _draw_elements_on_canvas(
    img: np.ndarray,
    elements,
    pixel_um: float,
    minx: float,
    maxy: float,
):
    def to_px(p: Point):
        col = int(round((p.x - minx) / pixel_um))
        row = int(round((maxy - p.y) / pixel_um))
        return col, row

    spot_sizes = []
    powers = []

    for el in elements:
        if not isinstance(el, (TimedPoints, Line)):
            continue

        spot_sizes.append(el.bp.spot_size)
        powers.append(el.bp.power)

        if isinstance(el, TimedPoints):
            rad_px = int(np.ceil((el.bp.spot_size / 2.0) / pixel_um))
            for p in el.points:
                col, row = to_px(p)
                cv2.circle(img, (col, row), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)
            continue

        thickness_px = max(1, int(round(el.bp.spot_size / pixel_um)))
        rad_px = max(1, int(np.ceil((el.bp.spot_size / 2.0) / pixel_um)))
        col1, row1 = to_px(el.P1)
        col2, row2 = to_px(el.P2)
        cv2.line(
            img,
            (col1, row1),
            (col2, row2),
            255,
            thickness=thickness_px,
            lineType=cv2.LINE_8,
        )
        cv2.circle(img, (col1, row1), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)
        cv2.circle(img, (col2, row2), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)

    average_spot_size = sum(spot_sizes) / len(spot_sizes) if spot_sizes else 0.0
    average_power = sum(powers) / len(powers) if powers else 0.0
    return average_spot_size, average_power

def rasterize_coverage(elements, pixel_um: float, close_gap_um: float | None = None):
    """
    Rasterize elements into a binary image.
    Returns: img (uint8 0/255), origin (minx, miny), pixel_um
    """
    if pixel_um <= 0:
        raise ValueError("pixel_um must be > 0")

    minx, miny, maxx, maxy, max_spot = _bounds_and_pad(elements)
    if max_spot == 0:
        # nothing to draw
        return np.zeros((1,1), np.uint8), (minx, miny), pixel_um, (0.0, 0.0)

    pad = max_spot  # pad by one diameter to be safe
    minx -= pad; miny -= pad; maxx += pad; maxy += pad

    height_px, width_px = _bounds_to_shape((minx, miny, maxx, maxy), pixel_um)
    img = np.zeros((height_px, width_px), dtype=np.uint8)
    average_spot_size, average_powers = _draw_elements_on_canvas(img, elements, pixel_um, minx, maxy)

    # Optional morphological closing to seal tiny gaps
    if close_gap_um and close_gap_um > 0:
        k = max(1, int(round(close_gap_um / pixel_um)))
        # ensure odd kernel size
        if k % 2 == 0: k += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k,k))
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=1)

    return img, (minx, miny), pixel_um, (average_spot_size, average_powers)


def rasterize_coverage_to_bounds(
    elements,
    pixel_um: float,
    bounds_xyxy: tuple[float, float, float, float],
    close_gap_um: float | None = None,
):
    if pixel_um <= 0:
        raise ValueError("pixel_um must be > 0")

    minx, miny, maxx, maxy = bounds_xyxy
    height_px, width_px = _bounds_to_shape(bounds_xyxy, pixel_um)
    img = np.zeros((height_px, width_px), dtype=np.uint8)
    average_spot_size, average_power = _draw_elements_on_canvas(img, elements, pixel_um, minx, maxy)

    if close_gap_um and close_gap_um > 0:
        k = max(1, int(round(close_gap_um / pixel_um)))
        if k % 2 == 0:
            k += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=1)

    return img, (minx, miny), pixel_um, (average_spot_size, average_power)

def raster_area_um2(img: np.ndarray, pixel_um: float) -> float:
    return float(np.count_nonzero(img)) * (pixel_um ** 2)

def raster_contours(img: np.ndarray, origin_xy: tuple[float,float], pixel_um: float):
    """
    Extract polygon contours (outer boundaries) from the raster, as lists of (x_um,y_um).
    """
    # OpenCV expects white=object; we already have that
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    minx, miny = origin_xy
    H, W = img.shape

    polys = []
    for cnt in contours:
        pts = []
        for p in cnt[:,0,:]:
            j, i = int(p[0]), int(p[1])
            x = minx + j * pixel_um
            y = (miny + H * pixel_um) - i * pixel_um  # invert y mapping used above
            pts.append((x, y))
        # optional simplification with Douglas–Peucker (in µm)
        polys.append(pts)
    return polys
