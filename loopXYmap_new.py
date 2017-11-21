# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux
"""

import pylab as py
import time
import datetime
import os.path
from AttocubeANCV1 import AttocubeANC, ANCError
from pylonWeetabixTrigger import trigSender, trigReceiver
from KeithleyMultimeter import KeithleyMultimeter
#from starlightRead import StarlightCCD
from visa import VisaIOError
    
def secondsInHMS(nbOfSeconds):
    
    hours = py.floor(nbOfSeconds / 3600)
    minutes = py.floor((nbOfSeconds - hours*3600) / 60)
    seconds = nbOfSeconds - minutes*60 - hours*3600
    
    return hours, minutes, seconds
    

X_ATTOAXIS = 4  # Axis number for the X piezo scanner on the ANC300
Y_ATTOAXIS = 5  # Axis number for the Y piezo scanner on the ANC300
SMOOTH_DELAY = 0.05  # delay between steps for smooth piezo movements


#######################
#     Parameters      #

delayBetweenPoints = 0
delayBetweenRows = 0.5

xLims = (0, 25)
xStep = 0.5

yLims = (0, 25)
yStep = 0.5

voltsDirectory = r'C:\Users\ted\Desktop\temporary_meas'
realPosDirectory = r'C:\Users\ted\Desktop\temporary_meas'

triggerSpectro = True
voltsRecord = False
realPosRecord = True

#######################


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
    scanners = AttocubeANC('ASRL4::INSTR')
    if triggerSpectro:
        senderTask = trigSender("/SmallNIbox/port1/line3")
        senderTask.StartTask()
        receiverTask = trigReceiver("/SmallNIbox/port1/line2")
        receiverTask.StartTask()
    if voltsRecord:
        voltmeter = KeithleyMultimeter(r'ASRL15::INSTR')  
    
    scanners.scanMode(X_ATTOAXIS, Y_ATTOAXIS)
    
    currentIndex = 0
    powerInVolts = []
    
    print 'step \txT (V)\tyT (V) \txR (V)\tyR (V)  (T = target, R = real)'
    
    
    # go smoothly to start position
    currentX = scanners.getOffset(X_ATTOAXIS)[0]
    currentY = scanners.getOffset(Y_ATTOAXIS)[0]
    smoothStep = 1.
    xSmoothNbOfSteps = int(abs(py.floor((currentX - xLims[0]) / float(smoothStep))) + 1)
    ySmoothNbOfSteps = int(abs(py.floor((currentY - yLims[0]) / float(smoothStep))) + 1)
    totalSmoothNbOfSteps = max((xSmoothNbOfSteps, ySmoothNbOfSteps))
    xSmoothPositions = py.append(py.linspace(currentX, xLims[0], xSmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - xSmoothNbOfSteps) + xLims[0])
    ySmoothPositions = py.append(py.linspace(currentY, yLims[0], ySmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - ySmoothNbOfSteps) + yLims[0])
    
    for x, y in zip(xSmoothPositions, ySmoothPositions):
        while True:
            try:
                scanners.setOffset(x, X_ATTOAXIS)
                scanners.setOffset(y, Y_ATTOAXIS)
            except (ANCError, VisaIOError) as error:
                print error
                time.sleep(1)
            else:
                break
        time.sleep(SMOOTH_DELAY)
    
    
    # start main loop
    startTime = 0
    for y in yPositions:
        firstInRow = True
        for x in xPositions:
            currentIndex = currentIndex + 1
            while True:
                try:
                    scanners.setOffset(x, X_ATTOAXIS)
                    scanners.setOffset(y, Y_ATTOAXIS)
                except (ANCError, VisaIOError) as error:
                    print error
                    time.sleep(1)
                else:
                    break
            
            while True:
                try:
                    xReal, yReal = scanners.getOffset(X_ATTOAXIS, Y_ATTOAXIS)
                except (ANCError, VisaIOError) as error:
                    print error
                    time.sleep(1)
                else:
                    break
            
            realPosVarToSave += '{:.1f} \t{:.1f} \t{:.1f} \t{:.1f}\n'.format(x, y, xReal, yReal)
            
            # display update
            print '{}/{} \t{:.1f} \t{:.1f} \t{:.1f} \t{:.1f}'.format(currentIndex, xNbOfSteps*yNbOfSteps, x, y, xReal, yReal)
    
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
            while True:
                try:
                    scanners.setOffset(x, X_ATTOAXIS)
                except (ANCError, VisaIOError) as error:
                    print error
                    time.sleep(1)
                else:
                    break
            time.sleep(SMOOTH_DELAY)
    
    # end of scan, go back to zero smoothly
    for y in yPositions[::-1]:
        while True:
            try:
                scanners.setOffset(y, Y_ATTOAXIS)
            except (ANCError, VisaIOError) as error:
                print error
                time.sleep(1)
            else:
                break
        time.sleep(SMOOTH_DELAY)
            
    
except:
    raise
finally:
    scanners.close()
    if triggerSpectro:
        senderTask.StopTask()
        receiverTask.StopTask()
    if voltsRecord:
        voltmeter.close()
        py.savetxt(voltsFilePath, powerInVolts)
    if realPosRecord:
        with open(realPosFilePath, 'w') as posFile:
            posFile.write(realPosVarToSave)
    
    
    