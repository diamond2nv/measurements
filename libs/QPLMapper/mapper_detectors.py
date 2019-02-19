# -*- coding: utf-8 -*-

import time
import sys
import visa
import numpy as np
import pylab as pl

from measurements.libs.QPLMapper import mapper_general as mgen
if sys.version_info.major == 3:
    from importlib import reload
try:
    from measurements.instruments.HF import WavelengthMeter
except:
    print ('Wavemeter not found')
try:
    from measurements.instruments import Lakeshore335 as LS335
    reload (LS335)
except:
    print ('LakeShore not found')
try:
    from measurements.instruments import NIBox
    from measurements.instruments.LockIn7265 import LockIn7265
    from measurements.instruments.pylonWeetabixTrigger import trigSender, trigReceiver
    from measurements.instruments.KeithleyMultimeter import KeithleyMultimeter
    from measurements.instruments.AgilentMultimeter import AgilentMultimeter
    from measurements.instruments import u3
    from TimeTagger import createTimeTagger, Counter

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
        self._is_changed = False
        self.readout_values = None

    def initialize(self):
        pass

    def readout(self):
        return None

    def is_ready(self):
        return True

    def first_point(self):
        return True

    def _is_changed (self):
        pass

    def _close(self):
        pass

    def close_error_handling(self):
        print('WARNING: Detector {} did not close properly.'.format(self.string_id))


class PylonNICtrl (DetectorCtrl):

    def __init__(self, sender_port="/Weetabix/port1/line3", receiver_port="/Weetabix/port1/line2", work_folder=None):
        DetectorCtrl.__init__ (self, work_folder = work_folder)
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
        DetectorCtrl.__init__ (self, work_folder = work_folder)
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
        DetectorCtrl.__init__ (self, work_folder = work_folder)
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
        DetectorCtrl.__init__ (self, work_folder = work_folder)
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
        DetectorCtrl.__init__ (self, work_folder = work_folder)
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

    def __init__(self, VISA_address, mode='voltage', agilent=False, work_folder=None):
        DetectorCtrl.__init__ (self, work_folder = work_folder)
        self.agilent = agilent
        if not agilent:
            self.string_id = 'Keithley multimeter'
        else:
            self.string_id = 'Agilent multimeter'
        self._VISA_address = VISA_address
        self.delay_after_readout = 0.
        self._wfolder = work_folder
        self.mode = mode

    def initialize(self):
        try:
            if not self.agilent:
                self._multimeter = KeithleyMultimeter(self._VISA_address, meas_mode=self.mode)
            else:
                self._multimeter = AgilentMultimeter(self._VISA_address, meas_mode=self.mode)
        except visa.VisaIOError as err:
            self.visa_error_handling(err)

    def readout(self):
        return self._multimeter.read()

    def _close(self):
        self._multimeter.close()
        
class Pylon_LabjackCtrl (DetectorCtrl):

    def __init__(self, TriggerIn = 6, TTLOut = 7):
        """Inputs are the labjack FIO pins connected to spectrometer Trigger in and TTL out"""
        self.string_id = 'Pylon Spectro - Labjack U3 Ctrl'
        self.TriggerIn = TriggerIn
        self.TTLOut = TTLOut

    def initialize(self):
        self.dev = u3.U3()#opens first found U3

    def readout(self):
        """sends a pulse to trigger the spectrometer,
        spectrometer should take a reading"""
        self.dev.configIO(FIOAnalog=0x0F)
        self.pulseduration = 254 #units are unknown, you have take a reading to know how wide this pulse is
        
        """sets the state and direction (to output) of corrresponding FIO pin """
        self.dev.setDOState(ioNum=self.TriggerIn, state=0) #set state to zero
        self.dev.getFeedback(u3.WaitLong(30))#give it some time at zero before sending the pulse 
        self.dev.setDOState(ioNum=self.TriggerIn, state=1) #set state to one
        self.dev.getFeedback(u3.WaitShort(self.pulseduration)) # wait pulse duration
        self.dev.setDOState(ioNum=self.TriggerIn, state=0)#set state back to zero

    def is_ready(self):
        """Looks for a pulse from the spectrometer"""
        return self.dev.getDIState(ioNum = self.TTLOut) # checkes state and changes direction to input

    def first_point(self):
        return self.dev.getDIState(ioNum = self.TTLOut)

    def _close(self):
        pass

