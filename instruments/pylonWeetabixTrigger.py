# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 11:01:12 2016

@author: raphael proux

To receive and send triggers using Weetabix (NI-6341-USB DAQmx cardboard)
Meant for using with the PyLoN cameras (modern cameras from Princeton)
"""

import PyDAQmx as daq
import pylab as py
import time


class trigSender(daq.Task):
    def __init__(self, channel):
        daq.Task.__init__(self)
        self.CreateDOChan(channel,"",daq.DAQmx_Val_ChanPerLine)
        dataDown = py.array([0], dtype=py.uint8)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataDown, None, None)
        
    def emit(self):
        """
        Emits a 1 ms pulse on the digital output
        """
        dataUp = py.array([1], dtype=py.uint8)
        dataDown = py.array([0], dtype=py.uint8)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataUp, None, None)
        self.WriteDigitalLines(1, 1, 10.0, daq.DAQmx_Val_GroupByChannel, dataDown, None, None)

        
class trigReceiver(daq.Task):
    def __init__(self, channel):
        daq.Task.__init__(self)
        self.CreateDIChan(channel,"",daq.DAQmx_Val_ChanPerLine)
        
    def listen(self):
        """
        Measures the current state of the digital input (one sample)
        """
        data = py.array([0], dtype=py.uint8)
        self.ReadDigitalLines(1, 10.0, daq.DAQmx_Val_GroupByChannel, data, 1, None, None, None)
        return data[0]


class voltOut(daq.Task):
    def __init__(self, channel, min_limit=0., max_limit=5.):
        daq.Task.__init__(self)
        self.CreateAOVoltageChan(channel, "ao0", min_limit, max_limit, daq.DAQmx_Val_Volts,
                                 None)
        self.WriteAnalogScalarF64(1, 10., 0., None)
        
    def write(self, voltage):
        self.WriteAnalogScalarF64(1, 10., voltage, None)
        
    def set_limits (self, min_limit=0., max_limit=5.):
        self._min_lim = min_limit
        self._max_lim = max_limit        
   
if __name__ == "__main__":
       
    try:
        # senderTask = trigSender("/Weetabix/port1/line0")
        # senderTask.StartTask()
        # receiverTask = trigReceiver("/Weetabix/port1/line1")
        # receiverTask.StartTask()
        # senderTask.emit()
        # print receiverTask.listen()
        voltsout = voltOut("SmallNIbox/ao0")
        time.sleep(1)
        voltsout.write(1)
        time.sleep(1)
        voltsout.write(2)
        time.sleep(1)
        voltsout.write(3)
        time.sleep(1)
        voltsout.write(4)
    finally:
        pass
        # senderTask.StopTask()
        # receiverTask.StopTask()