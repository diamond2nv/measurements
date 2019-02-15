# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 15:08:43 2019

@author: Karen
"""

import datetime
import os.path
import sys
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs.QPLMapper import mapper
if sys.version_info.major == 3:
    from importlib import reload

d = datetime.datetime.now()
CountsDirectory = r'C:\Users\Karen\Desktop\timetagger' # choose wherever you would like to save your readings
CountsFilePath = os.path.join(CountsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))# this is what your file will be called
reload(mapper)
reload(mscan)
reload(mdet)

a = 2.456 # centre of your scan in x
b = -0.70 # centre of your scan in y
d = 0.07 # distance from the centre to the edge of your scan

delayBetweenPoints = 0.02 #in seconds?
delayBetweenRows = 0.02 #in seconds?

xLims = (a-d,a+d)# explicitly states x-range
yLims = (b-d,b+d)# explicitly states y-range
xStep = 0.01 # distance between points
yStep = xStep

min_lim = -10. # minimum voltage that can be applied to the galvo
max_lim = 10. # maximum voltage that can be applied to the galvo
 
GalvoCtrl = mscan.LJTickDAC() # this is the class for using the Labjack with tick (object that controls the galvo here)
Swabianctrl = mdet.Swabian_Ctrl() # this is the class for the Swabian timetagger (object that takes the readings)

"""Initialising the Galvo scan in X and Y"""
XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [Swabianctrl]) # the galvo scan triggers and looks for a response from the detector listed
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)

"""Performing the scan"""
for i in range(0,1):
    XYscan.run_scan(silence_errors=False)
#    print('\n', i, '\n')
    
XYscan.plot_counts()
XYscan.save_to_txt(CountsFilePath,  flatten=True)
print("(Don't worry, that statement is part of a general code. It's not really volts, it's counts)")