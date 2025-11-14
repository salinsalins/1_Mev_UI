# coding: utf-8
"""
Created on May 22, 2025

@author: sanin
"""

import json
import logging
import math
import os, sys

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import bisplrep, bisplev, LinearNDInterpolator, splrep, BSpline

from qtpy.QtWidgets import QFileDialog
from qtpy.QtWidgets import QApplication, QMainWindow, QTableWidgetSelectionRange

# Smooth by BSpline
def smooth(x, y, factor=10, s=None):
    from scipy.interpolate import splrep, BSpline
    n = len(x)
    # if s is None:
    #     s = (max(y) - min(y))^2 / len(y) 
    tck_s = splrep(x, y, s=s)
    xsm = np.arange(min(x), max(x), (max(x) - min(x)) / (len(x) - 1) / factor)
    return xsm, BSpline(*tck_s)(xsm)
  
# Filter unique data
def unique(x, y, z):
    ui = []
    for i in range(len(x)):
        x0 = x[i]
        y0 = y[i]
        if x0 != np.inf:
            ui.append(i)
            for j in range(i+1, len(x)):
                if x[j] == x0 and y[j] == y0:
                    x[j] = np.inf
    return (x[ui], y[ui], z[ui])

def select_file(file_dir=None):
    """Opens a file select dialog"""
    # define current dir
    if file_dir is None:
        file_dir = "d:\\Your files\\Sanin\\Documents\\2025\\TRT\\Отчет 2025\\"
    file_open_dialog = QFileDialog(caption='Select Log File', directory=file_dir)
    # open file selection dialog
    fn = file_open_dialog.getOpenFileName()
    # Qt4 and Qt5 compatibility workaround
    if fn is not None and len(fn) > 1:
        fn = fn[0]
    # if fn is empty
    if fn is None or fn == '':
        return ''
    return os.path.abspath(fn)

def save_fig(fig, data_file_path, suffix='', dpi=None):
    if suffix and not suffix.startswith('_'):
        suffix = '_' + suffix
    if data_file_path.endswith('.txt'):
        png_file_name = data_file_path.replace('.txt', f'{suffix}.png')
    else:
        png_file_name = data_file_path + f'{suffix}.png'
    fig.savefig(png_file_name, dpi=dpi)

def restore_settings(config, file_name='data_plot_config.json'):
    config = {}
    config.logger = logging.Logger()
    try:
        # open and read config file
        with open(file_name, 'r') as configfile:
            s = configfile.read()
        # interpret file contents by json
        config = json.loads(s)
        # restore log level
        if 'log_level' in config:
            v = config['log_level']
            config.logger.setLevel(v)
        # # restore window size and position (can be changed by user during operation)
        # if 'main_window' in obj.config:
        #     obj.resize(QSize(obj.config['main_window']['size'][0], obj.config['main_window']['size'][1]))
        #     obj.move(QPoint(obj.config['main_window']['position'][0], obj.config['main_window']['position'][1]))
        # restore widgets state
        # for w in widgets:
        #     set_widget_state(w, obj.config)
        # # OK message
        # obj.logger.log(logging.INFO, 'Configuration restored from %s' % file_name)
    except KeyboardInterrupt:
       raise
    except:
        config.logger.log(logging.WARNING, 'Configuration restore error from %s' % file_name)
        config.logger.log(logging.DEBUG, 'Exception:', exc_info=True)
    return config


def save_settings(self, widgets=(), file_name='config.json'):
    try:
        # save current window size and position
        p = self.pos()
        s = self.size()
        self.config['main_window'] = {'size': (s.width(), s.height()), 'position': (p.x(), p.y())}
        # get state of widgets
        for w in widgets:
            get_widget_state(w, self.config)
        # write to file
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(self.config, indent=4))
        # OK message
        self.logger.info('Configuration saved to %s' % file_name)
        return True
    except KeyboardInterrupt:
       raise
    except:
        self.logger.log(logging.WARNING, 'Configuration save error to %s' % file_name)
        self.logger.log(logging.DEBUG, 'Exception:', exc_info=True)
        return False


