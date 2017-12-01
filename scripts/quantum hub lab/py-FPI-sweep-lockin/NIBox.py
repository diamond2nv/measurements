"""

@author: Ralph N E Malein

A module to set up the DAQmx tasks to run the NI box ("Weetabix") in various modes.

Currently only the counting mode works - class NIBoxCounter.
"""

import PyDAQmx as daq
import numpy as np
from ctypes import *


class Trigger(daq.Task):
    """
    Creates trigger counter task to determine counter timing.

    Args:
        ctr (str): Number of counter.
        freq (int): Frequency of trigger.
    """
    def __init__(self, ctr, freq):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.freq = freq
        self.CreateCOPulseChanFreq("/Weetabix/ctr"+self.ctr, "trigger_"+self.ctr,
                                   daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low, 0,
                                   self.freq, 0.5)
        self.CfgImplicitTiming(daq.DAQmx_Val_ContSamps, 1000)

    def get_term(self):
        """Returns output terminal for trigger pulses."""
        n = c_char_p(" ")
        self.GetCOPulseTerm("/Weetabix/ctr"+self.ctr, n, 20)
        return n.value


class InputCounter(daq.Task):
    """
    Creates input counter task default tied to PFI0 to count APD pulses.

    Args:
        gate_term (str): Name of timing trigger terminal.
        ctr (str, optional): Number of counter.  Defaults to "1".
        in_port (str, optional): Name of input port.  Defaults to "PFI0".
    """
    def __init__(self, gate_term, ctr="1", in_port="PFI0"):
        daq.Task.__init__(self)
        self.in_port = in_port
        self.ctr = str(ctr)
        self.CreateCICountEdgesChan("/Weetabix/ctr"+self.ctr, "ctr"+self.ctr,
                                    daq.DAQmx_Val_Rising, 0,
                                    daq.DAQmx_Val_CountUp)
        self.CfgSampClkTiming(gate_term, 10000, daq.DAQmx_Val_Rising,
                              daq.DAQmx_Val_ContSamps, 10000)
        self.SetCICountEdgesTerm("/Weetabix/ctr"+self.ctr, "/Weetabix/"+self.in_port)

    def read_counts(self):
        """Returns an array of 10000 samples of cumulative counts."""
        self.StopTask()
        self.data = np.zeros((10000,),dtype=np.uint32)
        self.ReadCounterU32(10000, 10., self.data, 10000, None, None)
        return self.data


class TrigSender(daq.Task):
    def __init__(self, channel):
        daq.Task.__init__(self)
        self.CreateDOChan(channel,"",daq.DAQmx_Val_ChanPerLine)
        dataDown = np.array([0], dtype=np.uint8)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataDown, None, None)

    def emit(self):
        """
        Emits a 1 ms pulse on the digital output
        """
        dataUp = np.array([1], dtype=np.uint8)
        dataDown = np.array([0], dtype=np.uint8)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataUp, None, None)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataDown, None, None)


class TrigReceiver(daq.Task):
    def __init__(self, channel):
        daq.Task.__init__(self)
        self.CreateDIChan(channel,"",daq.DAQmx_Val_ChanPerLine)

    def listen(self):
        """
        Measures the current state of the digital input (one sample)
        """
        data = np.array([0], dtype=np.uint8)
        self.ReadDigitalLines(1, 10.0, daq.DAQmx_Val_GroupByChannel, data, 1, None, None, None)
        return data[0]


