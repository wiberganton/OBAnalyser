import pandas as pd
import os
import matplotlib.pyplot as plt

def plot_lump_temp(temperatures):
    """
    input: temperatures as list on the form [time (s), temp (K)]
    """
    # Split the list into two separate lists for x and y
    x = [row[0] for row in temperatures]
    y = [row[1] for row in temperatures]

    # Plot
    plt.plot(x, y, marker='o')
    plt.xlabel("time (s)")
    plt.ylabel("temperature (K)")
    plt.grid(True)
    plt.show()



def plot_temperature_series(file_list):
    """
    Plots temperature series from a list of CSV files.
    Assumes:
      - First column is 'time'
      - All other columns are temperature values
      - Delimiters may be ',' or ';'
    """
    plt.figure(figsize=(10, 6))

    for file in file_list:
        # Auto-detect delimiter by inspecting the header
        with open(file, 'r', encoding='utf-8') as f:
            header = f.readline()
            delimiter = ';' if ';' in header else ','

        # Load CSV
        df = pd.read_csv(file, delimiter=delimiter)

        # First column is time
        time_col = df.columns[0]

        # Plot all other columns
        for col in df.columns[1:]:
            label = f"{col} ({os.path.basename(file)})"
            plt.plot(df[time_col], df[col], label=label)

    # Plot formatting
    plt.xlabel('Time')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Time from Multiple CSVs')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