app = QApplication(sys.argv)

png_dpi = 150
plt.rcParams['figure.constrained_layout.use'] = True

data_file_dir = "d:\\Your files\\Sanin\\Documents\\2025\\TRT\\Отчет 2025\\"
data_file_name = "Power_profile_walls_1_0.95_top.txt"
data_file_path = data_file_dir + data_file_name
data_file_path = select_file(data_file_dir)
print('Data file:', data_file_path)
raw_data = np.loadtxt(data_file_path, dtype=float, comments='%', delimiter=None, skiprows=0)
x = raw_data[:,0]
y = raw_data[:,1]

# Filter and shift data
x_left = 0
x_right = 4200
y_left = 0
y_right = 1000
index_in = (x >= x_left) * (x <= x_right) * (y >= y_left) * (y <= y_right)
index_out = (x <= x_left) + (x >= x_right) + (y <= y_left) + (y >= y_right)
index_out *= (y >= 500) * (y <= 700)
# x_f = x[index_out]
x_f = x[index_in]
# y_f = y[index_out]
y_f = y[index_in]

# Plot data raw - blue, filtered - orange
fig, ax = plt.subplots()
ax.plot(x, y, 'o', color='tab:blue')
ax.plot(x_f, y_f, 'o', color='tab:orange')
ax.grid(True)
ax.grid(which='major', axis='both', linestyle='-', color='gray', linewidth=0.8, alpha=0.7)
ax.minorticks_on()
ax.grid(which='minor', axis='both', linestyle=':', color='lightgray', linewidth=0.5, alpha=0.5)
plt.suptitle(data_file_path, fontsize=8)
ax.set_title("Particles on surface", fontsize=12)
ax.set_xlabel("X, mm", fontsize=12)
ax.set_ylabel("Y, mm", fontsize=12)
fig.set_dpi(150)
plt.show()
# Save plot
if data_file_path.endswith('.txt'):
    png_file_name = data_file_path.replace('.txt', '') + '_raw_data.png'
else:
    png_file_name = data_file_path + '_raw_data.png'
fig.savefig(png_file_name, dpi=png_dpi)

# Calculate Historramm
H, xedges, yedges = np.histogram2d(x_f, y_f, bins=20)

# Calibration for power density
power = 3.5e6       # Beam power [W]
N = 14500           # Number of particles
p1 = power / N      # Power for One particle [W]
cell_area = (xedges[1]-xedges[0]) * (yedges[1]-yedges[0]) / 100. # cm**2
calibrate = p1 / cell_area  # Power density for One particle [W/cm**2]

# Display the 2D histogram using Matplotlib's pcolormesh or imshow
# plt.figure(figsize=(8, 6))
# plt.pcolormesh(xedges, yedges, H.T * calibrate, cmap='viridis') # H.T is often used for correct orientation
# plt.colorbar(label='W/cm$^2$')
# plt.xlabel('X, mm')
# plt.ylabel('Y, mm')
# plt.title('Port power density, W/cm$^2$')
# plt.show()

dx = xedges[1] - xedges[0]
dy = yedges[1] - yedges[0]
rx = xedges[-1] - xedges[0]
ry = yedges[-1] - yedges[0]
print('X range:', rx, dx, 'mm')
print('Y range:', ry, dy, 'mm')

particles = len(x_f)
print('Total particles:', particles, 'of', len(x))
total_power = power / N * particles / 1000. # 'kW'
print('Total power (filtered):', total_power, 'kW')
print('Maximal power density:', np.max(H * calibrate) / 1000., 'kW/cm**2')
area = rx * ry / 100. # 'cm**2'
print('Area:', area, 'cm**2')
print('Averae power density:', total_power / area, 'kW/cm**2')

