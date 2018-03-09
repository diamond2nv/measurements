# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux
"""

import pylab as py
import time
import datetime
import os.path
from AttocubeANCV1 import AttocubeANC, ANCaxis
from LockIn7265GPIB import LockIn7265
from Keithley import Keithley
#from starlightRead import StarlightCCD

    
X_ATTOAXIS = 4  # Axis number for the X piezo scanner on the ANC300
Y_ATTOAXIS = 5  # Axis number for the Y piezo scanner on the ANC300
SMOOTH_DELAY = 0.05  # delay between steps for smooth piezo movements

ANCscannersVisaAddress = r'ASRL6::INSTR'
lockinVisaAddress = r'GPIB0::14::INSTR'
voltmeterVisaAddress = r'ASRL11::INSTR'


#######################
#     Parameters      #

delayBetweenPoints = 0.5
delayBetweenRows = 0.5

xLims = (0, 2)
xStep = 1

yLims = (0, 2)
yStep = 1

nMaps = 1

backToZero = False  # to go back to zero at the end of the measurement 
                   # (to avoid steady high voltage on piezo)

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################



def secondsInHMS(nbOfSeconds):
    
    hours = py.floor(nbOfSeconds / 3600)
    minutes = py.floor(nbOfSeconds % 3600) / 60
    seconds = nbOfSeconds - minutes*60 - hours*3600
    
    return hours, minutes, seconds
    
def goSmoothlyToPos(xPos, yPos, SxAxis, SyAxis, smoothStep=1., smoothDelay=SMOOTH_DELAY):
    # go smoothly to a position
    currentX = SxAxis.getOffset()
    currentY = SyAxis.getOffset()
    xSmoothNbOfSteps = int(abs(py.floor((currentX - xPos) / float(smoothStep))) + 1)
    ySmoothNbOfSteps = int(abs(py.floor((currentY - yPos) / float(smoothStep))) + 1)
    totalSmoothNbOfSteps = max((xSmoothNbOfSteps, ySmoothNbOfSteps))
    xSmoothPositions = py.append(py.linspace(currentX, xPos, xSmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - xSmoothNbOfSteps) + xPos)
    ySmoothPositions = py.append(py.linspace(currentY, yPos, ySmoothNbOfSteps), 
                                 py.zeros(totalSmoothNbOfSteps - ySmoothNbOfSteps) + yPos)
    
    for x, y in zip(xSmoothPositions, ySmoothPositions):
        SxAxis.setOffset(x)
        SyAxis.setOffset(y)
        time.sleep(smoothDelay)
    
    
    

# Program
d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

xNbOfSteps = int(abs(py.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
xPositions = py.linspace(xLims[0], xLims[1], xNbOfSteps)

yNbOfSteps = int(abs(py.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
yPositions = py.linspace(yLims[0], yLims[1], yNbOfSteps)

totalNbOfSteps = xNbOfSteps * yNbOfSteps

atto = AttocubeANC(ANCscannersVisaAddress)
try:
    # initialize instruments
    
    SxAxis = ANCaxis(X_ATTOAXIS, atto)
    SyAxis = ANCaxis(Y_ATTOAXIS, atto)
    lockin = LockIn7265(lockinVisaAddress)
    #voltmeter = Keithley(voltmeterVisaAddress)    
    
    currentIndex = 0
    powerInVolts = []
    
    print 'step \tx (V)\ty (V)'
    
    # go smoothly to start position
    goSmoothlyToPos(xPos=xLims[0], yPos=yLims[0], SxAxis=SxAxis, SyAxis=SyAxis)

    for z in range(nMaps): 
        # start main loop
        startTime = 0
        firstPoint = True
        for y in yPositions:
            firstInRow = True
            for x in xPositions:
                currentIndex = currentIndex + 1
                SxAxis.setOffset(x)
                SyAxis.setOffset(y)
            
                # display update
                print '{}/{} \t{:.1f} \t{:.1f}'.format(currentIndex, xNbOfSteps*yNbOfSteps, x, y)
    
                # For first point wait for a reaction (when acquisition is launched in WinSpec)
                while firstPoint:
                    lockin.sendPulse()
                    time.sleep(0.1)
                    if lockin.readADCdigital():
                        break

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
                if firstPoint:
                    firstPoint = False
                else:
                    lockin.sendPulse()
            
                time.sleep(0.5)
            
                #powerInVolts.append(voltmeter.read())
            
            
                # wait for CCD 'NOT SCAN' signal
                while True:
                    if not lockin.readADCdigital():
                        break
                    time.sleep(0.1)
                
#==============================================================================
#             test = StarlightCCD(0)
#             #while True:
#             test.exposure(.01)
#             #print test.ccdParams.width,'*', test.ccdParams.height
#             res = py.array(test.pixels).reshape(test.ccdParams.height,test.ccdParams.width)
#             py.savetxt(r'C:\Users\ted\Desktop\movies\scan-lumiere\{}-{:.1f}-{:.1f}.txt'.format(currentIndex, x, y), res, delimiter='\t')
#==============================================================================
        
            # move back to 0 smoothly
            for x in xPositions[::-1]:
                SxAxis.setOffset(x)
                time.sleep(SMOOTH_DELAY)
            
            # go smoothly to start position
            if backToZero:
                goSmoothlyToPos(xPos=0, yPos=0, SxAxis=SxAxis, SyAxis=SyAxis)
    
except:
    raise
finally:
    atto.close()
    #voltmeter.close()
    lockin.close()
    
    py.plot(powerInVolts)
    py.savetxt(voltsFilePath, powerInVolts)

    
    