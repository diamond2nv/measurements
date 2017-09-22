# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux
"""

import pylab as py
import time
#import sys
import datetime
import os.path
from AttocubeANC300 import AttocubeANC300
#from pylonWeetabixTrigger import trigSender, trigReceiver
from Keithley import Keithley
#from starlightRead import StarlightCCD



X_ATTOAXIS = 4  # Axis number for the X piezo scanner on the ANC300
Y_ATTOAXIS = 5  # Axis number for the Y piezo scanner on the ANC300
SMOOTH_DELAY = 0.05  # delay between steps for smooth piezo movements


#######################
#     Parameters      #

delayBetweenPoints = 0.1
delayBetweenRows = 0.5

#Voltage limits scan, in x and y
xLims = (0, 55)
xStep = 1.

yLims = (0, 55)
yStep = 1.

backToZero = True  # to go back to zero at the end of the measurement 
                   # (to avoid steady high voltage on piezo)

voltsDirectory = r'C:\Users\Bay 3\Desktop\temp_measurements'

#######################

    
def secondsInHMS(nbOfSeconds):
    
    hours = py.floor(nbOfSeconds / 3600)
    minutes = py.floor(nbOfSeconds % 3600 / 60)
    seconds = nbOfSeconds - minutes*60 - hours*3600
    return hours, minutes, seconds
    

def goSmoothlyToPos(xPos, yPos, attoScanners, smoothStep=1., smoothDelay=SMOOTH_DELAY, xAxis=X_ATTOAXIS, yAxis=Y_ATTOAXIS):
    # go smoothly to a position
    currentX = attoScanners.getVoltage(X_ATTOAXIS)
    currentY = attoScanners.getVoltage(Y_ATTOAXIS)
    xSmoothNbOfSteps = int(abs(py.floor((currentX - xPos) / float(smoothStep))) + 1)
    ySmoothNbOfSteps = int(abs(py.floor((currentY - yPos) / float(smoothStep))) + 1)
    totalSmoothNbOfSteps = max((xSmoothNbOfSteps, ySmoothNbOfSteps))
    xSmoothPositions = py.append(py.linspace(currentX, xPos, xSmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - xSmoothNbOfSteps) + xPos)
    ySmoothPositions = py.append(py.linspace(currentY, yPos, ySmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - ySmoothNbOfSteps) + yPos)
    
    for x, y in zip(xSmoothPositions, ySmoothPositions):
        attoScanners.setVoltage(xAxis, x)
        attoScanners.setVoltage(yAxis, y)
        time.sleep(smoothDelay)
    

# Program
d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

xNbOfSteps = int(abs(py.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
xPositions = py.linspace(xLims[0], xLims[1], xNbOfSteps)
x_idx = np.arange(xNbOfSteps)

yNbOfSteps = int(abs(py.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
yPositions = py.linspace(yLims[0], yLims[1], yNbOfSteps)
x_idx = np.arange(xNbOfSteps)

totalNbOfSteps = xNbOfSteps * yNbOfSteps
z = np.zeros ((xNbOfSteps, yNbOfSteps))

print 'Total number of steps: {}'.format(totalNbOfSteps)
print 'X number of steps:     {}'.format(xNbOfSteps)
print 'Y number of steps:     {}'.format(yNbOfSteps)

try:
    # initialize instruments
    scanners = AttocubeANC300('COM4')
    voltmeter = Keithley(r'ASRL6::INSTR')    
    
    currentIndex = 0
    powerInVolts = []
    xPosRecord = []
    yPosRecord = []
    
    # go smoothly to start position
    goSmoothlyToPos(xPos=xLims[0], yPos=yLims[0], attoScanners=scanners)
    
    print 'step \tx (V)\ty (V)'
    
    # start main loop
    startTime = 0
    firstPoint = True
    for yi in y_idx:
        y = yPositions [yi]
        firstInRow = True
        for xi in x_idx:
            x = xPositions [xi]
            currentIndex = currentIndex + 1
            scanners.setVoltage(X_ATTOAXIS, x)
            scanners.setVoltage(Y_ATTOAXIS, y)
            
            # display update
            print('{}/{} \t{:.1f} \t{:.1f}'.format(currentIndex, xNbOfSteps*yNbOfSteps, x, y))
            
                
            # elapsed time?
            if startTime == 0:
                startTime = time.time()
            if currentIndex % 10 == 0:
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
#            
#           
            v = voltmeter.read()
            powerInVolts.append(v)
            xPosRecord.append(x)
            yPosRecord.append(y)
            z[xi, yi] = v
                
        
        # move back to first point of row smoothly
        if y != yPositions[-1]:
            for x in xPositions[::-1]:
                scanners.setVoltage(X_ATTOAXIS, x)
                time.sleep(SMOOTH_DELAY)
          
    # go smoothly to 0 if asked
    if backToZero:
        goSmoothlyToPos(xPos=0, yPos=0, attoScanners=scanners)
        
    print '\nSCAN COMPLETED'
    print 'X from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})'.format(xLims[0], xLims[1], xStep, xNbOfSteps)
    print 'Y from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})'.format(yLims[0], yLims[1], yStep, yNbOfSteps)
    print 'Total number of steps: {}'.format(totalNbOfSteps)
    
except:
    raise
finally:
    scanners.close()
#    senderTask.StopTask()
#    receiverTask.StopTask()
    voltmeter.close()

    #py.scatter (xPosRecord, yPosRecord, c = powerInVolts, s=50)
    #py.colorbar()
    #py.show()    
    py.savetxt(voltsFilePath, py.array([xPosRecord, yPosRecord, powerInVolts]).transpose())

    py.figure(figsize = (10,10))
    X, Y = py,meshgrid (xPositions, yPositions)
    py.pcolor (X, Y, z, cmap = 'RdBu')
    py.xlabel ('scanner voltage [V]', fontsize=18)
    py.ylabel ('scanner voltage [V]', fontsize=18)
    py.show()
    
    
    