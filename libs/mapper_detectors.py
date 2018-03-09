# -*- coding: utf-8 -*-

import time
import sys
import visa

from measurements.libs import mapper_general as mgen

from measurements.instruments import NIBox
from measurements.instruments.LockIn7265GPIB import LockIn7265
from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver
from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
if sys.version_info.major == 3:
    from importlib import reload

reload(NIBox)
reload(mgen)


class DetectorCtrl (mgen.DeviceCtrl):

    string_id = 'Unknown detector'
    delay_after_readout = 0.
    delay_state_check = 0.

    def __init__(self, work_folder):
        self._wfolder = work_folder

    def initialize (self):
        pass

    def readout (self):
        return None

    def is_ready (self):
        return True

    def first_point (self):
        return True

    def _close(self):
        pass

    def close_error_handling(self):
        print('WARNING: Detector {} did not close properly.'.format(self.string_id))


class PylonNICtrl (DetectorCtrl):

    def __init__(self, work_folder, sender_port="/Weetabix/port1/line3", receiver_port = "/Weetabix/port1/line2"):
        self.string_id = 'Pylon (new spectro) camera - NI box control'
        self._wfolder = work_folder
        self._sender_port = sender_port
        self._receiver_port = receiver_port

    def initialize (self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def wait_for_ready (self):
        CCDready = 0
        while CCDready == 0:
            CCDready = self.receiverTask.listen()

    def readout(self):
        self.senderTask.emit()
        return 0

    def _close(self):
        self.senderTask.StopTask()
        self.receiverTask.StopTask()


class ActonNICtrl (DetectorCtrl):

    def __init__(self, sender_port, receiver_port):
        self.string_id = 'Acton (old spectro) camera - NI box control'
        self._sender_port = sender_port
        self._receiver_port = receiver_port
        self.delay_after_readout = 0.5
        # self.expect_not_scan = True
        self.measurement_started_flag = False
        self.first_point_flag = True

    def initialize (self):
        self.senderTask = trigSender(self._sender_port)
        self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def first_point (self):

        if not self.measurement_started_flag:
            self.senderTask.emit()
            time.sleep(0.1)
            if self.receiverTask.listen():
                self.measurement_started_flag = True
        if self.measurement_started_flag:
            return True
        else:
            return False

    def is_ready (self):
        # if self.expect_not_scan:  # wait for CCD 'NOT SCAN' signal (device scanning)
        #     if self.receiverTask.listen():
        #         self.expect_not_scan = False
        # if not self.expect_not_scan:
        #     if not self.receiverTask.listen():
        #         return True
        # return False

        return not self.receiverTask.listen()  # when NOT SCAN signal is down -> detector ready

    def readout (self):
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

    def __init__(self, work_folder, lockinVisaAddress):
        self.string_id = 'Acton (old spectro) camera - Lockin control'
        self._wfolder = work_folder
        self._lockin = LockIn7265(lockinVisaAddress)
        self.delay_after_readout = 0.5
        self.delay_state_check = 0.1 
        self.measurement_started_flag = False
        self.first_point_flag = True

    def first_point (self):
        if not self.measurement_started_flag:
            self._lockin.sendPulse()
            time.sleep(0.1)
            if self._lockin.readADCdigital():
                self.measurement_started_flag = True
        if self.measurement_started_flag:
            return True
        else:
            return False
        

    def is_ready (self):
        return not self._lockin.readADCdigital()

    def readout (self):
        if self.first_point_flag:
            self.first_point_flag = False
        else:
            self.lockin.sendPulse()
        return 0

    def _close(self):
        self.lockin.close()


class APDCounterCtrl (DetectorCtrl):

    def __init__(self, work_folder, ctr_port, debug = False):
        self.string_id = 'APD NI box counter'
        self._wfolder = work_folder
        self._ctr_port = ctr_port
        self.delay_after_readout = 0.
        self._debug = debug
        
    def set_integration_time_ms (self, t):
        self._ctr_time_ms = t

    def initialize (self):
        self._ctr = NIBox.NIBoxCounter(dt=self._ctr_time_ms)
        self._ctr.set_port (self._ctr_port)

    def readout (self):
        self._ctr.start()
        c = self._ctr.get_counts ()
        self._ctr.stop()

        if self._debug:
            print ("APD counts: ", c)

        return c

    def first_point (self):
        return True

    def _close (self):
        self._ctr.clear()


class VoltmeterCtrl (DetectorCtrl):

    def __init__(self, VISA_address):
        self.string_id = 'Voltmeter'
        self._VISA_address = VISA_address
        self.delay_after_readout = 0.

    def initialize (self):
        try:
            self._voltmeter = KeithleyMultimeter(self._VISA_address)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)

    def readout (self):
        return self._voltmeter.read()

    def _close (self):
        self._voltmeter.close()

