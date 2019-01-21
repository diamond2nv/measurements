# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 15:42:15 2016

@author: Ralph N E Malein

Uses PFI0 from Weetabix (NI-USB 6341) to display USB counts every 0.1s
Sweeps voltage from start to finish values, then reads APD
Timer currently just delay, does not change integration time
"""

import PyDAQmx as daq
from LockIn7265 import LockIn7265

import pylab as py
import time
from PyQt4 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg
from os.path import dirname

VISA_LOCKIN_ADDRESS = r'GPIB0::12::INSTR'

class Trigger(daq.Task):
    def __init__(self, ctr, freq):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.freq = freq
        
        print repr(self.freq)
        self.CreateCOPulseChanFreq("/Weetabix/ctr"+self.ctr, "trigger_"+self.ctr, 
                                   daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low, 0, 
                                   self.freq, 0.5)
        self.CfgImplicitTiming(daq.DAQmx_Val_ContSamps, 1000)

        
    def get_term(self):
        n = c_char_p(" ")
        self.GetCOPulseTerm("/Weetabix/ctr"+self.ctr, n, 20)
        return n.value
        
        
class InputCounter(daq.Task):
    def __init__(self, gate_term, ctr="1"):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.data = py.zeros((10,),dtype=py.uint32)
        self.CreateCICountEdgesChan("Weetabix/ctr"+self.ctr, "ctr"+self.ctr, 
                                    daq.DAQmx_Val_Rising, 0, 
                                    daq.DAQmx_Val_CountUp)
        self.CfgSampClkTiming(gate_term, 10000, daq.DAQmx_Val_Rising, 
                              daq.DAQmx_Val_ContSamps, 10000)
        self.SetCICountEdgesTerm("/Weetabix/ctr"+self.ctr, "/Weetabix/PFI0")

        
    def read_counts(self):
        self.StopTask()
        self.data = py.zeros((10000,),dtype=py.uint32)
        self.ReadCounterU32(10000, 10., self.data, 10000, None, None)
        return self.data
        

class MapWindow(QtGui.QWidget):
    def __init__(self, app):
        super(MapWindow, self).__init__()
        self.app = app
        self.init_ui()
        
        self.v_i = 0.
        self.v_f = 0.
        self.dt = 1
        self.no_of_steps = 1
        
        self.file_path = ""
        
    def init_ui(self):
        self.graph = pg.PlotWidget()
        self.eta_box = QtGui.QStatusBar(self)
        self.start_v = QtGui.QDoubleSpinBox(self)
        self.start_v.setMinimum(-10.)
        self.start_v.setDecimals(3)
        self.start_v.setSingleStep(0.1)
        self.end_v = QtGui.QDoubleSpinBox(self)
        self.end_v.setMinimum(-10.)
        self.end_v.setDecimals(3)
        self.end_v.setSingleStep(0.1)
        self.time = QtGui.QSpinBox(self)
        self.time.setMaximum(9999)
        self.time.setMinimum(100)
        self.time.setValue(100)
        self.steps = QtGui.QSpinBox(self)
        self.steps.setMaximum(99999)
        self.steps.setValue(1)
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        self.sav = QtGui.QPushButton("Save", self)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.graph)
        vbox.addWidget(self.eta_box)
        vbox.addWidget(QtGui.QLabel("Start Voltage"))
        vbox.addWidget(self.start_v)
        vbox.addWidget(QtGui.QLabel("End Voltage"))
        vbox.addWidget(self.end_v)
        vbox.addWidget(QtGui.QLabel("Time (ms)"))
        vbox.addWidget(self.time)
        vbox.addWidget(QtGui.QLabel("No. of steps"))
        vbox.addWidget(self.steps)
        vbox.addWidget(self.btn)
        vbox.addWidget(self.stp)
        vbox.addWidget(self.sav)
        
        self.setLayout(vbox)
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        self.sav.clicked.connect(self.save)
        self.start_v.valueChanged.connect(self.val_change)
        self.end_v.valueChanged.connect(self.val_change)
        self.time.valueChanged.connect(self.val_change)
        self.steps.valueChanged.connect(self.val_change)
        
        self.setGeometry(200, 200, 956, 704)
        self.setWindowTitle("Volt Sweep")
        
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        self.plotPen = pg.mkPen({'width': 4, 'color': 'y'})
        
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
        
    def init_ctr(self, intTime=100):
        # intTime in milliseconds
        frequency = int(py.ceil(1.0e7 / float(intTime)))
        self.trig = Trigger(0, frequency)
        self.trig.StartTask()
        self.ctr = InputCounter(self.trig.get_term(), 1)
        
        
    def val_change(self):
        self.v_i = self.start_v.value()
        self.v_f = self.end_v.value()
        self.dt = int(self.time.value())
        self.no_of_steps = self.steps.value()
        
    def start(self):
        self.init_ctr(intTime=self.dt)
        self.graph.clear()
        self.plot = self.graph.plot(pen=self.plotPen)
        self.buff = []
        self.running = False
        self.gotdata = False
        self.btn.setEnabled(False)
        self.voltT = LockIn7265(VISA_LOCKIN_ADDRESS)
        self.runThread = threading.Thread(target=self.run)
        now = time.time()
        then = now + self.no_of_steps*(self.dt/1000)
        then_str = time.ctime(then)
        self.eta_box.showMessage("Estimated end:" + then_str)
        
        self.runThread.start()
        self.running = True
        while self.running:
            if self.gotdata:                
                self.plot.setData(self.v_step[:len(self.buff)],self.buff)
                self.gotdata = False
            self.app.processEvents()
            
        self.btn.setEnabled(True)
        
    def stop(self):
        self.running = False
        
    def run(self):
        
        self.v_step = py.linspace(self.v_i,self.v_f,self.no_of_steps)
        try:
            for v in self.v_step:
                if self.running:
                    self.voltT.setDACvoltage(voltage=v)
                    self.ctr.data = py.zeros((10000,), dtype=py.uint32)
                    self.ctr.StartTask()
                    #time.sleep(float(self.dt)/1000)
                    self.ctr.ReadCounterU32(10000, 10., self.ctr.data, 10000, None, None)
                    self.ctr.StopTask()
                    data = float((self.ctr.data[-1])) / self.dt * 1000
                    self.buff.append(data)                    
                    self.gotdata = True
                    #print v
        finally:
            self.running = False
            self.ctr.StopTask()
            self.voltT.close()
            self.ctr.ClearTask()
#            self.voltT.ClearTask()
            self.trig.ClearTask()
        
    def save(self):
        if self.running == False:
            filename = QtGui.QFileDialog.getSaveFileName(self, "Save file", self.file_path, "*.txt")
            self.file_path = dirname(str(filename))
            py.savetxt(str(filename), [self.v_step, self.buff], fmt="%10.5f", delimiter=",")
        
        
if __name__ == "__main__":
       
    app = QtGui.QApplication(sys.argv)
    myapp = MapWindow(app)
    myapp.show()
    sys.exit(app.exec_())