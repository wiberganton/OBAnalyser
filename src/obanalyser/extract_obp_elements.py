import obplib as obp
import numpy as np
import csv
import copy
import pandas as pd
import os

from src.config import config
from src.obanalyser.analyse_obp import fill_zeros_with_last_nonzero

def extract_from_build_object(obp_files, out_file, t0=0):
    """
    input:  obp_files is a list with obp files on the form [[(path1_layer1, rep),(path2_layer1, rep)],[(path1_layer2, rep),(path2_layer2, rep)]]
            out_file is a file path (string) to csv file where the element data should be written
    """
    def write_to_csv(data, path, write_header = False, write_data = True, status='a'):
        print("data[0] ",data[0])
        print("data[0].keys() ",data[0].keys())
        with open(path, status, newline='') as csvfile:
            fieldnames = data[0].keys()  # Automatically get column names from the first dict
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()   # Write column names
            if write_data:
                writer.writerows(data) # Write all rows
    # Write headers to a new file
    write_to_csv(
        [{"x": 0, "y": 0, "spot_size": 0, "power": 0, "time": 0}],
        out_file,
        write_header=True,
        write_data=False,
        status='w'
    )
    t = t0
    for layer in obp_files:
        data = get_delay_elements(config.transition_time, t0=t)
        write_to_csv(data, out_file)
        t += config.transition_time
        for file in layer:
            data = extract_from_obp_file(file[0], start_time = t)
            repeat = file[1]
            result = []
            # Precompute time deltas from the original list
            time_deltas = [0]  # First element stays at offset 0
            for i in range(1, len(data)):
                delta = data[i]["time"] - data[i - 1]["time"]
                time_deltas.append(delta)
            # Initialize time to start from
            current_time = 0
            for _ in range(repeat):
                for i, item in enumerate(data):
                    new_item = copy.deepcopy(item)
                    new_item["time"] = current_time
                    result.append(new_item)
                    if i < len(time_deltas):
                        current_time += time_deltas[i]
            write_to_csv(result, out_file)
            t = result[-1]["time"]


def extract_from_obp_file(obp_path, start_time = 0):
    """
    input:  obp_path string with path to obp file
            start_time is in seconds when the first element is executed
    return: list with point wise obp data on the form [{x,y,spot_size,power,time}]
    """
    elements = obp.read_obp(obp_path)
    element_data = []
    t = start_time
    for element in elements:
        if not isinstance(element, list):
            element = [element]
        for lst_el in element:
            if isinstance(lst_el, obp.TimedPoints):
                dwellTimes = fill_zeros_with_last_nonzero(lst_el.dwellTimes)
                for i, point in enumerate(lst_el.points):
                    element_data.append({
                        "x": point.x / 1000,
                        "y": point.y / 1000,
                        "spot_size": lst_el.bp.spot_size,
                        "power": lst_el.bp.power,
                        "time": t + dwellTimes[i] / 1e9
                    })
                t += sum(dwellTimes) / 1e9
            elif isinstance(lst_el, obp.Line):
                line_points = calc_line_point_approximation(lst_el, t0=t)
                element_data.extend(line_points)
                t += lst_el.get_segment_duration()
            elif isinstance(lst_el, obp.Curve):
                line_points = calc_curve_point_approximation(lst_el, t0=t)
                element_data.extend(line_points)
                t += lst_el.get_segment_duration()
    return (element_data, t)


def calc_line_point_approximation(line, t0=0):
    segment_length = line.get_segment_length()
    points = [] # list of spots {x[mm], y[mm], spot_size[um], power[W], time[s]}
    step = 0
    while step <= segment_length:
        speed = line.Speed
        dx = line.P2.x - line.P1.x
        dy = line.P2.y - line.P1.y
        if step > 0:
            dx *= step / segment_length
            dy *= step / segment_length
        else:
            dx = 0
            dy = 0
        points.append({
            "x": (line.P1.x+dx)/1000,
            "y": (line.P1.y+dy)/1000,
            "spot_size": line.bp.spot_size,
            "power": line.bp.power,
            "time": t0+step/speed
        })
        step += config.length_step
    return points
def calc_curve_point_approximation(line, t0=0):
    segment_length = line.get_segment_length()
    segment_duration = line.get_segment_duration()
    points = [] # list of spots {x[mm], y[mm], spot_size[um], power[W], time[s]}
    steps = np.linspace(0, 1, int(segment_length/config.length_step)+1)

    P1 = np.array([line.P1.x, line.P1.y])
    P2 = np.array([line.P2.x, line.P2.y])
    P3 = np.array([line.P3.x, line.P3.y])
    P4 = np.array([line.P4.x, line.P4.y])

    for step in steps:
        points.append({
            "x": float(line._bez(P1, P2, P3, P4, step)[0]/1000),
            "y": float(line._bez(P1, P2, P3, P4, step)[1]/1000),
            "spot_size": line.bp.spot_size,
            "power": line.bp.power,
            "time": t0+step*segment_duration
        })
    return points


def get_delay_elements(t, t0=0):
    elements = [
        {
            "x": 0,
            "y": 0,
            "spot_size": 1000,
            "power": 0,
            "time": t0
        },
        {
            "x": 0,
            "y": 0,
            "spot_size": 1000,
            "power": 0,
            "time": t0+t
        }
    ]
    return elements

def split_csv_files(input_csv):
    def save_time_xy(input_csv, output_csv):
        df = pd.read_csv(input_csv)
        df[['time', 'x', 'y']].to_csv(output_csv, index=False)
        print(f"Saved: {output_csv}")

    def save_time_spot_size_changes(input_csv, output_csv):
        df = pd.read_csv(input_csv)
        df_changes = df.loc[(df['spot_size'] != df['spot_size'].shift()) | 
                            (df['spot_size'] != df['spot_size'].shift(-1))]
        df_changes[['time', 'spot_size']].to_csv(output_csv, index=False)
        print(f"Saved: {output_csv}")

    def save_time_power_changes(input_csv, output_csv):
        df = pd.read_csv(input_csv)
        df_changes = df.loc[(df['power'] != df['power'].shift()) | 
                            (df['power'] != df['power'].shift(-1))]
        df_changes[['time', 'power']].to_csv(output_csv, index=False)
        print(f"Saved: {output_csv}")
    base = os.path.splitext(input_csv)[0]
    save_time_xy(input_csv, base + r"_time_xy.csv")
    save_time_spot_size_changes(input_csv, base + r"_time_spot_size.csv")
    save_time_power_changes(input_csv, base + r"_time_power.csv")