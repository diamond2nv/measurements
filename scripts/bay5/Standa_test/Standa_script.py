import datetime
import os.path
import sys

from measurements.libs.QPLMapper import mapper_scanners as mscan, mapper_detectors as mdet
from  measurements.libs.QPLMapper import mapper

if sys.version_info.major == 3:
    from importlib import reload

xStep = 0.5
yStep = xStep

delayBetweenPoints = 0.1
delayBetweenRows = 0.1

xLims = (0, 2)
yLims = (0, 2)

Motor = mscan.Standa(conversion_factor = 1000)

dummyAPD = mdet.dummyAPD(r"C:\Users\Daniel\Desktop")

XYscan = mapper.XYScan(scanner_axes=Motor, detectors=[dummyAPD])

XYscan.set_range(xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
XYscan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
#XYscan.run_scan()
#XYscan.plot_counts()