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
from measurements.instruments import solstis

if sys.version_info.major == 3:
    from importlib import reload

reload(NIBox)
reload(mgen)

#################################################
#           DEFAULT SCANNERS CLASSES            #
#################################################
# These classes should not be modified unless you know what you are doing
# For Scanner implementation, see the LAB SCANNERS CLASSES section below.

class ScannerCtrl (mgen.DeviceCtrl):

    """Default Scanner class which defines the mandatory functions to be present in any
    scanner class and gives them default behaviour. Also contains functions like 
    move_smooth() which should mostly work the same way for any type of scanner
    
    Attributes:
        number_of_axes (int): number of axes/channels of the device
        smooth_delay (float): delay in seconds between each step of the move_smooth
        smooth_step (float): amplitude of each step for the move_smooth function
        string_id (str): string identifying the device. Used in error messages.
    """
    
    def __init__(self, channels=[]):
        self.smooth_step = 1.
        self.smooth_delay = 0.05
        self.string_id = 'Unknown scanner'

        if channels is None:
            self.number_of_axes = 0
        else:
            try:
                self.number_of_axes = len(channels)
            except TypeError:
                self.number_of_axes = len(list(channels))

        try:
            channels = list(channels)
        except TypeError:
            channels = [channels]
        if channels == [None]:
            channels = []

        self._channels = channels
        self.number_of_axes = len(channels)
        self._dev_initialised = False
        self._dev_closed = True

    def __getitem__(self, key):
        if type(key) is not int:
            raise TypeError('Axis number should be an integer.')
        if not 0 <= key < self.number_of_axes:
            raise IndexError(f'The addressed axis does not exist (out of bounds). This device has {self.number_of_axes} axes defined, you tried accessing axis {key}.')
        return Saxis(self, key)

    def __len__(self):
        return self.number_of_axes

    def initialize(self, force=False):
        if force:
            self._dev_initialised = False
        if not self._dev_initialised:
            try:
                self._initialize()
            except visa.VisaIOError as err:
                self.visa_error_handling(err)
            self._dev_initialised = True
            self._dev_closed = False

    def _initialize(self):
        pass

    def move(self, target, axis=0):
        if 0 <= axis < self.number_of_axes:
            self._move(target, axis)

    def _move(self, target, axis=0):
        pass

    def get(self, axis=0):
        if 0 <= axis < self.number_of_axes:
            return self._get(axis)
        else:
            return None

    def _get(self, axis=0):
        return None

    def _close(self):
        # here, call device close function
        pass

    def close(self):
        if not self._dev_closed:
            super().close()
            self._dev_closed = True

    def set_smooth_delay(self, value):
        self.smooth_delay = value

    def set_smooth_step(self, value):
        self.smooth_step = value

    def move_smooth(self, scanner_axes, targets=[]):
        move_smooth(scanner_axes=scanner_axes, targets=targets)

    def close_error_handling(self):
        print('WARNING: Scanners {} did not close properly.'.format(self.string_id))


class Saxis():
    def __init__(self, scanner, axis):
        self.axis = axis
        self.scanner = scanner
    def __getitem__(self, key):
        raise AttributeError("'Saxis' object is not subscriptable.")
    def move(self, target):
        self.scanner.move(target=target, axis=self.axis)
    def get(self):
        return self.scanner.get(axis=self.axis)
    def move_smooth(self, target):
        # note this construction through the scanner object allows the user to overload move_smooth() for a specific scanner
        self.scanner.move_smooth(scanner_axes=[self], targets=[target])
    def initialize(self):
        self.scanner.initialize()
    def close(self):
        self.scanner.close()