class Pylon_LabjackCtrl (DetectorCtrl):

    def __init__(self, TriggerIn = 6, TTLOut = 7):
        """Inputs are the labjack FIO pins connected to spectrometer Trigger in and TTL out"""
        self.string_id = 'Pylon Spectro - Labjack U3 Ctrl'
        self.TriggerIn = TriggerIn
        self.TTLOut = TTLOut

    def initialize(self):
        self.dev = u3.U3()#opens first found U3

    def readout(self):
        """sends a pulse to trigger the spectrometer,
        spectrometer should take a reading"""
        self.dev.configIO(FIOAnalog=0x0F)
        self.pulseduration = 254 #units are unknown, you have take a reading to know how wide this pulse is
        
        """sets the state and direction (to output) of corrresponding FIO pin """
        self.dev.setDOState(ioNum=self.TriggerIn, state=0) #set state to zero
        self.dev.getFeedback(u3.WaitLong(30))#give it some time at zero before sending the pulse 
        self.dev.setDOState(ioNum=self.TriggerIn, state=1) #set state to one
        self.dev.getFeedback(u3.WaitShort(self.pulseduration)) # wait pulse duration
        self.dev.setDOState(ioNum=self.TriggerIn, state=0)#set state back to zero

    def is_ready(self):
        """Looks for a pulse from the spectrometer"""
        return self.dev.getDIState(ioNum = self.TTLOut) # checkes state and changes direction to input

    def first_point(self):
        return self.dev.getDIState(ioNum = self.TTLOut)

    def _close(self):
        pass
    
class Swabian_Ctrl (DetectorCtrl):

    def __init__(self):
        self.dt=100 # in milliseconds
        self.string_id = 'Swabian Timtagger'
        self.gotdata=False
        
    def initialize(self):
        """Creates instance of class"""
        self.tag = createTimeTagger()
        self.tag.setTriggerLevel(0, 0.15)
        self.tag.setTriggerLevel(1, 0.15)

    def readout(self):
        """Takes a single reading of counts"""
        self.ctr = Counter(self.tag, [0,1], int(1e9), int(self.dt))
        time.sleep(self.dt/1000.)
        rates = self.ctr.getData()
        newCount = (pl.mean(rates[0]) + pl.mean(rates[1]))*1000
        self.gotdata = True
        return newCount
    
    def is_ready(self):
        """check to see if ready for a reading"""
        if self.gotdata:
            self.gotdata=False
            return True
        else:
            return False

    def first_point(self):
        return True
        pass
    
    def _close(self):
        self.ctr.stop()
        pass

class HighFinese(DetectorCtrl):
    def __init__(self,channel):
        self.string_id = 'High Finese Wavemeter'
        self.gotData = False
        self.channel = channel

    def initialize(self):
        self.wlm = WavelengthMeter(dllpath="C:\Windows\System32\wlmData.dll", debug=False)
    def readout(self,channel=None,wavelength=True,power=False):
        """Return wavelength in nm/ freq in THz/ power in a.u."""
        if channel is None:
            channel = self.channel
        outputs = self.wlm.GetAll(channel)
        self.gotdata = True
        if wavelength and not power:
            return outputs['wavelength']
        elif not wavelength and not power:
            return outputs['frequency']
        else:
            return outputs['power']
        
    def is_ready(self):
        if self.gotdata:
            self.gotdata=False
            return True
        else:
            return False
    

    def first_point(self):
        return True
        pass

    def _close(self):
        pass
    
class LakeShore(DetectorCtrl):

    def __init__(self,address='COM5',channel='A'):
        self.string_id = 'Lake Shore 335'
        self.gotData = False
        self.channel = channel
        self.address = address

    def initialize(self):
        self.tCtrl = LS335.Lakeshore335(self.address)
        self.tCtrl.id()

    def readout(self,channel=None,wavelength=True,power=False):
        """Return wavelength in nm/ freq in THz/ power in a.u."""
        if channel is None:
            channel = self.channel
        temp = []
        for j in channel:
            temp.append(self.tCtrl.get_kelvin (channel))
        self.gotdata = True
        return np.array(temp)

        
    def is_ready(self):
        if self.gotdata:
            self.gotdata=False
            return True
        else:
            return False
    

    def first_point(self):
        return True
        pass

    def _close(self):
        self.tCtrl.close()