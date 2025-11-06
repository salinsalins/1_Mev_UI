# coding: utf-8
"""
Created on May 22, 2025

@author: sanin
"""

import math
import os
import PyQt6

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import bisplrep, bisplev, LinearNDInterpolator, splrep, BSpline

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

data_file_name = "d:\\Your files\\Sanin\\Documents\\2025\\TRT\\Отчет 2025\\Power_profile.txt"
data_folder = os.path.dirname(data_file_name)

data = np.loadtxt(data_file_name, dtype=float, comments='%', delimiter=None, skiprows=0)
x = data[:,0]
y = data[:,1]
z = data[:,2]

power = 3.5e6 # Beam power [W]

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
fig.set_size_inches(8, 4)

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


# Image plot
# im = ax.imshow(x, y, z)
# im = ax.imshow(data, cmap=matplotlib.cm.RdBu, vmin=0.0, vmax=np.max(data), extent=[np.min(x), np.max(x), -np.pi * radius, np.pi * radius])
# im.set_interpolation('bilinear')
# im.set_interpolation('bicubic')
# cb = fig.colorbar(im, ax=ax)

# ax.plot((400, 400), (600, -600))

# ax.set_ylim((-np.pi * radius, np.pi * radius))
# ax.set_xlim((np.min(x), np.max(x)))
# ax.scatter(x, y, marker='.', s=0.2, linewidths=0.1, color='g')

# x1 = np.linspace(np.min(x), np.max(x), bins)
# y1 = np.linspace(np.min(y), np.max(y), bins)*np.pi
# plt.contour(x1, y1, dens1, levels=[100, 250])


plt.show()

# Second plot

# average density (r)
import scipy.integrate as integrate

fig, ax = plt.subplots()
fig.set_dpi(150)
ax.grid(True)
ax.grid(which='major', axis='both', linestyle='-', color='gray', linewidth=0.8, alpha=0.7)
ax.minorticks_on()
ax.grid(which='minor', axis='both', linestyle=':', color='lightgray', linewidth=0.5, alpha=0.5)
ax.set_title("Average Power Density for Radius, kW/cm$^2$", fontsize=14)
ax.set_xlabel("r, mm", fontsize=14)
ax.set_ylabel("Power density, kW/cm$^2$", fontsize=14)
r = np.arange(10, 200, 10)
pr = np.arange(10., 200., 10.)
for i in range(len(r)):
    pr[i] = 2.0/r[i]/r[i] * integrate.quad(lambda x: BSpline(*tck_s1)(x) * x, 0, r[i])[0]

ax.plot(r, pr * power / 1000., 'o-', color='tab:red')

plt.show()

# Save plot
# file_name = "R_vs_z.png"
# fig.savefig(file_name)




pass

