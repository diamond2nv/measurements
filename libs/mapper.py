# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 09:23:52 2017

@author: cristian bonato
"""

import pylab as py
import time
import datetime
import os.path
#from measurements.instruments.AttocubeANC300 import AttocubeANC300
from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver, voltOut
from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
#from measurements.instruments.Keithley import Keithley
#from measurements.instruments.LockIn7265GPIB import LockIn7265
from measurements.instruments import NIBox
from tools import data_object as DO 

reload (NIBox)

class DetectorCtrl ():

	def __init__(self, work_folder):
		self._wfolder = work_folder

	def initialize (self):
		pass

	def readout (self):
		pass

	def wait_for_ready (self):
		pass

	def first_point (self):
		pass

class ScannerCtrl ():

    def __init__(self):
        pass

    def moveX (self, value):
        pass

    def moveY (self, value):
        pass

    def getX (self):
        pass

    def getY (self):
        pass

    def goSmoothlyToPos(self, xPos, yPos):
        currX = self.getX()
        currY = self.getY()

        xSmooth_nr_steps = int(abs(py.floor((currX - xPos) / float(self.smooth_step))) + 1)
        ySmooth_nr_steps = int(abs(py.floor((currY - yPos) / float(self.smooth_step))) + 1)

        totalSmoothNbOfSteps = max((xSmooth_nr_steps, ySmooth_nr_steps))
        xSmoothPositions = py.append(py.linspace(currX, xPos, xSmooth_nr_steps), py.zeros(totalSmoothNbOfSteps - xSmooth_nr_steps) + xPos)
        ySmoothPositions = py.append(py.linspace(currY, yPos, ySmooth_nr_steps), py.zeros(totalSmoothNbOfSteps - ySmooth_nr_steps) + yPos)

        for x, y in zip(xSmoothPositions, xSmoothPositions):
            self.moveX(x)
            self.moveY(y)
            time.sleep(self.smooth_delay)

class AttocubeNI (ScannerCtrl):

    def __init__ (self, chX = '/Weetabix/ao0', chY = '/Weetabix/ao1', conversion_factor=1/15.):
        self._chX = chX
        self._chY = chY
        self.conversion_factor = conversion_factor

        self.smooth_step = 1
        self.smooth_delay = 0.05

        self._currX = 0
        self._currY = 0

    def initialize (self):
        self.scanners_volt_drive_X = voltOut(self._chX)
        self.scanners_volt_drive_Y = voltOut(self._chY)

    def moveX (self, value):
        self.scanners_volt_drive_X.write(self.conversion_factor * value)
        self._currX = value

    def moveY (self, value):
        self.scanners_volt_drive_Y.write(self.conversion_factor * value)
        self._currY = value

    def close(self):
        self.scanners_volt_drive_X.StopTask()
        self.scanners_volt_drive_Y.StopTask()

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY


class PylonNICtrl (DetectorCtrl):

    def __init__(self, work_folder, sender_port="/Weetabix/port1/line3", receiver_port = "/Weetabix/port1/line2"):
        self._wfolder = work_folder
        self._sender_port = sender_port
        self._receiver_port = receiver_port
        self.delay_after_readout = 0.

    def initialize (self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def wait_for_ready (self):
        CCDready = 0
        while CCDready == 0:
            CCDready = self.receiverTask.listen()

    def readout (self):
    	self.senderTask.emit()
        return 0

    def close(self):
        self.senderTask.StopTask()
        self.receiverTask.StopTask()

class LockinCtrl (DetectorCtrl):

    def __init__(self, work_folder, lockinVisaAddress):
        self._wfolder = work_folder
        self._lockin = LockIn7265(lockinVisaAddress)
        self.delay_after_readout = 0.5

    def first_point (self):
        while True:
            self.lockin.sendPulse()
            time.sleep(0.1)
            if lockin.readADCdigital():
                break

    def wait_for_ready (self):
        while True:
            if not lockin.readADCdigital():
                break
            time.sleep(0.1)

    def readout (self):
        self.lockin.sendPulse()
        return 0

    def close(self):
        self.lockin.close()


class APDCounterCtrl (DetectorCtrl):

    def __init__(self, work_folder, ctr_port):
        self._wfolder = work_folder
        self._ctr_port = ctr_port

    def initialize (self):
        self._ctr = NIBox.NIBoxCounter(dt=ctr_time_ms)
        self._ctr.set_port (ctr_port)
        self._ctr.start()

    def readout (self):
        c = self._ctr.get_counts ()
        return c

    def close (self):
        self._ctr.stop()
        self._ctr.clear()

class XYScan ():

    def __init__(self, scanner = None, detector = None, voltmeter = None):
        self._scanner = scanner
        self._detector = detector
        self._voltmeter = voltmeter

        self.delayBetweenPoints = 1
        self.delayBetweenRows = 0.5

        self._back_to_zero = False

        # Check what kind of detector is used (spectrometer or apd)
        if (isinstance (detector, PylonNICtrl) or isinstance (detector, LockinCtrl)):
            self.detector_type = 'spectro'
        elif (isinstance (detector, APDCounterCtrl)):
            self.detector_type = 'apd'
        else:
            self.detector_type = 'unknown'

    def set_delays (self, between_points, between_rows):
        self.delayBetweenPoints = between_points
        self.delayBetweenRows = between_rows

    def restore_back_to_zero(self):
        self._back_to_zero = True

    def set_range (self, xLims, xStep, yLims, yStep):

        self.xNbOfSteps = int(abs(py.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
        self.xPositions = py.linspace(xLims[0], xLims[1], self.xNbOfSteps)
        self.yNbOfSteps = int(abs(py.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
        self.yPositions = py.linspace(yLims[0], yLims[1], self.yNbOfSteps)
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps

        if (self.detector_type=='apd'):
            self.counts = py.zeros (self.xNbOfSteps, self.yNbOfSteps)

        if (self._voltmeter):
            self.powerInVolts = py.zeros (self.xNbOfSteps, self.yNbOfSteps)

    def secondsInHMS(self, nbOfSeconds):
        hours = py.floor(nbOfSeconds / 3600)
        minutes = py.floor(nbOfSeconds % 3600) / 60
        seconds = nbOfSeconds - minutes*60 - hours*3600
        return hours, minutes, seconds

    def print_elapsed_time (self, startTime, currentIndex):
        if startTime == 0:
            startTime = time.time()
            if currentIndex % 20 == 0:
                elapsedTime = float(time.time() - startTime)
                remainingTime = elapsedTime / currentIndex * (totalNbOfSteps - (currentIndex-1))

                hoursE, minutesE, secondsE = secondsInHMS(elapsedTime)
                hoursR, minutesR, secondsR = secondsInHMS(remainingTime)

                print 'Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR)
        return startTime

    def run_scan (self):

        try:
            self._detector.initialize()
            self._scanner.initialize()

            startTime = 0
            firstPoint = True
            idx = 0

            for id_y in range(self.yNbOfSteps): 
                y = self.yPositions[id_y]
                firstInRow = True
                for id_x in range(self.xNbOfSteps):
                    x = self.xPositions[id_x]
                    idx += 1
                    self._scanner.moveX(x)
                    self._scanner.moveY(y)

                    # display update
                    print '{}/{} \t{:.1f} \t{:.1f}'.format(idx, 
                                    self.xNbOfSteps*self.yNbOfSteps, x, y)

                    # For first point may wait for a reaction 
                    # (when acquisition is launched in WinSpec)
                    if firstPoint:
                        self._detector.first_point()
                        firstPoint = False

                    startTime = self.print_elapsed_time(startTime = startTime, currentIndex = idx)

                    # delay between rows
                    if firstInRow:
                        time.sleep(self.delayBetweenRows)
                        firstInRow = False

                    # delay between points
                    time.sleep(self.delayBetweenPoints)

                    # trigger exposure
                    if firstPoint:
                        firstPoint = False
                    else:
                        c = self._detector.readout()
                        if (self.detector_type=='apd'):
                            self.counts[id_x, id_y] = c
                        if (self._voltmeter):
                            self.powerInVolts[id_x, id_y] = self._voltmeter.read()


                    time.sleep(self._detector.delay_after_readout)

                    #powerInVolts.append(voltmeter.read())

                    # wait for CCD 'NOT SCAN' signal
                    self._detector.wait_for_ready()

                # move back to 0 smoothly
                for x in self.xPositions[::-1]:
                    self._scanner.moveX(x)
                    time.sleep(self._scanner.smooth_delay)          

            # go smoothly to start position
            if self._back_to_zero:
                self._scanner.goSmoothlyToPos(xPos=0, yPos=0)
        except:
            raise

        finally:
            self._scanner.close()
            self._detector.close()
            if (self._voltmeter):
                self._voltmeter.close()

    def save_to_hdf5 (self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print ("File saved")




