import obplib as obp
import numpy as np
import csv
import copy
import pandas as pd
import os

from obanalyser.config import config
from obanalyser.analyse_obp import fill_zeros_with_last_nonzero
import obanalyser.plotters.plot_csv as plot_csv

def extract_multiple_files(obp_files, out_file, t0=0, plot_info=False):
    """
    input:  obp_files is a list with obp files on the form [[(path1_layer1, rep),(path2_layer1, rep)],[(path1_layer2, rep),(path2_layer2, rep)]]
            if the path = "" a delay of rep seconds is inserted
    """
    element_data = []
    t = t0
    for layer in obp_files:
        for path, rep in layer:
            if path == "":
                element_data.extend(get_delay_elements(rep, t0=t))
                t += rep
            else:
                for i in range(rep):
                    local_data, t_local = extract_from_obp_file(path, start_time=t)
                    element_data.extend(local_data)
                    t = t_local
    with open(out_file, 'w', newline='') as csvfile:
        fieldnames = element_data[0].keys()  # Automatically get column names from the first dict
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()   # Write column names
        writer.writerows(element_data) # Write all rows
    split_csv_files(out_file)
    if plot_info:
        plot_csv.plot_xy_path(out_file)
        plot_csv.plot_power_vs_time(out_file)


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
                local_t = t
                for i, point in enumerate(lst_el.points):
                    local_t += dwellTimes[i] / 1e9
                    element_data.append({
                        "x": point.x / 1000,
                        "y": point.y / 1000,
                        "spot_size": lst_el.bp.spot_size,
                        "power": lst_el.bp.power,
                        "time": local_t
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
        records = []
        # Always start with the first row
        first_row = df.iloc[0]
        records.append({'time': first_row['time'], 'spot_size': first_row['spot_size']})
        for i in range(1, len(df)):
            prev_row = df.iloc[i - 1]
            curr_row = df.iloc[i]
            if curr_row['spot_size'] != prev_row['spot_size']:
                # Add the change point with the previous value
                records.append({'time': curr_row['time'], 'spot_size': prev_row['spot_size']})
                # Add the change point with the new value
                records.append({'time': curr_row['time'], 'spot_size': curr_row['spot_size']})
        # Add final value explicitly
        last_row = df.iloc[-1]
        records.append({'time': last_row['time'], 'spot_size': last_row['spot_size']})
        # Save to CSV
        changes_df = pd.DataFrame(records)
        changes_df.to_csv(output_csv, index=False)
        print(f"Saved: {output_csv}")

    def save_time_power_changes(input_csv, output_csv):
        df = pd.read_csv(input_csv)
        records = []
        # Always start with the first row
        first_row = df.iloc[0]
        records.append({'time': first_row['time'], 'power': first_row['power']})
        for i in range(1, len(df)):
            prev_row = df.iloc[i - 1]
            curr_row = df.iloc[i]
            if curr_row['power'] != prev_row['power']:
                # Add the change point with the previous value
                records.append({'time': curr_row['time'], 'power': prev_row['power']})
                # Add the change point with the new value
                records.append({'time': curr_row['time'], 'power': curr_row['power']})
        # Add final value explicitly
        last_row = df.iloc[-1]
        records.append({'time': last_row['time'], 'power': last_row['power']})
        # Save to CSV
        changes_df = pd.DataFrame(records)
        changes_df.to_csv(output_csv, index=False)
        print(f"Saved: {output_csv}")
        
    base = os.path.splitext(input_csv)[0]
    save_time_xy(input_csv, base + r"_time_xy.csv")
    save_time_spot_size_changes(input_csv, base + r"_time_spot_size.csv")
    save_time_power_changes(input_csv, base + r"_time_power.csv")