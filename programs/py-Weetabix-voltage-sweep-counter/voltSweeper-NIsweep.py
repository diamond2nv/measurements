# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 15:42:15 2016

@author: Ralph N E Malein

Uses Lockin 7265 DAC 1 to control bias voltage on sample
Sweeps voltage from start to finish values, then reads APD / SNSPD

"""

import PyDAQmx as daq
from LockIn7265 import LockIn7265

import pylab as pl
import time
from PyQt4 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg
from os.path import dirname
import picoHarp as ph
from TimeTagger import createTimeTagger, Counter

VISA_LOCKIN_ADDRESS = r'GPIB0::12::INSTR'

class Trigger(daq.Task):
    """
    PyDAQmx.Task subclass: generates "Trigger" class that determines clock for 
    "InputCounter" class
    """
    def __init__(self, ctr, freq):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.freq = freq
        # Create counter output pulse channel determined by frequency self.freq
        self.CreateCOPulseChanFreq("/Weetabix/ctr"+self.ctr, "trigger_"+self.ctr, 
                                   daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low, 0, 
                                   self.freq, 0.5)
        self.CfgImplicitTiming(daq.DAQmx_Val_ContSamps, 1000)

        
    def get_term(self):
        """
        Returns output terminal for Trigger task
        """
        n = c_char_p(" ")
        self.GetCOPulseTerm("/Weetabix/ctr"+self.ctr, n, 20)
        return n.value
        
    
class VoltOut(daq.Task):
    def __init__(self, channel):
        daq.Task.__init__(self)
        self.CreateAOVoltageChan(str(channel), "ao0", -1., 1., daq.DAQmx_Val_Volts,
                                 None)
        
    def write(self, voltage):
        self.WriteAnalogF64(1, 1, 10.,daq.DAQmx_Val_GroupByChannel, voltage, None, None)    
    
    def close(self):
        pass
        
class InputCounter(daq.Task):
    """
    PyDAQmx.Task subclass: generates IputCounter class that counts TTL pulses
    on PFI0 input to NI box
    """
    def __init__(self, gate_term, ctr="1"):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.data = pl.zeros((10,),dtype=pl.uint32)
        self.CreateCICountEdgesChan("Weetabix/ctr"+self.ctr, "ctr"+self.ctr, 
                                    daq.DAQmx_Val_Rising, 0, 
                                    daq.DAQmx_Val_CountUp)
        self.CfgSampClkTiming(gate_term, 10000, daq.DAQmx_Val_Rising, 
                              daq.DAQmx_Val_ContSamps, 10000)
        self.SetCICountEdgesTerm("/Weetabix/ctr"+self.ctr, "/Weetabix/PFI1")

        
    def read_counts(self):
        self.StopTask()
        self.data = pl.zeros((10000,),dtype=pl.uint32)
        self.ReadCounterU32(10000, 10., self.data, 10000, None, None)
        return self.data
        

class MapWindow(QtGui.QWidget):
    NI_BOX = 0
    PICOHARP = 1
    SWABIAN = 2
    
    def __init__(self, app):
        super(MapWindow, self).__init__()
        self.app = app
        self.init_ui()
        
        self.v_i = 0.
        self.v_f = 0.
        self.dt = 1
        self.no_of_steps = 1
        self.repeats = 1
        
        self.file_path = ""
        self.val_change()
        
    def init_ui(self):
        # defining widgets and layout
        self.graph = pg.PlotWidget()
        
        self.eta_box = QtGui.QStatusBar(self)
        
        self.start_v = QtGui.QDoubleSpinBox(self)
        self.start_v.setMinimum(-10.000)
        self.start_v.setMaximum(10.000)
        self.start_v.setDecimals(3)
        self.start_v.setSingleStep(0.100)
        self.start_v.setValue(-0.05)
        
        self.end_v = QtGui.QDoubleSpinBox(self)
        self.end_v.setMinimum(-10.000)
        self.end_v.setMaximum(10.000)
        self.end_v.setDecimals(3)
        self.end_v.setSingleStep(0.100)
        self.end_v.setValue(0.05)
        
        self.time = QtGui.QDoubleSpinBox(self)
        self.time.setMaximum(9.9)
        self.time.setMinimum(0.001)
        self.time.setSingleStep(0.1)
        self.time.setDecimals(3)
        self.time.setValue(0.1)
        
        self.steps = QtGui.QSpinBox(self)
        self.steps.setMaximum(99999)
        self.steps.setValue(1)
        
        self.step_size_field = QtGui.QSpinBox(self)
        self.step_size_field.setMaximum(10000)
        self.step_size_field.setMinimum(1)
        self.step_size_field.setSingleStep(1)
        self.step_size_field.setValue(1)
        
        self.reps = QtGui.QSpinBox(self)
        self.reps.setMinimum(1)
        self.reps.setSingleStep(1)
        self.reps.setValue(5)
        
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        self.sav = QtGui.QPushButton("Save", self)
        
        self.cb = QtGui.QComboBox()
        self.cb.addItems(["National Instruments box", "PicoHarp", "Swabian"])
        self.cb.setCurrentIndex(self.SWABIAN)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.graph)
        vbox.addWidget(self.eta_box)
        vbox.addWidget(QtGui.QLabel("Start Voltage"))
        vbox.addWidget(self.start_v)
        vbox.addWidget(QtGui.QLabel("End Voltage"))
        vbox.addWidget(self.end_v)
        vbox.addWidget(QtGui.QLabel("No. of steps"))
        vbox.addWidget(self.steps)
        vbox.addWidget(QtGui.QLabel("Step size (mV)"))
        vbox.addWidget(self.step_size_field)
        vbox.addWidget(QtGui.QLabel("Number of repeats"))
        vbox.addWidget(self.reps)
        vbox.addWidget(self.cb)
        vbox.addWidget(QtGui.QLabel("Time (s)"))
        vbox.addWidget(self.time)
        vbox.addWidget(self.btn)
        vbox.addWidget(self.stp)
        vbox.addWidget(self.sav)
        
        self.setLayout(vbox)
        self.setGeometry(250, 80, 956, 900)
        self.setWindowTitle("Volt Sweep")
        
        # connecting signals and sockets
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        self.sav.clicked.connect(self.save)
        self.start_v.valueChanged.connect(self.val_change)
        self.end_v.valueChanged.connect(self.val_change)
        self.time.valueChanged.connect(self.val_change)
        self.steps.valueChanged.connect(self.val_change)
        self.step_size_field.valueChanged.connect(self.val_change)
        self.reps.valueChanged.connect(self.val_change)
        self.cb.currentIndexChanged.connect(self.val_change)
        
        # graph style
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        self.plotPen = pg.mkPen({'width': 1, 'color': 'y'})
        
        bottom = self.graph.getPlotItem().getAxis('bottom')
        left = self.graph.getPlotItem().getAxis('left')
        
        bottom.setStyle(tickTextOffset=15, tickLength=10)
        left.setStyle(tickTextOffset=5, tickLength=10)
        
        bottom.setPen(axisPen)
        left.setPen(axisPen)
        
        bottom.tickFont = axisFont
        left.tickFont = axisFont
        
        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom.setLabel(text='Voltage', units='V', **labelStyle)
        left.setLabel(text='Counts', units="Hz", **labelStyle)
        bottom.setHeight(70)
        left.setWidth(80)
        YAxis = self.graph.getPlotItem().getViewBox().YAxis
        self.graph.enableAutoRange(axis=YAxis)
        XAxis = self.graph.getPlotItem().getViewBox().XAxis
        self.graph.enableAutoRange(axis=XAxis)
        
        self.show()
        
        
    def val_change(self):
        self.v_i = int(pl.floor(self.start_v.value() * 1000))  # in mV
        self.v_f = int(pl.ceil(self.end_v.value() * 1000))  # in mV
        self.dt = int(self.time.value() * 1000)  # in ms
        if self.no_of_steps == self.steps.value():  # step_size was modified
            self.step_size = self.step_size_field.value()  # in mV
            self.no_of_steps = int(float(self.v_f - self.v_i) // self.step_size) + 1
            self.steps.setValue(self.no_of_steps)
        else:
            self.no_of_steps = self.steps.value()
            self.step_size = int(float(self.v_f - self.v_i) / (self.no_of_steps - 1))
            self.step_size_field.setValue(self.step_size)
        self.repeats = self.reps.value()
        self.counterDev = self.cb.currentIndex()
        
    def start(self):
        self.graph.clear()
        self.plot = self.graph.plot(pen=self.plotPen)
        self.buff = []
        self.running = False
        self.gotdata = False
        self.btn.setEnabled(False)
        self.voltT = VoltOut('/Weetabix/ao0')#LockIn7265(VISA_LOCKIN_ADDRESS)
        if self.counterDev == self.NI_BOX:
            self.NI_init_ctr(intTime=self.dt)
            self.runThread = threading.Thread(target=self.NI_run)  
        elif self.counterDev == self.PICOHARP:
            self.runThread = threading.Thread(target=self.PH_run)
        else:
            self.runThread = threading.Thread(target=self.SW_run)
        now = time.time()
        then = now + self.no_of_steps*(float(self.dt) /1000)
        then_str = time.ctime(then)
        self.eta_box.showMessage("Estimated end:" + then_str)
        self.running = True
        self.runThread.start()
        
        while self.running:
            if self.gotdata:                
                self.plot.setData(self.v_step[:len(self.buff)],self.buff)
                self.gotdata = False
            self.app.processEvents()
            
        self.btn.setEnabled(True)
        
    def stop(self):
        self.running = False
        
        
    def NI_init_ctr(self, intTime=100):
        # intTime in milliseconds
        frequency = int(pl.ceil(1.0e7 / float(intTime)))
        self.trig = Trigger(0, frequency)
        self.trig.StartTask()
        self.ctr = InputCounter(self.trig.get_term(), 1)
        
    def NI_run(self):
        
        self.v_step = pl.array([pl.linspace(self.v_i, self.v_f, self.no_of_steps) for i in range(self.repeats)]).flatten()
        try:
            for v in self.v_step:
                if self.running:
                    #print 'YAYAYA {} {}'.format(float(v), float(v)/1000)
                    self.voltT.write(pl.array([float(v)/1000]).astype(pl.float64))
                    self.ctr.data = pl.zeros((10000,), dtype=pl.uint32)
                    self.ctr.StartTask()
                    #time.sleep(float(self.dt)/1000)
                    self.ctr.ReadCounterU32(10000, 10., self.ctr.data, 10000, None, None)
                    self.ctr.StopTask()
                    data = float((self.ctr.data[-1])) / self.dt * 1000
                    self.buff.append(data)                    
                    self.gotdata = True
                    #print v
                else:
                    break
        finally:
            self.running = False
            self.ctr.StopTask()
            self.ctr.ClearTask()
            self.trig.ClearTask()
            self.voltT.close()
#            self.voltT.ClearTask()
        
    def PH_run(self):   
        """Runs in own thread - reads data via Picoharp counters"""
        
        self.v_step = pl.array([pl.linspace(self.v_i, self.v_f, self.no_of_steps) for i in range(self.repeats)]).flatten()
        try:
            self.ph = ph.PicoHarp()
            for v in self.v_step:
                if self.running:
                    self.voltT.setDACvoltage(voltage=float(v) / 1000, outputId=2)
                    
                    nbOfIntegrations = self.dt / 100
                    newCount = 0
                    for i in range(nbOfIntegrations):
                        time.sleep(0.1)  # 100 ms gate time on PicoHarp counters
                        rates = self.ph.getCountRates()
                        newCount += sum(rates) * 0.1  # counts on 100 ms integration bin
                    
                    self.buff.append(newCount / (float(self.dt) / 1000))
                    self.gotdata = True
                else:
                    break
                    
        finally:
            self.running = False
            self.ph.close()
            self.voltT.close()
#            self.voltT.ClearTask()
            
    def SW_run(self):
        """Runs in own thread - reads data via Swabian box"""
        
        self.v_step = pl.array([pl.linspace(self.v_i, self.v_f, self.no_of_steps) for i in range(self.repeats)]).flatten()
        try:
            
            self.tag = createTimeTagger()
            self.tag.setTriggerLevel(0, 0.2)
            self.tag.setTriggerLevel(1, 0.2)
            self.ctr = Counter(self.tag, [0,1], int(1e9), int(self.dt))
            self.tag.sync()
            for v in self.v_step:
                if self.running:
                    self.voltT.setDACvoltage(voltage=float(v) / 1000, outputId=2)
                    time.sleep(self.dt/1000.)
                    rates = self.ctr.getData()
                    newCount = (pl.mean(rates[0]) + pl.mean(rates[1]))*1000
                    self.buff.append(newCount)
                    # print self.measure_data
                    self.gotdata = True
                
        finally:
            self.ctr.stop()
            self.tag.reset()
            self.running = False
            self.btn.setEnabled(True)        
            
    def save(self):
        if self.running == False:
            filename = QtGui.QFileDialog.getSaveFileName(self, "Save file", self.file_path, "*.txt")
            self.file_path = dirname(str(filename))
            self.buff.extend([0 for i in range(len(self.v_step) - len(self.buff))])
            with open(str(filename),'wb') as f:
                pl.savetxt(f, pl.array([self.v_step, self.buff]).transpose(), fmt="%10.5f", delimiter=",")
        
        
if __name__ == "__main__":
       
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    myapp = MapWindow(app)
    myapp.show()
    app.exec_()