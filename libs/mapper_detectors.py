# -*- coding: utf-8 -*-

import time
import sys
import visa
import numpy as np

from measurements.libs import mapper_general as mgen
if sys.version_info.major == 3:
    from importlib import reload
try:
    from measurements.instruments import NIBox
    from measurements.instruments.LockIn7265 import LockIn7265
    from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver
    from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
    reload (NIBox)
except:
    print ("Enter simulation mode.")


reload(mgen)


class DetectorCtrl (mgen.DeviceCtrl):

    string_id = 'Unknown detector'
    delay_after_readout = 0.
    delay_state_check = 0.

    def __init__(self, work_folder=None):
        self._wfolder = work_folder

    def initialize(self):
        pass

    def readout(self):
        return None

    def is_ready(self):
        return True

    def first_point(self):
        return True

    def _close(self):
        pass

    def close_error_handling(self):
        print('WARNING: Detector {} did not close properly.'.format(self.string_id))


class PylonNICtrl (DetectorCtrl):

    def __init__(self, sender_port="/Weetabix/port1/line3", receiver_port="/Weetabix/port1/line2", work_folder=None):
        self.string_id = 'Pylon (new spectro) camera - NI box control'
        self._wfolder = work_folder
        self._sender_port = sender_port
        self._receiver_port = receiver_port

    def initialize(self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def first_point(self):
        return self.receiverTask.listen()

    def is_ready(self):
        a = self.receiverTask.listen()
        return a

    def readout(self):
        self.senderTask.emit()
        return 0

    def _close(self):
        self.senderTask.StopTask()
        self.receiverTask.StopTask()


class ActonNICtrl (DetectorCtrl):

    def __init__(self, sender_port, receiver_port, work_folder=None):
        self.string_id = 'Acton (old spectro) camera - NI box control'
        self._sender_port = sender_port
        self._receiver_port = receiver_port
        self.delay_after_readout = 0.5
        # self.expect_not_scan = True
        self.measurement_started_flag = False
        self.first_point_flag = True
        self._wfolder = work_folder

    def initialize(self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def first_point(self):

        if not self.measurement_started_flag:
            self.senderTask.emit()
            time.sleep(0.1)
            if self.receiverTask.listen():
                self.measurement_started_flag = True
        if self.measurement_started_flag:
            return True
        else:
            return False

    def is_ready(self):
        a = not self.receiverTask.listen()  # when NOT SCAN signal is down -> detector ready
        return a

    def readout(self):
        if self.first_point_flag:
            self.first_point_flag = False
        else:
            self.senderTask.emit()
            # self.expect_not_scan = True
        return 0

    def _close(self):
        self.senderTask.StopTask()
        self.receiverTask.StopTask()


class ActonLockinCtrl (DetectorCtrl):

    def __init__(self, lockinVisaAddress, work_folder=None):
        self.string_id = 'Acton (old spectro) camera - Lockin control'
        self._wfolder = work_folder
        self._lockin = LockIn7265(lockinVisaAddress)
        self.delay_after_readout = 0.5
        self.delay_state_check = 0.1 
        self.measurement_started_flag = False
        self.first_point_flag = True

    def first_point(self):
        if not self.measurement_started_flag:
            self._lockin.send_pulse()
            time.sleep(0.1)
            if self._lockin.read_ADC_digital():
                self.measurement_started_flag = True
        if self.measurement_started_flag:
            return True
        else:
            return False

    def is_ready(self):
        return not self._lockin.read_ADC_digital()

    def readout(self):
        if self.first_point_flag:
            self.first_point_flag = False
        else:
            self._lockin.send_pulse()
        return 0

    def _close(self):
        self._lockin.close()


class APDCounterCtrl (DetectorCtrl):

    def __init__(self, ctr_port, debug=False, work_folder=None):
        self.string_id = 'APD-NIbox'
        self._wfolder = work_folder
        self._ctr_port = ctr_port
        self.delay_after_readout = 0.
        self._debug = debug

    def set_integration_time_ms(self, t):
        self._ctr_time_ms = t

    def initialize(self):
        self._ctr = NIBox.NIBoxCounter(dt=self._ctr_time_ms)
        self._ctr.set_port(self._ctr_port)

    def readout(self):
        self._ctr.start()
        c = self._ctr.get_counts()
        self._ctr.stop()

        if self._debug:
            print("APD counts: ", c)

        return c

    def first_point(self):
        
        return True

    def _close(self):
        self._ctr.clear()

class dummyAPD (DetectorCtrl):

    def __init__(self, work_folder, random_counts = True, debug = False):
        self.string_id = 'dummyAPD'
        self._wfolder = work_folder
        self.delay_after_readout = 0.
        self._debug = debug
        self._random = random_counts
        
    def set_integration_time_ms (self, t):
        self._ctr_time_ms = t

    def initialize (self):
        pass

    def readout (self):
        if self._random:
            c = int(1000*np.random.rand ())
        else:
            c = 0
        if self._debug:
            print ("APD counts: ", c)

        return c

    def first_point (self):
        self.readout()
        return True

    def _close (self):
        pass

class MultimeterCtrl (DetectorCtrl):

    def __init__(self, VISA_address, mode='voltage', work_folder=None):
        self.string_id = 'Keithley multimeter'
        self._VISA_address = VISA_address
        self.delay_after_readout = 0.
        self._wfolder = work_folder
        self.mode = mode

    def initialize(self):
        try:
            self._multimeter = KeithleyMultimeter(self._VISA_address, meas_mode=self.mode)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)

    def readout(self):
        return self._multimeter.read()

    def _close(self):
        self._multimeter.close()