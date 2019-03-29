import datetime
import os.path
import numpy as np
import sys
from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs.QPLMapper import mapper
if sys.version_info.major == 3:
    from importlib import reload

d = datetime.datetime.now()
voltsDirectory = r'C:\Users\ted\Dropbox (Heriot-Watt University Team)\RES_EPS_Quantum_Photonics_Lab\Setups\Bay5-LT\Two spot microscope\Power stability measuremnet'
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
reload(mapper)
reload(mscan)
reload(mdet)

xStep = 1

delayBetweenPoints = 60 #seconds
delayBetweenRows = 1 # seconds

xLims = (0,720)
yLims = (0,0)
yStep = xStep

dummyscanner =mscan.TestScanner()
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL13::INSTR')

XYscan = mapper.XYScan(scanner_axes = dummyscanner, detectors= [voltmeterCtrl])
XYscan.set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints,between_rows = delayBetweenRows)

XYscan.run_scan(silence_errors=False)

y = XYscan.detector_readout_0.flatten()
x = np.arange(0,len(y)*delayBetweenPoints,delayBetweenPoints)
np.savetxt(voltsFilePath,np.transpose([x,y]))