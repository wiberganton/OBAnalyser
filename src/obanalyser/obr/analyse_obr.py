import pandas as pd
import numpy as np
from functools import reduce

from obanalyser.obr.recoate_times import get_recoate_times
from obanalyser.obr.layer_heights import get_layer_heights
from obanalyser.obr.write_db import write_layers, write_energy_input, write_temperatures
from obanalyser.obr.exposure import get_power_times
from obanalyser.obr.temperatures import read_mqqt

def analyse_obr(
        log_file, 
        db_path=r"tests\output\obr_analysis.db",
        temp_sensors=[
            ('freemelt/0/ChamberService/0/BuildTemperature/Name/Sensor1', 'Temperature'),
            ('freemelt/0/PyrometerService/0/BuildTemperature/Name/Pyrometer',"Temperature")
        ]):
    # Get recoate times
    recoate_df = get_recoate_times(log_file)
    t0 = recoate_df["Time (s)"].iloc[0]
    recoate_df["Time (s)"] = (recoate_df["Time (s)"] - t0) / 1e9  # Convert to seconds
    # Get build heights
    heights = get_layer_heights(log_file, t0=t0)

    df_build = heights # with columns ["Build height (mm)", "time"]
    df_layers = recoate_df #with columns ["Time (s)", "Layer"]

    bins = np.append(df_layers["Time (s)"].values, np.inf)  # add infinity for the last layer
    df_build["Layer"] = pd.cut(
        df_build["time"],
        bins=bins,
        labels=df_layers["Layer"],
        right=False  # intervals are [start, end)
    )
    df_result = df_build[["Build height (mm)", "Layer"]].dropna().reset_index(drop=True)
    df_last = df_result.groupby("Layer", as_index=False).last()
    layer_combined = pd.merge(recoate_df, df_last, on="Layer")
    layer_combined["Layer height (mm)"] = layer_combined["Build height (mm)"].diff().fillna(layer_combined["Build height (mm)"].iloc[0])
    write_layers(db_path, layer_combined)
    # Get exposure times
    exposure_times = get_power_times(log_file, t0)
    write_energy_input(db_path, exposure_times)
    # Temperatures
    dfs = []
    for sensor_tag, sensor_name in temp_sensors:
        temp = read_mqqt(log_file, sensor_tag, t0, value_key=sensor_name)
        dfs.append(temp)
    dfs_long = []  # to collect transformed DFs
    for i, df in enumerate(dfs):
        # Extract sensor name (the second column)
        sensor_col = df.columns[1]
        # Rename columns to consistent names
        temp_df = df.rename(columns={
            "Time (s)": "Time",
            sensor_col: "Temp"
        }).copy()
        # Add Index column (sensor index or name)
        temp_df["Index"] = sensor_col  # or i if you prefer numbers
        dfs_long.append(temp_df)
    df_temps = pd.concat(dfs_long, ignore_index=True)
    write_temperatures(db_path, df_temps)
