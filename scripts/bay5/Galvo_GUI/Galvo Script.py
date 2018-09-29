"""

Aperture centre location:
    x = -0.75, y = 2.2          13/09/2018
    x = -0.5, y = 2.6           13/09/2018  (f3,f4 moved)    
    x = -0.57, y=2.345          14/09/2018  (w/ f3,f4)
    x = -0.575, y = 2.34
    x = -0.55, y = 2.35
    x = -0.68, y = 2.45         19/09/2018 (w/ f3,f4 (complete realignment))
Seems if dx and dy are not the same it throws an error, is it plotting the right way round?:
https://stackoverflow.com/questions/42687454/pcolor-data-plot-in-python#

use pcolormesh() instead of pcolor() 

"""

import datetime
import os.path
import sys
import visa
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload
import csv


d = datetime.datetime.now()
voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

reload(mapper)
reload(mscan)
reload(mdet)

delayBetweenPoints = 0.01
delayBetweenRows = 0.02

a = -0.68
b = 2.47
#d = 0.15/2
d = 0.00

xLims = (a-d,a+d)
xStep = 0.0005
yLims = (b-d, b+d)
yStep = xStep

min_lim = -5.
max_lim = 5.

GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=min_lim, max_limit=max_lim)

voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL5::INSTR')
#dummyAPD = mdet.dummyAPD(r"C:\Users\Daniel\PhD\Python\measurements\libs\mapper_detectors")


XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [voltmeterCtrl])
XYscan.set_back_to_zero = False
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.run_scan(silence_errors=False)
#XYscan.save_to_txt(voltsFilePath) 
#XYscan.save_to_hdf5(voltsFilePath)
#XYscan.plot_counts()