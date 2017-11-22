# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, cristian bonato


VERSION WITH SCANNER CONTROLLER BEING USED WITH DC INPUT VOLTAGE (NISmallBox)
"""

import pylab as py
import time
import datetime
import os.path
from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver, voltOut
from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
#from starlightRead import StarlightCCD
from visa import VisaIOError
from measurements.instruments import NIBox 

from measurements.libs import mapper 


SMOOTH_DELAY = 0.05  # delay between steps for smooth piezo movements

#######################
#     Parameters      #

delayBetweenPoints = 1
delayBetweenRows = 0.5

xLims = (0, 2)
xStep = 0.5

yLims = (0, 2)
yStep = 0.5

#voltsDirectory = r'C:\Users\ted\Desktop\temporary_meas'
#realPosDirectory = r'C:\Users\ted\Desktop\temporary_meas'

#######################
# convert to Attocube DC drive voltage
toDC_drive_voltage = 1./15

# APD counter integration time (ms)
ctr_time_ms = 1000
ctr_port = 'fpi0'

#######################
# instruments
attoCtrl = mapper.AttocubeNI (chX = '/Weetabix/ao0', chY = '/Weetabix/ao0')
spectroCtrl = mapper.PylonNICtrl (sender_port="/Weetabix/port1/line3",
                         receiver_port = "/Weetabix/port1/line2")

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
realPosFilePath = os.path.join(realPosDirectory, 'realPos_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
XYscan = mapper.XYscan(scanner = attoCtrl, detector = spectroCtrl)
XYscan.set_range (xLim=xLim, xStep=xStep, yLim=yLim, yStep=yStep)
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.run_scan()

