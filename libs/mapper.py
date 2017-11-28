# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 09:23:52 2017

@author: cristian bonato
"""

import pylab as pl
import time
import datetime
import os.path
import sys
import visa

from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver, voltOut
from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
#from measurements.instruments.LockIn7265GPIB import LockIn7265
from measurements.instruments import NIBox
from measurements.instruments import AttocubeANCV1 as attoANC
from tools import data_object as DO 

if sys.version_info.major == 3:
    from importlib import reload

reload (NIBox)

class DetectorCtrl ():

    def __init__(self, work_folder):
        self._wfolder = work_folder
        self.delay_after_readout = 0.

    def initialize (self):
        pass

    def readout (self):
        return None

    def wait_for_ready (self):
        pass

    def first_point (self):
        pass

    def close(self):
       pass

class ScannerCtrl ():

    def __init__(self):
        self.smooth_step = 1
        self.smooth_delay = 0.05

    def initialize(self):
        pass

    def moveX (self, value):
        pass

    def moveY (self, value):
        pass

    def getX (self):
        return None

    def getY (self):
        return None

    def close(self):
        pass

    def goSmoothlyToPos(self, xPos, yPos):
        currX = self.getX()
        currY = self.getY()

        xSmooth_nr_steps = int(abs(pl.floor((currX - xPos) / float(self.smooth_step))) + 1)
        ySmooth_nr_steps = int(abs(pl.floor((currY - yPos) / float(self.smooth_step))) + 1)

        totalSmoothNbOfSteps = max((xSmooth_nr_steps, ySmooth_nr_steps))
        xSmoothPositions = pl.append(pl.linspace(currX, xPos, xSmooth_nr_steps), pl.zeros(totalSmoothNbOfSteps - xSmooth_nr_steps) + xPos)
        ySmoothPositions = pl.append(pl.linspace(currY, yPos, ySmooth_nr_steps), pl.zeros(totalSmoothNbOfSteps - ySmooth_nr_steps) + yPos)

        for x, y in zip(xSmoothPositions, xSmoothPositions):
            self.moveX(x)
            self.moveY(y)
            time.sleep(self.smooth_delay)

class AttocubeNI (ScannerCtrl):

    def __init__ (self, chX='/Weetabix/ao0', chY='/Weetabix/ao1', conversion_factor=1/15.):
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

class AttocubeVISA (ScannerCtrl):

    def __init__ (self, VISA_address, axisX=1, axisY=2):
        self._VISA_address = VISA_address
        self._axisX = axisX
        self._axisY = axisY

        self.smooth_step = 0.5
        self.smooth_delay = 0.05

        self._currX = 0
        self._currY = 0


    def initialize (self):
        try:
            self._ANChandle = attoANC.AttocubeANC(self._VISA_address)
        except visa.VisaIOError as err:
            if int(err.error_code) == -1073807343:
                print('\n##########  ATTENTION: '+
                      'Address of the Attocube ANC does not match any device. You should' +
                      ' check the address of the device or reset it.\n')
                raise
                
            elif int(err.error_code) == -1073807246:
                print('\n##########  ATTENTION: ' +
                      'The Attocube ANC is busy. Did you close any other program using it?\n')
                raise
            else:
                raise 

    def moveX (self, value):
        self._ANChandle.setOffset(value, self._axisX)
        self._currX = value

    def moveY (self, value):
        self._ANChandle.setOffset(value, self._axisY)
        self._currY = value

    def close(self):
        try:
            self._ANChandle.close()
        except:
            pass

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


class ActonNICtrl (DetectorCtrl):

    def __init__(self, sender_port, receiver_port):
        self._sender_port = sender_port
        self._receiver_port = receiver_port
        self.delay_after_readout = 0.5

    def initialize (self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def first_point (self):
        while True:
            self.senderTask.emit()
            time.sleep(0.1)
            if self.receiverTask.listen():
                break

    def wait_for_ready (self):
        # wait for CCD 'NOT SCAN' signal
        while True:
            if self.receiverTask.listen():
                break
        # time.sleep(0.5)
        while True:
            if not self.receiverTask.listen():
                break

    def readout (self):
        self.senderTask.emit()
        return 0

    def close(self):
        self.senderTask.StopTask()
        self.receiverTask.StopTask()


class ActonLockinCtrl (DetectorCtrl):

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
        self.delay_after_readout = 0.
        
    def set_integration_time_ms (self, t):
        self._ctr_time_ms = t

    def initialize (self):
        self._ctr = NIBox.NIBoxCounter(dt=self._ctr_time_ms)
        self._ctr.set_port (self._ctr_port)

    def readout (self):
        self._ctr.start()
        c = self._ctr.get_counts ()
        self._ctr.stop()

        return c

    def close (self):
        self._ctr.clear()

class VoltmeterCtrl (DetectorCtrl):

    def __init__(self, VISA_address):
        self._VISA_address = VISA_address
        self.delay_after_readout = 0.

    def initialize (self):
        try:
            self._voltmeter = KeithleyMultimeter(self._VISA_address)  
        except:
            raise Exception('The Keithley Voltmeter could not be initialized. Did you close any other programs using it?')

    def readout (self):
        return self._voltmeter.read()

    def close (self):
        self._voltmeter.close()

class XYScan ():

    def __init__(self, scanner = None, detector = None, voltmeter = None):
        self._scanner = scanner
        self._detector = detector
        self._voltmeter = voltmeter

        self.delayBetweenPoints = 1
        self.delayBetweenRows = 0.5

        self._back_to_zero = False

        # Check what kind of detector is used (spectrometer or apd)
        if (isinstance (detector, PylonNICtrl) or isinstance (detector, ActonLockinCtrl) or isinstance (detector, ActonNICtrl)):
            self.detector_type = 'spectro'
        elif (isinstance (detector, APDCounterCtrl)):
            self.detector_type = 'apd'
        else:
            self.detector_type = 'unknown'

    def set_delays (self, between_points, between_rows):
        self.delayBetweenPoints = between_points
        self.delayBetweenRows = between_rows

    def set_back_to_zero(self):
        # to go back to 0 V at the end of a scan
        self._back_to_zero = True

    def set_range (self, xLims, xStep, yLims, yStep):

        self.xNbOfSteps = int(abs(pl.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
        self.xPositions = pl.linspace(xLims[0], xLims[1], self.xNbOfSteps)
        self.yNbOfSteps = int(abs(pl.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
        self.yPositions = pl.linspace(yLims[0], yLims[1], self.yNbOfSteps)
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps
        self.xStep = xStep
        self.yStep = yStep

        if (self.detector_type=='apd'):
            self.counts = pl.zeros ([self.xNbOfSteps, self.yNbOfSteps])

        if self._voltmeter is not None:
            self.powerInVolts = pl.zeros ([self.xNbOfSteps, self.yNbOfSteps])

    def secondsInHMS(self, nbOfSeconds):
        hours = pl.floor(nbOfSeconds / 3600)
        minutes = pl.floor(nbOfSeconds % 3600 / 60)
        seconds = nbOfSeconds - minutes*60 - hours*3600
        return hours, minutes, seconds

    def print_elapsed_time (self, startTime, currentIndex, totalNbOfSteps):
        elapsedTime = float(time.time() - startTime)
        remainingTime = elapsedTime / currentIndex * (totalNbOfSteps - (currentIndex-1))
        
        hoursE, minutesE, secondsE = self.secondsInHMS(elapsedTime)
        hoursR, minutesR, secondsR = self.secondsInHMS(remainingTime)

        print('Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR))

    def run_scan (self):

        try:
            self._detector.initialize()
            self._scanner.initialize()
            if self._voltmeter is not None:
                self._voltmeter.initialize()

            print('Total number of steps: {}\n'.format(self.totalNbOfSteps) +
                  'X number of steps:     {}\n'.format(self.xNbOfSteps) +
                  'Y number of steps:     {}'.format(self.yNbOfSteps))

            start_time = 0
            first_point = True
            idx = 0

            self._scanner.goSmoothlyToPos(xPos=self.xPositions[0], yPos=self.yPositions[0])

            print('\nScanners are at start position. Waiting for spectrometer acquisition.\n')

            print('step \tx (V)\ty (V)')

            for id_y, y in enumerate(self.yPositions): 
                firstInRow = True
                
                for id_x, x in enumerate(self.xPositions):
                    idx += 1
                    
                    self._scanner.moveX(x)
                    self._scanner.moveY(y)

                    # display update
                    print('{}/{} \t{:.1f} \t{:.1f}'.format(idx, self.totalNbOfSteps, x, y))

                    # For first point may wait for a reaction 
                    # (when acquisition is launched in WinSpec and the old Acton spectrometers)
                    if first_point:
                        self._detector.first_point()
                        start_time = time.time()
                        first_point = False
                    else:
                        if idx % 10 == 0:
                            self.print_elapsed_time(startTime=start_time, currentIndex=idx, totalNbOfSteps=self.totalNbOfSteps)

                        # delay between rows
                        if firstInRow:
                            time.sleep(self.delayBetweenRows)
                            firstInRow = False

                        # delay between points
                        time.sleep(self.delayBetweenPoints)

                        # trigger exposure
                        c = self._detector.readout()
                        if (self.detector_type=='apd'):
                            self.counts[id_x, id_y] = c

                    if self._voltmeter is not None:
                        self.powerInVolts[id_x, id_y] = self._voltmeter.readout()

                    time.sleep(self._detector.delay_after_readout)  # some old devices will not react immediately to say they are integrating

                    # wait for detector to say it finished
                    self._detector.wait_for_ready()

                # move back to first point of row smoothly
                if y != self.yPositions[-1]:
                    self._scanner.goSmoothlyToPos(xPos=self.xPositions[0], yPos=y)        

            # go smoothly to start position
            if self._back_to_zero:
                print('\nGoing back to 0 V on scanners...')
                self._scanner.goSmoothlyToPos(xPos=0, yPos=0)

            print('\nSCAN COMPLETED\n' +
                  'X from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.xPositions[0], self.xPositions[-1], self.xStep, self.xNbOfSteps) +
                  'Y from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.yPositions[0], self.yPositions[-1], self.yStep, self.yNbOfSteps) +
                  'Total number of steps: {}'.format(self.totalNbOfSteps))
        except KeyboardInterrupt:
            print('\n####  Program interrupted by user.  ####')
        finally:
            try:
                self._scanner.close()
            finally:
                try:
                    self._detector.close()
                finally:
                    if (self._voltmeter):
                        self._voltmeter.close()

    def save_to_hdf5 (self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print ("File saved")
        
    def plot_counts (self):
        
        if (self.detector_type == 'apd'):
            py.figure(figsize=(10,10))
            py.pcolor (self.counts)
            py.show()
        else:
            print ("No counts available.. use APD")

        
    def save_volts(self, filename, flatten=True):
        if self._voltmeter is not None:
            if flatten == True:
                pl.savetxt(filename, self.powerInVolts.flatten())
            else:
                pl.savetxt(filename, self.powerInVolts)
            print("\nPower as volts saved in file.")
        else:
            print("\nVoltmeter was not defined for this measurement. No file saved.")
