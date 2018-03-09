# -*- coding: utf-8 -*-

import pylab as pl
import time
import sys
import visa

from measurements.libs import mapper_general as mgen

#from measurements.instruments.LockIn7265GPIB import LockIn7265
from measurements.instruments import NIBox
from measurements.instruments import AttocubeANCV1 as attoANC
from measurements.instruments.pylonWeetabixTrigger import voltOut
from measurements.instruments import KeithleyPSU2220

if sys.version_info.major == 3:
    from importlib import reload

reload(NIBox)
reload(mgen)


class ScannerCtrl (mgen.DeviceCtrl):

    smooth_step = 1.
    smooth_delay = 0.05
    string_id = 'Unknown scanner'
    _channels = []

    def initialize(self):
        pass

    def move(self, target, axis=0):
        pass

    def moveX(self, value):
        pass

    def moveY(self, value):
        pass

    def get(self, axis=0):
        return None

    def getX (self):
        pass

    def getY (self):
        pass

    def _close(self):
        pass

    def move_smooth(self, targets=[0], axes=None):
        # targets and axes should be iterables (or axes=None if default x, y, etc.)
        if axes is None:
            axes = range(len(targets))
        to_pos_list = targets
        nb_steps_list = []
        from_pos_list = []
        for axis, to_pos in zip(axes, to_pos_list):
            from_pos = self.get(axis=axis)
            from_pos_list.append(from_pos)
            print(from_pos,to_pos,axis)
            nb_steps_list.append(int(abs(pl.floor((from_pos - to_pos) / float(self.smooth_step))) + 1))

        total_nb_of_steps = max(nb_steps_list)
        smooth_positions = []
        for to_pos, from_pos, nb_steps in zip(to_pos_list, from_pos_list, nb_steps_list):
            smooth_positions.append(pl.append(pl.linspace(from_pos, to_pos, nb_steps), 
                                              pl.zeros(total_nb_of_steps - nb_steps) + to_pos))

        for i in range(total_nb_of_steps):
            for axis, pos in zip(axes, smooth_positions):
                self.move(pos[i], axis=axis)
            time.sleep(self.smooth_delay)
            

    def close_error_handling(self):
        print('WARNING: Scanners {} did not close properly.'.format(self.string_id))


class AttocubeNI (ScannerCtrl):

    def __init__ (self, chX='/Weetabix/ao0', chY='/Weetabix/ao1', conversion_factor=1/15.):
        self.string_id = 'Attocube ANC controlled by NI box DC AO'
        self._channels = [chX, chY]
        self.conversion_factor = conversion_factor

        self.smooth_step = 1
        self.smooth_delay = 0.05

        self._currX = 0
        self._currY = 0

    def initialize (self):
        self.scanners_volt_drive_X = voltOut(self._channels[0])
        self.scanners_volt_drive_Y = voltOut(self._channels[1])

    def move(self, target, axis=0):
        if axis == 0:
            self.moveX(target)
        elif axis == 1:
            self.moveY(target)

    def moveX (self, value):
        self.scanners_volt_drive_X.write(self.conversion_factor * value)
        self._currX = value

    def moveY (self, value):
        self.scanners_volt_drive_Y.write(self.conversion_factor * value)
        self._currY = value

    def _close(self):
        self.scanners_volt_drive_X.StopTask()
        self.scanners_volt_drive_Y.StopTask()

    def get(self, axis=0):
        if axis == 0:
            return self.getX()
        elif axis == 1:
            return self.getY()

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY


class AttocubeVISA (ScannerCtrl):
    # NOTE : IMPLEMENT POSITION GETTERS PROPERLY

    def __init__ (self, VISA_address, axisX=1, axisY=2):
        self.string_id = 'Attocube ANC controlled by VISA'
        self._VISA_address = VISA_address
        self._channels = [axisX, axisY]
       
        self.smooth_step = 0.5
        self.smooth_delay = 0.05

        self._currX = 0
        self._currY = 0

    def initialize (self):
        try:
            self._ANChandle = attoANC.AttocubeANC(self._VISA_address)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)

    def move(self, target, axis=0):
        if axis == 0:
            self.moveX(target)
        elif axis == 1:
            self.moveY(target)

    def moveX (self, value):
        self._ANChandle.setOffset(value, self._channels[0])
        self._currX = value

    def moveY (self, value):
        self._ANChandle.setOffset(value, self._channels[1])
        self._currY = value

    def _close(self):
        self._ANChandle.close()

    def get(self, axis=0):
        if axis == 0:
            return self.getX()
        elif axis == 1:
            return self.getY()

    def getX (self):
        return self._currX

    def getY (self):
        return self._currY


class Keithley2220(ScannerCtrl):

    def __init__(self, VISA_address, channels):
        self.string_id = 'Keithley PSU2220 DC power supply controlled by VISA'
        self._VISA_address = VISA_address

        self.smooth_step = 0.1
        self.smooth_delay = 0.05

        try:
            channels = list(channels)
        except TypeError:
            channels = [channels]
        if len(channels) == 1:
            channels.append(None)


        self._channels = channels
        print(self._channels,"channels")

    def initialize(self, switch_on_output=False):
        try:
            self._Keithley_handle = KeithleyPSU2220.Keithley2220(self._VISA_address)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)
        if switch_on_output:
            self.output_switch(on=True)

    def move(self, value, axis, mode='voltage'):
        if axis is not None:
            if mode == 'voltage':
                self._Keithley_handle.setVoltage(channel=self._channels[axis], voltage=value)
            elif mode == 'current':
                self._Keithley_handle.setCurrent(channel=self._channels[axis], voltage=value)

    def moveX(self, value):
        self.move(value=value, axis=self._channels[0])
    def moveY(self, value):
        self.move(value=value, axis=self._channels[1])

    def get_setting(self, axis, mode='voltage'):
        if axis is not None:
            if mode == 'voltage':
                return self._Keithley_handle.readSetVoltage(channel=self._channels[axis])
            elif mode == 'current':
                return self._Keithley_handle.readSetCurrent(channel=self._channels[axis])

    def get(self, axis=None, mode='voltage'):
        if axis is not None:
            if mode == 'voltage':
                return self._Keithley_handle.readVoltage(channel=self._channels[axis])

            elif mode == 'current':
                return self._Keithley_handle.readCurrent(channel=self._channels[axis]) 

    def getX(self):
        return self.get(axis=self.channels[0])
    def getY(self):
        return self.get(axis=self.channels[1])

    def channel_combine(self, combMode=KeithleyPSU2220.Keithley2220channelModes.OFF):
        # 'off', 'parallel' or 'series'
        self._Keithley_handle.channelCombine(combMode)

    def output_switch(self, on=True):
        self._Keithley_handle.outputOn(state=on)

    def _close(self):
        self._Keithley_handle.close()



