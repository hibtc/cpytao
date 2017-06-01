import os
from pytao.tao import Tao

# start tao with no plotting and no automatic computation of curves
lattice = os.path.join(os.path.dirname(__file__), 'minimal.lat')
tao = Tao('-lat', lattice, '-noplot', '-gui_mode')
tao.command('place * none')

# list of possible plots can be retrieved using
# `tao.get_list('plot_list t')` or simply `tao.plots()`
plot_name = 'beta'

# enable specific curve to retrieve data
tao.command('place r11', plot_name)
tao.command('set plot r11 visible = T')
tao.command('x_scale r11')
graph, = tao.properties('plot1 r11')['graph']


for curve in tao.curve_names('r11'):
    info = tao.properties('plot_curve', curve)
    data = tao.curve_data(curve)
    x, y = data.T

    # plot it using own library
    import matplotlib.pyplot as plt
    plt.plot(x, y, label=info['name'])

plt.show()

