
import datetime
import os.path
import sys
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload
import matplotlib.pyplot as plt
import csv


d = datetime.datetime.now()
#voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
#voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 0.01
delayBetweenRows = 0.1

xLims = (-1,1)
xStep = 0.1
yLims = (1, 2)
yStep = 0.1

min_lim = -5.
max_lim = 5.


GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=min_lim, max_limit=max_lim)

#voltmeterCtrl = mdet.VoltmeterCtrl(VISA_address=r'ASRL6::INSTR')

dummyAPD = mdet.dummyAPD(r"C:\Users\Daniel\PhD\Python\measurements\libs\mapper_detectors")

# Scanning program
XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [dummyAPD])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.run_scan(silence_errors=False)
XYscan.plot_counts()

#XYscan.save_volts(XYscan.counts, voltsFilePath, flatten=True)