class NIBoxCounter():
    """
    A class to count pulses.

    Args:
        dt (int): integration time in milliseconds.

    Attributes:
        dt (int): integration time in milliseconds.
        f (int): frequency of the Trigger task: determined by dt.
        Trg (Trigger class): task that controls timing trigger.
        Ctr (InputCounter class): task that counts input pulses.
    """
    def __init__(self, dt):
        self.dt = dt
        self.f = int(np.ceil(1.0e7 / float(self.dt)))
        self.Trg = Trigger(0, self.f)
        self.Ctr = InputCounter(self.Trg.get_term(), 1)

    def start(self):
        """Starts Trg and Ctr tasks."""
        self.Trg.StartTask()
        self.Ctr.StartTask()

    def stop(self):
        """Stops Trg and Ctr tasks."""
        self.Ctr.StopTask()
        self.Trg.StopTask()

    def clear(self):
        """Clears Trg and Ctr tasks. They must be reinitialised to be used again."""
        self.Trg.ClearTask()
        self.Ctr.ClearTask()

    def set_port(self, port):
        """
        Sets the input port for pulse counting.

        Args:
            port (str): Name of input port on NI box, in form "PFI#"
        """
        self.Ctr.StopTask()
        self.Ctr.SetCICountEdgesTerm("/Weetabix/ctr"+self.Ctr.ctr, "/Weetabix/"+port)
        self.Ctr.in_port = port

    def set_dt(self, dt):
        """
        Sets the integration time and calculates f.

        Args:
            dt (int): integration time in milliseconds.
        """
        self.dt = dt
        self.f = int(np.ceil(1.0e7 / float(self.dt)))
        self.Trg.StopTask()
        self.Trg.SetCOPulseFreq("/Weetabix/ctr"+self.Trg.ctr, self.f)
        self.Trg.freq = self.f
        self.Trg.StartTask()

    def get_counts(self):
        """Gets counts in integration time."""
        data = self.Ctr.read_counts()
        return data[-1]


class NIBoxSpec():
    """
    A class to use the NI box's digital I/O to trigger the spectrometer.

    Args:
        i_ch (str): Name of the input digital line on the NI box.
        o_ch (str): Name of the output digital line on the NI box.

    """
    def __init__(self, i_ch, o_ch):
        self.i_ch = i_ch
        self.o_ch = o_ch
        self.Sender = TrigSender(self.o_ch)
        self.Listener = TrigReceiver(self.i_ch)

    def start(self):
        """Starts Sender and Listener tasks."""
        self.Sender.StartTask()
        self.Listener.StartTask()

    def stop(self):
        """Stops Sender and Listener tasks."""
        self.Listener.StopTask()
        self.Sender.StopTask()

    def clear(self):
        """Clears Sender and Listener tasks. They must be reinitialised to be used again."""
        self.Sender.ClearTask()
        self.Listener.ClearTask()

    def set_i_ch(self, i_ch):
        """
        Sets the input channel.

        Args:
            i_ch (str): Name of the input channel.
        """
        self.i_ch = i_ch
        self.Listener.ClearTask()
        self.Listener = TrigReceiver(self.i_ch)

    def set_o_ch(self, o_ch):
        """
        Sets the output channel.

        Args:
            i_ch (str): Name of the output channel.
        """
        self.o_ch = o_ch
        self.Sender.ClearTask()
        self.Sender = TrigSender(self.o_ch)

    def emit(self):
        """Sends a pulse from the output channel."""
        self.Sender.emit()

    def listen(self):
        """Checks the value of the input channel."""
        self.Listener.listen()

    def emit_wait(self, timeout=None):
        """
        Sends an output pulse, then waits for an input pulse.

        Args:
            timeout (int, optional): Specifies a timout time in seconds for
                waiting.  If not specified, waits indefinitely.

        Returns:
            echo (int): 1 if an input pulse is measured within timeout,
                0 otherwise.
        """
        self.Sender.emit()
        echo = 0
        if timeout:
            now = time.time()
            end = now + timeout
            while echo == 0 and time.time() <= end:
                echo = self.Listener.listen()
        else:
            while echo == 0:
                echo = self.Listener.listen()
        return echo

# INCOMPLETE HEREAFTER
class NIBoxVoltage():
    """
    A class to use the NI Box's analogue input/output to read and write voltages.
    """
    def __init__(self, a_o, a_i=None):
        self.a_o = a_o
        self.a_i = a_i