def move_smooth(scanner_axes, targets=[]):
    smooth_steps = [s_axis.scanner.smooth_step for s_axis in scanner_axes]
    smooth_delay = 0
    for s_axis in scanner_axes:
        if s_axis.scanner.smooth_delay > smooth_delay:
            smooth_delay = s_axis.scanner.smooth_delay

    to_pos_list = targets
    nb_steps_list = []
    from_pos_list = []
    for s_axis, smooth_step, to_pos in zip(scanner_axes, smooth_steps, to_pos_list):
        
        from_pos = s_axis.get()
        from_pos_list.append(from_pos)
        # print(from_pos,to_pos,axis)
        if from_pos is None:
            nb_steps_list.append(0)
        else:
            nb_steps_list.append(int(abs(pl.floor((from_pos - to_pos) / float(smooth_step))) + 1))

    total_nb_of_steps = max(nb_steps_list)
    smooth_positions = []
    for to_pos, from_pos, nb_steps in zip(to_pos_list, from_pos_list, nb_steps_list):
        if from_pos is None:
            from_pos = 0
        smooth_positions.append(pl.append(pl.linspace(from_pos, to_pos, nb_steps), 
                                          pl.zeros(total_nb_of_steps - nb_steps) + to_pos))

    for i in range(total_nb_of_steps):
        for s_axis, pos in zip(scanner_axes, smooth_positions):
            s_axis.move(pos[i])
        time.sleep(smooth_delay)


#################################################
#             LAB SCANNERS CLASSES              #
#################################################

class TestScanner (ScannerCtrl):

    def __init__(self, address, channels=[2,3]):
        super().__init__(channels=channels)
        self.string_id = 'Test device'
        self.address = address

        self.smooth_step = 0.5
        self.smooth_delay = 0.5

    def _initialize(self):
        print('Device initialized')

    def _move(self, target, axis=0):
        print(f'Move axis {axis} to target {target}')

    def _get(self, axis=0):
        print(f'Got value from axis {axis}')
        return 1.1

    def _close(self):
        print('Closing test device')


class AttocubeNI (ScannerCtrl):
    def __init__(self, chX='/Weetabix/ao0', chY='/Weetabix/ao1', start_pos=[0,0], conversion_factor=1/15.):
        super().__init__(channels=[chX, chY])
        self.string_id = 'Attocube ANC scanners controlled by NI box DC AO'
        self.conversion_factor = conversion_factor

        self.smooth_step = 1
        self.smooth_delay = 0.05

        self._curr_pos = [pos for channel, pos in zip(self._channels, start_pos)]

    def _initialize(self):
        self.scanners_volt_drives = [voltOut(channel) for channel in self._channels]

    def _move(self, target, axis=0):
        self.scanners_volt_drives[axis].write(self.conversion_factor * target)
        self._curr_pos[axis] = target

    def _get(self, axis=0):
        return self._curr_pos[axis]

    def _close(self):
        for scanner in self.scanners_volt_drives:
            scanner.StopTask()


class AttocubeVISA (ScannerCtrl):

    def __init__(self, VISA_address, chX=1, chY=2):
        super().__init__(channels=[chX, chY])
        self.string_id = 'Attocube ANC scanners controlled by VISA'
        self._VISA_address = VISA_address

        self.smooth_step = 0.5
        self.smooth_delay = 0.05

    def _initialize(self):
        self._ANChandle = attoANC.AttocubeANC(self._VISA_address)

    def _move(self, target, axis=0):
        self._ANChandle.setOffset(target, self._channels[axis])

    def _get(self, axis=0):
        return self._ANChandle.getOffset(self._channels[axis])

    def _close(self):
        self._ANChandle.close()


class AttocubeVISAstepper (ScannerCtrl):
    
    def __init__ (self, VISA_address, channels, nb_of_clicks_per_deg=928./5):
        super().__init__(channels=channels)
        self.string_id = 'Attocube ANC steppers controlled by VISA'
        self._VISA_address = VISA_address
       
        self._channels = channels[0:1]
        self.number_of_axes = 1
        
        self._curr_position = [0]

        self.nb_of_clicks_per_deg = nb_of_clicks_per_deg
       
    def _initialize (self):
        self._ANChandle = attoANC.AttocubeANC(self._VISA_address)

        self._attoAxis = attoANC.ANCaxis(self._channels[0], self._ANChandle)

    def _move(self, target, axis=0):

        move_by_deg = target - self._curr_position[0]
        move_by_clicks = int(py.floor(move_by_deg * self.nb_of_clicks_per_deg))
        if move_by_clicks < 0:
            self._attoAxis.stepDown(-move_by_clicks)
        else:
            self._attoAxis.stepUp(move_by_clicks)

        self._curr_position[0] += move_by_deg

    def _get(self, axis=0):
        return self._curr_position[0]

    def _close(self):
        self._ANChandle.close()



