import pandas as pd
import matplotlib.pyplot as plt

def plot_power_vs_time(csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Plot power vs time
    plt.figure(figsize=(8, 5))
    plt.plot(df['time'], df['power'], label='Power', color='blue')
    plt.xlabel('Time [s]')
    plt.ylabel('Power [W]')
    plt.title('Power as a Function of Time')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_xy_path(csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Plot x vs y
    plt.figure(figsize=(8, 5))
    plt.plot(df['x'], df['y'], marker='o', linestyle='-', color='green', label='Path')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('XY Coordinate Path')
    plt.grid(True)
    plt.axis('equal')  # Ensures aspect ratio is equal for X and Y
    plt.legend()
    plt.tight_layout()
    plt.show()
