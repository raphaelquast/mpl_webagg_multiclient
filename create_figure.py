import matplotlib.pyplot as plt

def create_figure():
    """Create a simple example figure."""

    f, ax = plt.subplots()
    ax.plot([1,2,3,4,5], "-o")
    ax.plot([5,4,3,2,1], "-o")

    def onclick(event):
        if event.inaxes is ax:
            l, = ax.plot(event.xdata, event.ydata, "o", ms=4)
            ax.draw_artist(l)
            f.canvas.blit()

    f.canvas.mpl_connect("motion_notify_event", onclick)
    return f

