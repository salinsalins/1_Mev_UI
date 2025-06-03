# coding: utf-8
"""
Created on May 22, 2025

@author: sanin
"""

import math

import numpy
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from scipy import integrate

import PySide6

# fver = "1Q_220A_50mm"
# dir = "d:\\Your files\\Sanin\\Documents\\2024\\TRT project\\COMSOL\\"
# fname = dir + "Beam_Data_" + fver + ".txt"
# data = np.loadtxt(fname, dtype=float, comments='%', delimiter=None, skiprows=0)
#print(data)

# plt.rcParams["figure.figsize"] = [7.00, 7.00]
# plt.rcParams["figure.autolayout"] = True
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
#ax.scatter(x, y, z, c=c, alpha=1)
#plt.show()

diam = 200.0 * 2. # [mm]
radius = diam / 2.
current = 9.0 # [A]
energy = 120. # [keV]
e_charge = 1.6e-19 # [Q]
m_hminus = 1.67e-27 # [kg]
epsilon = 8.85e-12
c_light = 3e8 # [m/s]

velocity = math.sqrt(energy * 1000. * e_charge * 2./m_hminus)
beta = velocity / c_light
gamma = 1./(1. - beta*beta)
perveance = e_charge * current / (2.*math.pi*epsilon*m_hminus*2.0*(beta*gamma*c_light)**3)

data = [0,0]

a='''
1.10 0.6370
1.20 0.9082
1.30 1.1209
1.40 1.3039
1.50 1.4681
1.60 1.6193
1.70 1.7607
1.80 1.8945
1.90 2.0220
2.00 2.1444
2.10 2.2625
2.20 2.3768
2.30 2.4878
2.40 2.5960
2.50 2.7017
2.60 2.8051
2.70 2.9064
2.80 3.0058
2.90 3.1035
3.00 3.1997
3.10 3.2944
3.20 3.3877
3.30 3.4798
3.40 3.5708
3.50 3.6607
3.60 3.7495
3.70 3.8374
3.80 3.9244
3.90 4.0105
4.00 4.0958
4.10 4.1804
4.20 4.2642
4.30 4.3473
4.40 4.4298
4.50 4.5117
4.60 4.5929
4.70 4.6736
4.80 4.7537
4.90 4.8333
5.00 4.9123
5.50 5.3007
6.00 5.6788
6.50 6.0482
7.00 6.4101
7.50 6.7654
8.00 7.1148
8.50 7.4590
9.00 7.7985
9.50 8.1338
10.00 8.4651 
10.50 8.7929 
11.00 9.1173 
11.50 9.4387 
12.00 9.7573 
12.50 10.0732
13.00 10.3866
13.50 10.6976
14.00 11.0065
14.50 11.3132
15.00 11.6180
15.50 11.9209
16.00 12.2221
16.50 12.5215
17.00 12.8194
17.50 13.1156
18.00 13.4105
18.50 13.7039
19.00 13.9959
19.50 14.2867
20.00 14.5761
20.50 14.8644
21.00 15.1516
21.50 15.4376
22.00 15.7225
22.50 16.0063
23.00 16.2892
23.50 16.5711
24.00 16.8520
24.50 17.1321
25.00 17.4112
25.50 17.6894
26.00 17.9669
26.50 18.2435
27.00 18.5193
27.50 18.7943
28.00 19.0686
28.50 19.3421
29.00 19.6149
29.50 19.8871
30.00 20.1585
'''

# data = np.loadtxt(fname, dtype=float, comments='%', delimiter=None, skiprows=0)
data = np.fromstring(a, dtype=float, sep=' ')

index = np.arange(len(data)/2-1, dtype=int)

x = data[2*index]
y = data[2*index+1]

print('Perveance = ', perveance, a)

# fig, ax = plt.subplots()
#
# im = ax.imshow(dens1, cmap=matplotlib.cm.RdBu, vmin=0.0, vmax=np.max(dens1), extent=[np.min(x), np.max(x), -np.pi * radius, np.pi * radius])
# #im.set_interpolation('bilinear')
# im.set_interpolation('bicubic')
#
# cb = fig.colorbar(im, ax=ax)
#
# ax.set_title("Deposited Power Density [W/cm^2]", fontsize=14)
# plt.xlabel("Z, mm", fontsize=14)
# plt.ylabel("mm", fontsize=14)
# #ax.plot((400, 400), (600, -600))
#
# ax.set_ylim((-np.pi * radius, np.pi * radius))
# ax.set_xlim((np.min(x), np.max(x)))
# #ax.scatter(x, y, marker='.', s=0.2, linewidths=0.1, color='g')
#
# x1 = np.linspace(np.min(x), np.max(x), bins)
# y1 = np.linspace(np.min(y), np.max(y), bins)*np.pi
# plt.contour(x1, y1, dens1, levels=[100, 250])
#

def target_function_f(x):
    return 1.0 / np.sqrt(np.log(x))
# выполним интегрирование

i = 0
for d in x:
    result = integrate.quad(target_function_f, 1.0, d)
    print(i, d, result[0], (result[0]-y[i])/result[0])
    i += 1

x1 = np.linspace(1.001, 50.001, 1000)
y1 = x1.copy()*0.0
i = 0
for d in x1:
    y1[i] = integrate.quad(target_function_f, 1.0, d)[0]
    i += 1

fig, ax = plt.subplots()

ax.set_title("F function", fontsize=14)
plt.xlabel("x", fontsize=14)
plt.ylabel("F(x)", fontsize=14)
plt.grid(True)

ax.plot(x, y)
ax.plot(x1, y1)
# plt.show()

pfname = "f_function.png"
fig.savefig(pfname)

ax.clear()
ax.set_title("F^-1 function", fontsize=14)
plt.xlabel("F(x)", fontsize=14)
plt.ylabel("x", fontsize=14)
plt.grid(True)

ax.plot(y1, x1)
# plt.show()

pfname = "f_reversed_function.png"
fig.savefig(pfname)

z = np.linspace(0.,1.,100)

ax.clear()
ax.set_title("Expansion(z)", fontsize=14)
plt.ylabel("Expansion", fontsize=14)
plt.xlabel("z, mm", fontsize=14)
plt.grid(True)

ax.plot(z*1000.0, np.interp(z*math.sqrt(2.*perveance)/radius*1000., y1, x1))
# plt.show()

pfname = "Expansion_vs_z.png"
fig.savefig(pfname)

ax.clear()
ax.set_title(f'R(z). I={current}A; W={energy}keV; Ro = {radius}mm', fontsize=14)
plt.ylabel("R, mm", fontsize=14)
plt.xlabel("z, mm", fontsize=14)
plt.grid(True)

ax.plot(z*1000.0, radius*np.interp(z*math.sqrt(2.*perveance)/radius*1000., y1, x1), 'b')
plt.show()

# print(radius*np.interp(1.0*math.sqrt(2.*perveance)/radius*1000., y, x))

pfname = "R_vs_z.png"
fig.savefig(pfname)

pass