# Plot histogramm 
extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]]
ratio = rx / ry
p_h = 3
p_w = int(p_h * ratio * 0.8)
print(p_w, p_h)
# p_w = 3
p_w = 12
print(p_w, p_h)
fig, ax = plt.subplots(layout="constrained")
# fig.set_size_inches(p_w, p_h)
# fig.set_dpi(150)
im = ax.imshow(H.T * calibrate, cmap=matplotlib.cm.gnuplot2, extent=extent, interpolation='bicubic')
# im.set_interpolation('bicubic')
plt.suptitle(data_file_path, fontsize=6)
ax.set_title("Power Density Profile, W/cm$^2$", fontsize=12)
ax.set_xlabel("X , mm", fontsize=12)
ax.set_ylabel("Y , mm", fontsize=12)
ax.grid(which='major', axis='both', linestyle='-', color='red', linewidth=0.4, alpha=0.5)
cb = plt.colorbar(im)
# cb = plt.colorbar(im, shrink=0.75)

# width, height = fig.canvas.get_width_height()

# xd = [np.min(x_f), np.max(x_f)] 
# yd = [np.min(y_f), np.max(y_f)] 
# xy_pixels = ax.transData.transform(np.vstack([xd,yd]).T)
# rdx=xy_pixels[0][1] - xy_pixels[0][0]
# rdy=xy_pixels[1][1] - xy_pixels[1][0]

# if rx/rdx/1.2 > ry/rdy:
#     p_w = p_w * ry/rdy/rx*rdx
# fig.set_size_inches(p_w, p_h)
dpi_fig = fig.get_dpi()
bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
width = bbox.width * fig.dpi
height = bbox.height * fig.dpi
width_inches = bbox.width
axis_width_pixels = width_inches * dpi_fig
print(f"Figure DPI: {dpi_fig}")
print(f"Axis width in inches: {width_inches:.2f}")
print(f"Axis width in pixels: {axis_width_pixels:.2f}")
print(f"Axis height in pixels: {height:.2f}")
fig_bbox = fig.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
# if bbox.xmin > 0.:
#     fig.set_size_inches(p_w - bbox.xmin, p_h)
plt.show()
# plt.close()

# fig, ax = plt.subplots((p_w - bbox.xmin, p_h), layout="constrained")
# # fig.set_size_inches(p_w - bbox.xmin, p_h)
# im = ax.imshow(H.T * calibrate, cmap=matplotlib.cm.gnuplot2, extent=extent, interpolation='bicubic')
# # im.set_interpolation('bicubic')
# plt.suptitle(data_file_path, fontsize=6)
# ax.set_title("Power Density Profile, W/cm$^2$", fontsize=12)
# ax.set_xlabel("X , mm", fontsize=12)
# ax.set_ylabel("Y , mm", fontsize=12)
# ax.grid(which='major', axis='both', linestyle='-', color='red', linewidth=0.4, alpha=0.5)
# cb = plt.colorbar(im)

# plt.show()

# Save plot
if data_file_path.endswith('.txt'):
    png_file_name = data_file_path.replace('.txt', '.png')
else:
    png_file_name = data_file_path + '.png'
fig.savefig(png_file_name, dpi=png_dpi)

exit(0)


data_file_name = "d:\\Your files\\Sanin\\Documents\\2025\\TRT\\Отчет 2025\\Power_profile.txt"
data_folder = os.path.dirname(data_file_name)

data = np.loadtxt(data_file_name, dtype=float, comments='%', delimiter=None, skiprows=0)
x = data[:,0]
y = data[:,1]
z = data[:,2]

x, y, z = unique(x, y, z)

interp = LinearNDInterpolator(list(zip(x, y)), z)

x1 = np.linspace(-200, 200, 40)
y1 = interp(x1, x1*0.0)
y2 = interp(x1*0.0, x1)

# Smooth
s = 0.000001
tck_s1 = splrep(x1, y1, s=s)
tck_s2 = splrep(x1, y2, s=s)
xsm = np.arange(min(x1), max(x1), (max(x1)-min(x1))/(len(x1)-1)/10)

# print(1./len(xsm), s1)

fig, ax = plt.subplots()

# ax.plot(xx, yy * power / 1000., 'o', color='tab:blue')
# plt.show()

