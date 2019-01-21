import datetime
import os.path
import sys
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs.QPLMapper import mapper
if sys.version_info.major == 3:
    from importlib import reload
import pylab as pl
import numpy as np

d = datetime.datetime.now()
voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
reload(mapper)
reload(mscan)
reload(mdet)


a = 3.05
b = 0.21
d = 0.00
xStep = 0.005

delayBetweenPoints = 0.02
delayBetweenRows = 0.02

xLims = (a-d,a+d)
yLims = (b-d,b+d)
yStep = xStep

min_lim = -5.
max_lim = 5.


GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=min_lim, max_limit=max_lim)
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL17::INSTR')
dummyAPD = mdet.dummyAPD(voltsDirectory)

XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [voltmeterCtrl])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)

for i in range(0,0):
    XYscan.run_scan(silence_errors=False)
    print('\n', i, '\n')
XYscan.run_scan(silence_errors=False)

#XYscan.plot_counts()

#XYscan.save_to_txt(voltsFilePath,  flatten=True)

#x = np.arange(a-d, a+d, xStep)
#y = pl.loadtxt(voltsFilePath)
#if np.size(x) == np.size(y):
#    pl.plot(x,y,'o')
#else:
#    pl.plot(x, y[:np.size(y)-1],'o')
#
#
#def gaussian(x, mu, sig):
#    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))
#    print(sig*2.3548)
###
#dy = np.gradient(y)
#dx = np.linspace(0,83,np.size(y))
##
#pl.plot(dx,dy,'o')
#pl.plot(dx, 0.002*gaussian(dx, 73.3, 0.22))
#pl.plot(dx, 0.001*gaussian(dx, 22.35, 0.3))
#pl.plot(dx, 0.0025*gaussian(dx, 13.18, 0.22))
#pl.plot(dx, -0.0025*gaussian(dx, 18.4, 0.22))
#pl.xlim(0,15)