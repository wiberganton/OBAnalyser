import matplotlib.pyplot as plt

def plot_obp_img(img):
    try:
        plt.imshow(img, origin='upper', cmap='gray')
        plt.title("Rasterized coverage")
        plt.axis('equal'); plt.show()
    except Exception:
        pass