# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux


VERSION WITH SCANNER CONTROLLER BEING USED WITH DC INPUT VOLTAGE (NISmallBox)
"""

import pylab as py
import time
import datetime
import os.path
from pylonWeetabixTrigger import trigSender, trigReceiver, voltOut
from KeithleyMultimeter import KeithleyMultimeter
#from starlightRead import StarlightCCD
from visa import VisaIOError
    
def secondsInHMS(nbOfSeconds):
    
    hours = py.floor(nbOfSeconds / 3600)
    minutes = py.floor((nbOfSeconds - hours*3600) / 60)
    seconds = nbOfSeconds - minutes*60 - hours*3600
    
    return hours, minutes, seconds
    

SMOOTH_DELAY = 0.05  # delay between steps for smooth piezo movements


#######################
#     Parameters      #

delayBetweenPoints = 1
delayBetweenRows = 0.5

xLims = (0, 2)
xStep = 0.5

yLims = (0, 2)
yStep = 0.5

voltsDirectory = r'C:\Users\ted\Desktop\temporary_meas'
realPosDirectory = r'C:\Users\ted\Desktop\temporary_meas'

triggerSpectro = True
voltsRecord = False

#######################

# convert to Attocube DC drive voltage
toDC_drive_voltage = 1./15


# Program
d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))
realPosFilePath = os.path.join(realPosDirectory, 'realPos_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

xNbOfSteps = int(abs(py.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
xPositions = py.linspace(xLims[0], xLims[1], xNbOfSteps)

yNbOfSteps = int(abs(py.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
yPositions = py.linspace(yLims[0], yLims[1], yNbOfSteps)

totalNbOfSteps = xNbOfSteps * yNbOfSteps

realPosVarToSave = ''

try:
    # initialize instruments
    scanners_volt_drive_X = voltOut("/Weetabix/ao0")
    scanners_volt_drive_Y = voltOut("/Weetabix/ao1")

    if triggerSpectro:
        senderTask = trigSender("/Weetabix/port1/line3")
        senderTask.StartTask()
        receiverTask = trigReceiver("/Weetabix/port1/line2")
        receiverTask.StartTask()
    if voltsRecord:
        voltmeter = KeithleyMultimeter(r'ASRL15::INSTR')  
    
    # scanners.scanMode(X_ATTOAXIS, Y_ATTOAXIS)
    
    currentIndex = 0
    powerInVolts = []
    
    print 'step \tx (V)\ty (V)'
   
    
    # start main loop
    startTime = 0
    for y in yPositions:
        firstInRow = True
        for x in xPositions:
            currentIndex = currentIndex + 1
            scanners_volt_drive_X.write(toDC_drive_voltage * x)
            scanners_volt_drive_Y.write(toDC_drive_voltage * y)

            # display update
            print '{}/{} \t{:.1f} \t{:.1f}'.format(currentIndex, xNbOfSteps*yNbOfSteps, x, y)
    
            # wait for CCD 'Waiting for trigger' signal
            if triggerSpectro:
                CCDready = 0
                while CCDready == 0:
                    CCDready = receiverTask.listen()

            # elapsed time?
            if startTime == 0:
                startTime = time.time()
            if currentIndex % 20 == 0:
                elapsedTime = float(time.time() - startTime)
                remainingTime = elapsedTime / currentIndex * (totalNbOfSteps - (currentIndex-1))
                
                hoursE, minutesE, secondsE = secondsInHMS(elapsedTime)
                hoursR, minutesR, secondsR = secondsInHMS(remainingTime)
                
                print 'Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR)

            # delay between rows
            if firstInRow:
                time.sleep(delayBetweenRows)
            firstInRow = False
            
            # delay between points
            time.sleep(delayBetweenPoints) 
            
            # trigger exposure
            if triggerSpectro:
                senderTask.emit()
            
            # record volts
            if voltsRecord:
                powerInVolts.append(voltmeter.read())
            
        # end of row
        # move back to 0 smoothly
        for x in xPositions[::-1]:
            scanners_volt_drive_X.write(toDC_drive_voltage * x)
            time.sleep(SMOOTH_DELAY)
    
    # end of scan, go back to zero smoothly
    for y in yPositions[::-1]:
        scanners_volt_drive_Y.write(toDC_drive_voltage * y)
        time.sleep(SMOOTH_DELAY)
            
    
except:
    raise
finally:
    scanners_volt_drive_X.StopTask()
    scanners_volt_drive_Y.StopTask()
    if triggerSpectro:
        senderTask.StopTask()
        receiverTask.StopTask()
    if voltsRecord:
        voltmeter.close()
        py.savetxt(voltsFilePath, powerInVolts)
    
    
    