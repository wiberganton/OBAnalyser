import numpy as np
import cv2

import obplib as obp
from obplib import Point, Line, TimedPoints

from obanalyser.config import config
# Assuming your classes: Point, Beamparameters, Line, TimedPoints exist

def analyse_obp_files_area(obp_files_list):
    """
    Reads a list of obp files and returns the total area of the files
    """
    area_um2 = 0.0
    for obp_file in obp_files_list:
        img, area = rasterize_file(obp_file[0], pixel_um=10, close_gap_um=50)
        area_um2 += area
    return area_um2

def rasterize_file(obp_path: str, pixel_um: float=100, close_gap_um: float=100):
    """
    input:  obp_path string with path to obp file
            pixel_um: pixel size in µm
            close_gap_um: optional morphological closing to seal gaps up to this size (µm)
    return: img (uint8 0/255), origin (minx, miny), pixel_um
    """
    elements = obp.read_obp(obp_path)
    img, origin, px = rasterize_coverage(elements, pixel_um, close_gap_um)
    area = raster_area_um2(img, px)
    img = cv2.bitwise_not(img)
    return img, area

def _bounds_and_pad(elements):
    xs, ys, max_spot = [], [], 0.0
    for el in elements:
        if isinstance(el, TimedPoints) or isinstance(el, Line):
            if el.bp.spot_size < config.melt_spot_size_threshold:
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
        return np.zeros((1,1), np.uint8), (minx, miny), pixel_um

    pad = max_spot  # pad by one diameter to be safe
    minx -= pad; miny -= pad; maxx += pad; maxy += pad

    width_um = maxx - minx
    height_um = maxy - miny
    W = int(np.ceil(width_um / pixel_um)) + 1
    H = int(np.ceil(height_um / pixel_um)) + 1

    img = np.zeros((H, W), dtype=np.uint8)

    def to_px(p: Point):
        # Pixel coordinates: x→col (j), y→row (i); y flipped to image coords
        j = int(round((p.x - minx) / pixel_um))
        i = int(round((maxy - p.y) / pixel_um))
        return (j, i)

    for el in elements:
        if isinstance(el, TimedPoints) or isinstance(el, Line):
            if el.bp.spot_size < config.melt_spot_size_threshold:
                if isinstance(el, TimedPoints):
                    rad_px = int(np.ceil((el.bp.spot_size / 2.0) / pixel_um))
                    for p in el.points:
                        j,i = to_px(p)
                        cv2.circle(img, (j,i), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)
                elif isinstance(el, Line):
                    thickness_px = max(1, int(round(el.bp.spot_size / pixel_um)))
                    rad_px = max(1, int(np.ceil((el.bp.spot_size / 2.0) / pixel_um)))
                    j1,i1 = to_px(el.P1)
                    j2,i2 = to_px(el.P2)
                    # draw center segment
                    cv2.line(img, (j1,i1), (j2,i2), 255, thickness=thickness_px, lineType=cv2.LINE_8)
                    # round caps at ends (OpenCV lines are flat-capped)
                    cv2.circle(img, (j1,i1), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)
                    cv2.circle(img, (j2,i2), rad_px, 255, thickness=-1, lineType=cv2.LINE_8)

    # Optional morphological closing to seal tiny gaps
    if close_gap_um and close_gap_um > 0:
        k = max(1, int(round(close_gap_um / pixel_um)))
        # ensure odd kernel size
        if k % 2 == 0: k += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k,k))
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=1)

    return img, (minx, miny), pixel_um

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