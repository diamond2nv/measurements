# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 17:27:46 2016

@author: Ralph N E Malein

Uses PFI0 from Weetabix (NI-USB 6341) to display USB counts every 0.1s
Displays curve of last 5s of data, counts indefinitely until Stop button press
MAY NEED "Start" TO BE PRESSED TWICE FOR SOME REASON
"""

import PyDAQmx as daq
import pylab as py
from PyQt4 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg


class Trigger(daq.Task):
    """Creates trigger counter task to determine counter timing"""
    def __init__(self, ctr, freq):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.freq = freq
        self.CreateCOPulseChanFreq("/Weetabix/ctr"+self.ctr, "trigger_"+self.ctr, 
                                   daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low, 0, 
                                   self.freq, 0.5)
        self.CfgImplicitTiming(daq.DAQmx_Val_ContSamps, 1000)
        
    def get_term(self):
        n = c_char_p(" ")
        self.GetCOPulseTerm("/Weetabix/ctr"+self.ctr, n, 20)
        return n.value
        
        
class InputCounter(daq.Task):
    """Creates input counter task tied to PFI0 to count APD pulses"""
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
        self.running = False
        
    def init_ui(self):
        self.lcd = QtGui.QLCDNumber(self)
        self.lcd.setMinimumSize(QtCore.QSize(300, 100))
        self.lcd.setDigitCount(7)
        self.lcd.setSegmentStyle(2)
        self.graph = pg.PlotWidget()
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.lcd)
        vbox.addWidget(self.graph)
        hbox = QtGui.QGridLayout()
        hbox.addWidget(self.btn)
        hbox.addWidget(self.stp)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)

        self.setGeometry(200, 200, 956, 704)
        self.setWindowTitle("Counter")
        
        
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        plotPen = pg.mkPen({'width': 4, 'color': 'y'})
        
        bottom = self.graph.getPlotItem().getAxis('bottom')
        left = self.graph.getPlotItem().getAxis('left')
        
        bottom.setStyle(tickTextOffset=15, tickLength=10)
        left.setStyle(tickTextOffset=5, tickLength=10)
        
        bottom.setPen(axisPen)
        left.setPen(axisPen)
        
        bottom.tickFont = axisFont
        left.tickFont = axisFont
        
        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom.setLabel(text='Time', units=None, **labelStyle)
        left.setLabel(text='Counts', units=None, **labelStyle)
        bottom.setHeight(70)
        left.setWidth(80)
        YAxis = self.graph.getPlotItem().getViewBox().YAxis
        self.graph.enableAutoRange(axis=YAxis)
        XAxis = self.graph.getPlotItem().getViewBox().XAxis
        self.graph.enableAutoRange(axis=XAxis)
        
        self.plot = self.graph.plot(pen=plotPen)
        
        self.show()
        
    def init_ctr(self):
        """Initialises counter tasks"""
        self.trig = Trigger(0, 100000)
        self.trig.StartTask()
        self.ctr = InputCounter(self.trig.get_term(), 1)
        
    def start(self):
        """Called upon start button press - initialises data then starts run thread"""
        self.buff = []
        self.gotdata = False
        self.init_ctr()
        self.btn.setDisabled(True)
        self.runThread = threading.Thread(target=self.run)        
        self.runThread.start()  
        self.running = True
        while self.running:
            if self.gotdata:
                self.plot.setData(self.measure_data)
                self.lcd.display(self.measure_data[-1])
                self.gotdata = False
            self.app.processEvents()        
        
    def stop(self):
        """Prematurely stops run thread"""
        self.running = False
        
    def run(self):   
        """Runs in own thread - reads data via input counter task"""
        self.measure_data = py.zeros((50,))
        try:            
            while self.running:
                self.ctr.data = py.zeros((10000,), dtype=py.uint32)
                self.ctr.ReadCounterU32(10000, 10., self.ctr.data, 10000, None, None)
                self.ctr.StopTask()
                self.measure_data[0] = (self.ctr.data[-1])*10
                self.measure_data[py.isinf(self.measure_data)] = py.nan
                self.measure_data = py.roll(self.measure_data, -1)                
                print self.measure_data
                self.gotdata = True              
        finally:
            self.running = False
            self.ctr.StopTask()
            self.ctr.ClearTask()
            self.trig.ClearTask()
            self.btn.setEnabled(True)            
        
        
if __name__ == "__main__":       
    app = QtGui.QApplication(sys.argv)
    myapp = MapWindow(app)
    myapp.show()
    sys.exit(app.exec_())
