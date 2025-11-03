import sqlite3
import pandas as pd

def write_layers(db_path, layer_data_df):
    # Your DataFrame: layer_data_df  (columns: "Time (s)", "Layer", "Build height (mm)")

    conn = sqlite3.connect(db_path)
    layer_data_df.to_sql("layer_metrics", conn, if_exists="replace", index=False)

    conn.close()

def write_energy_input(db_path, energy_data_df):
    # Your DataFrame: energy_data_df  (columns: "Time (s)", "Power (W)")

    conn = sqlite3.connect(db_path)
    energy_data_df.to_sql("energy_input", conn, if_exists="replace", index=False)

    conn.close()

def write_temperatures(db_path, temp_data_df):
    # Your DataFrame: energy_data_df  (columns: "Time (s)", "Sensor1", "Sensor2", ...)

    conn = sqlite3.connect(db_path)
    temp_data_df.to_sql("temperatures", conn, if_exists="replace", index=False)

    conn.close()