class Keithley2220(ScannerCtrl):

    def __init__(self, VISA_address, channels):
        super().__init__(channels)
        self.string_id = 'Keithley PSU2220 DC power supply controlled by VISA'
        self._VISA_address = VISA_address

        self.smooth_step = 0.5
        self.smooth_delay = 0.05

        self._axes_modes = ['voltage' for ch in self._channels]

    def _initialize(self, switch_on_output=False):
        try:
            self._Keithley_handle = KeithleyPSU2220.Keithley2220(self._VISA_address)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)
        if switch_on_output:
            self.output_switch(on=True)

    def set_axis_mode(self, axis, mode):
        if axis is not None and mode in {'voltage', 'current'}:
            self._axes_modes = mode

    def _move(self, target, axis):
        if self._axes_modes[axis] == 'voltage':
            self._Keithley_handle.set_voltage(channel=self._channels[axis], voltage=target)
        elif self._axes_modes[axis] == 'current':
            self._Keithley_handle.set_current(channel=self._channels[axis], voltage=target)

    def get_set_value(self, axis):
        if axis is not None:
            if self._axes_modes[axis] == 'voltage':
                return self._Keithley_handle.read_set_voltage(channel=self._channels[axis])
            elif self._axes_modes[axis] == 'current':
                return self._Keithley_handle.read_set_current(channel=self._channels[axis])
        else:
            return None

    def _get(self, axis=None):
        if self._axes_modes[axis] == 'voltage':
            return self._Keithley_handle.read_voltage(channel=self._channels[axis])
        elif self._axes_modes[axis] == 'current':
            return self._Keithley_handle.read_current(channel=self._channels[axis])

    def channel_combine(self, combMode=KeithleyPSU2220.Keithley2220channelModes.OFF):
        # 'off', 'parallel' or 'series'
        self._Keithley_handle.channel_combine(combMode)

    def output_switch(self, on=True):
        self._Keithley_handle.output_on(state=on)

    def _close(self):
        self._Keithley_handle.close()


class Keithley2220_neg_pos(Keithley2220):
    def __init__(self, VISA_address, ch_neg, ch_pos):
        super().__init__(VISA_address, channels=[ch_neg,ch_pos])

    def _move(self, target, axis=0):
        if target < 0:
            super()._move(-target, axis=0)
            super()._move(0, axis=1)
        else:
            super()._move(target, axis=1)
            super()._move(0, axis=0)

    def _get(self, axis=0):
        neg_bias = super()._get(0)
        pos_bias = super()._get(1)
        return pos_bias-neg_bias

class SolstisLaserScanner(ScannerCtrl):
    def __init__(self, laser_ip_address, pc_ip_address, port_number, timeout=40, finish_range_radius=0.01, max_nb_of_fails=10):
        super().__init__([0])

        self.string_id = 'Solstis Laser'
        self.laser_ip_address = laser_ip_address
        self.pc_ip_address = pc_ip_address
        self.port_number = port_number
        self.timeout = timeout
        self.finish_range_radius = finish_range_radius
        self.max_nb_of_fails = max_nb_of_fails
        self.problematic_wavelengths = []
        
    def _initialize(self, switch_on_output=False):

        self._laser_handle = solstis.SolstisLaser(laser_ip_address=self.laser_ip_address, pc_ip_address=self.pc_ip_address, port_number=self.port_number)
   
    def _move(self, target, axis):
        self._laser_handle.set_wavelength(target)
        
        nb_of_fails = 0
        while True:
            try:
                self._laser_handle.wait_for_tuning(timeout=self.timeout, finishRangeRadius=self.finish_range_radius)
            except solstis.SolstisError:
                nb_of_fails += 1
                if nb_of_fails > self.max_nb_of_fails:
                    self.problematic_wavelengths.append(target)
                    break
                else:
                    print 'Laser failed to tune to {}, retrying {}/{}'.format(target, nb_of_fails, self.max_nb_of_fails)
                    self._laser_handle.set_wavelength(target)
            else:
                break

    def _get(self, axis):
        return self._laser_handle.get_wavelength()

    def _close(self):
        self._laser_handle.close()




if __name__ == '__main__':
    toto = TestScanner(address='totoLand', channels=[3,5])
    toto.initialize()
    print(toto[0].get())
    print(toto[1].get())
    toto[0].move(2)
    toto[1].move(4)
    # toto[0].move_smooth(3)

    move_smooth(toto, [3,4])

    for titi in toto:
        titi.move(10)
