import datetime
import os.path
import sys
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs import mapper
if sys.version_info.major == 3:
    from importlib import reload

d = datetime.datetime.now()
voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
reload(mapper)
reload(mscan)
reload(mdet)

a = 1
b = 2
d = 0
xStep = 0.4
delayBetweenPoints = 1
delayBetweenRows = 1

xLims = (a,a)
yLims = (b,b)
yStep = xStep

min_lim = -10.
max_lim = 10.
 
GalvoCtrl = mscan.LJTickDAC()
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL7::INSTR')
XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [voltmeterCtrl])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)

for i in range(0,0):
    XYscan.run_scan(silence_errors=False)
    print('\n', i, '\n')
XYscan.run_scan(silence_errors=False)

#XYscan.plot_counts()

#XYscan.save_to_txt(voltsFilePath,  flatten=True)