ax.plot(x1, y1 * power / 1000., 'o', color='tab:blue')
ax.plot(xsm, BSpline(*tck_s1)(xsm) * power / 1000., '-', label='Vertical', color='tab:blue')
ax.plot(x1, y2 * power / 1000., 'o', color='tab:orange')
ax.plot(xsm, BSpline(*tck_s2)(xsm) * power / 1000., '-', label='Horizontal', color='tab:orange')

# Customization

# Change the size of the existing figure
fig.set_size_inches(8, 8)
fig.set_dpi(150)

# Add a basic grid
ax.grid(True)

# Customize the grid for major ticks
ax.grid(which='major', axis='both', linestyle='-', color='gray', linewidth=0.8, alpha=0.7)

# Add minor ticks and a minor grid
ax.minorticks_on()
ax.grid(which='minor', axis='both', linestyle=':', color='lightgray', linewidth=0.5, alpha=0.5)

# Add labels and a title
ax.set_title("Power Density Profile, kW/cm$^2$", fontsize=14)
ax.set_xlabel("X, mm", fontsize=14)
ax.set_ylabel("Power density, kW/cm$^2$", fontsize=14)

# Add a legend
ax.legend()


# ax.plot(x1, y1 * power / 1000., 'o-', label='data')

x2 = np.linspace(-200, 200, 40)
y2 = interp(x2*0.0, x2)
# ax.plot(x2, y2 * power / 1000., 'o-', label='data')

plt.show()

# Image plot
fig, ax = plt.subplots()
fig.set_dpi(150)

xmin = -200
xmax = 200
dx = 40
xx = np.linspace(xmin, xmax, dx)
n = len(xx)
idata = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        idata[i, j] = interp(xx[i], xx[j])

im = ax.imshow(idata * power / 1000, cmap=matplotlib.cm.gnuplot2, extent=[xmin, xmax, xmin, xmax])
#im = ax.imshow(idata, cmap=matplotlib.cm.RdBu, extent=[xmin, xmax, xmin, xmax])
# im.set_interpolation('bilinear')
im.set_interpolation('bicubic')
cb = fig.colorbar(im, ax=ax)
# ax.plot((xmin, xmax), (xmin, xmax))
ax.set_title("Port Power Density Profile, kW/cm$^2$", fontsize=14)
ax.set_xlabel("X - horizontal, mm", fontsize=14)
ax.set_ylabel("Y - vertical, mm", fontsize=14)
ax.grid(which='major', axis='both', linestyle='-', color='red', linewidth=0.4, alpha=0.5)
plt.show()

# Scatter plot
# ax.set_ylim((-np.pi * radius, np.pi * radius))
# ax.set_xlim((np.min(x), np.max(x)))
# ax.scatter(x, y, marker='.', s=0.2, linewidths=0.1, color='g')

# Contour plot
# x1 = np.linspace(np.min(x), np.max(x), bins)
# y1 = np.linspace(np.min(y), np.max(y), bins)*np.pi
# plt.contour(x1, y1, dens1, levels=[100, 250])

# Power_density(r) plot

# average density vs r
import scipy.integrate as integrate

fig, ax = plt.subplots()
fig.set_dpi(150)
ax.grid(True)
ax.grid(which='major', axis='both', linestyle='-', color='gray', linewidth=0.8, alpha=0.7)
ax.minorticks_on()
ax.grid(which='minor', axis='both', linestyle=':', color='lightgray', linewidth=0.5, alpha=0.5)
ax.set_title("Average Power Density for Radius, kW/cm$^2$", fontsize=14)
ax.set_xlabel("Radius, mm", fontsize=14)
ax.set_ylabel("Power density, kW/cm$^2$", fontsize=14)
r = np.arange(10, 200, 10)
pr = np.arange(10., 200., 10.)
for i in range(len(r)):
    pr[i] = 2.0/r[i]/r[i] * integrate.quad(lambda x: (BSpline(*tck_s1)(x) + BSpline(*tck_s2)(x) + BSpline(*tck_s1)(-x) + BSpline(*tck_s2)(-x)) / 4 * x, 0, r[i])[0]

ax.plot(r, pr * power / 1000., 'o-', color='tab:red')

plt.show()

# Save plot
# file_name = "R_vs_z.png"
# fig.savefig(file_name)


pass

