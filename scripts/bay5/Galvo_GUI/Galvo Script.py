import datetime
import os.path
import sys
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs.QPLMapper import mapper
if sys.version_info.major == 3:
    from importlib import reload

d = datetime.datetime.now()
voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
reload(mapper)
reload(mscan)
reload(mdet)


a = 3.3145
b = -0.1985
d = 0.005
xStep = 0.0001

delayBetweenPoints = 0.05
delayBetweenRows = 0.05

xLims = (a-d,a+d)
yLims = (b-d,b+d)
yStep = xStep

#attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL4::INSTR', chX=0, chY=5)
GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=-5., max_limit=5.)
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL13::INSTR')
dummyAPD = mdet.dummyAPD(voltsDirectory)

XYscan = mapper.XYScan(scanner_axes = GalvoCtrl, detectors= [voltmeterCtrl])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)

for i in range(0,0):
    XYscan.run_scan(silence_errors=False)
    print('\n', i, '\n')
XYscan.run_scan(silence_errors=False)

XYscan.plot_counts()

#XYscan.save_to_txt(voltsFilePath,  flatten=True)