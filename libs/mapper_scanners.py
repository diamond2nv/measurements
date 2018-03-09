# -*- coding: utf-8 -*-

import pylab as pl
import time
import sys
import visa

from measurements.libs import mapper_general as mgen

#from measurements.instruments.LockIn7265GPIB import LockIn7265
#from measurements.instruments import NIBox
from measurements.instruments import AttocubeANCV1 as attoANC
from measurements.instruments import KeithleyPSU2220
#from measurements.instruments.pylonWeetabixTrigger import voltOut

if sys.version_info.major == 3:
    from importlib import reload

#reload(NIBox)
reload(mgen)


class ScannerCtrl (mgen.DeviceCtrl):

    smooth_step = 1.
    smooth_delay = 0.05
    string_id = 'Unknown scanner'

    def initialize(self):
        self._currX = 0
        self._currY = 0

    def moveX (self, value):
        pass

    def moveY (self, value):
        pass

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY

    def _close(self):
        pass

    def goSmoothlyToPos(self, xPos, yPos):
        currX = self.getX()
        currY = self.getY()

        xSmooth_nr_steps = int(abs(pl.floor((currX - xPos) / float(self.smooth_step))) + 1)
        ySmooth_nr_steps = int(abs(pl.floor((currY - yPos) / float(self.smooth_step))) + 1)

        totalSmoothNbOfSteps = max((xSmooth_nr_steps, ySmooth_nr_steps))
        xSmoothPositions = pl.append(pl.linspace(currX, xPos, xSmooth_nr_steps), pl.zeros(totalSmoothNbOfSteps - xSmooth_nr_steps) + xPos)
        ySmoothPositions = pl.append(pl.linspace(currY, yPos, ySmooth_nr_steps), pl.zeros(totalSmoothNbOfSteps - ySmooth_nr_steps) + yPos)

        for x, y in zip(xSmoothPositions, ySmoothPositions):
            self.moveX(x)
            self.moveY(y)
            time.sleep(self.smooth_delay)

    def close_error_handling(self):
        print('WARNING: Scanners {} did not close properly.'.format(self.string_id))


class AttocubeNI (ScannerCtrl):

    def __init__ (self, chX='/Weetabix/ao0', chY='/Weetabix/ao1', conversion_factor=1/15.):
        self.string_id = 'Attocube ANC controlled by NI box DC AO'
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

    def _close(self):
        self.scanners_volt_drive_X.StopTask()
        self.scanners_volt_drive_Y.StopTask()

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY


class AttocubeVISA (ScannerCtrl):

    def __init__ (self, VISA_address, axisX=1, axisY=2):
        self.string_id = 'Attocube ANC controlled by VISA'
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
            self.visa_error_handling(err)

    def moveX (self, value):
        self._ANChandle.setOffset(value, self._axisX)
        self._currX = value

    def moveY (self, value):
        self._ANChandle.setOffset(value, self._axisY)
        self._currY = value

    def _close(self):
        self._ANChandle.close()

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY

class KeithleyPSU (ScannerCtrl):

    def __init__ (self, VISA_address, channel=1):
        self.string_id = 'Keithley PSU2220'
        self._VISA_address = VISA_address
        self._axisX = channel

        self.smooth_step = 0.5
        self.smooth_delay = 0.05

        self._currX = 0
        self._currY = 0

    def initialize(self):
        try:
            self._PSUhandle = KeithleyPSU2220.Keithley2220(self._VISA_address)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)

    def moveX (self, value):
        self._PSUhandle.setVoltage(channel=self._axisX, voltage=value)
        self._currX = value

    def getX (self):
        self._currX = self._PSUhandle.readVoltage(channel=self._axisX)
        return self._currX

    def _close(self):
        self._PSUhandle.close()
