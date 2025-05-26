
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