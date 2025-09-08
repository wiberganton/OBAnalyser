import matplotlib.pyplot as plt

def plot_build_data(build):
    layer_time = []
    layer_energy = []
    layer_energy_time = []
    for layer in build.layers:
        layer_time.append(layer.get_layer_time())
        layer_energy.append(layer.get_layer_energy())
        layer_energy_time.append(layer.get_layer_energy()/layer.get_layer_time())
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6))

    # First property
    ax1.bar(range(len(layer_time)), layer_time, color='skyblue')
    ax1.set_xticks(range(len(layer_time)))
    ax1.set_ylabel('Layer time (s)', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.set_title('Layer time')

    # Second property
    ax2.bar(range(len(layer_energy)), layer_energy, color='salmon')
    ax2.set_xticks(range(len(layer_energy)))
    ax2.set_ylabel('Layer energy (J)', color='salmon')
    ax2.tick_params(axis='y', labelcolor='salmon')
    ax2.set_title('Layer energy')

    # Second property
    ax3.bar(range(len(layer_energy_time)), layer_energy_time, color='red')
    ax3.set_xticks(range(len(layer_energy_time)))
    ax3.set_ylabel('J/s', color='red')
    ax3.tick_params(axis='y', labelcolor='red')
    ax3.set_title('Layer energy/time')

    plt.tight_layout()
    plt.show()