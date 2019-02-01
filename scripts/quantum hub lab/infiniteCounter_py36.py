# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 17:27:46 2016

@author: Ralph N E Malein

Uses PFI0 from Weetabix (NI-USB 6341) to display USB counts every 0.1s
Displays curve of last 5s of data, counts indefinitely until Stop button press

"""

import PyDAQmx as daq
import pylab as pl
from PyQt5 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg
import picoHarp as ph
import time
import sys
sys.path.insert(0, "C:/Program Files (x86)/Swabian Instruments/Time Tagger/API/Python3.6/x64")
from TimeTagger import createTimeTagger, Counter, Countrate

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
    """Creates input counter task tied to PFI1 to count APD pulses"""
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
        self.dt = 50  # self.dt is in milliseconds 
        self.counterDev = 0
        self.detID = 0
        self.running = False
        self.val_change()
        
    def init_ui(self):
        # defining widgets and layout
        self.lcd = QtGui.QLCDNumber(self)
        self.lcd.setMinimumSize(QtCore.QSize(300, 100))
        self.lcd.setDigitCount(7)
        self.lcd.setSegmentStyle(2)
        
        self.graph = pg.PlotWidget()
        
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        
        self.time = QtGui.QDoubleSpinBox(self)
        self.time.setMaximum(9.9)
        self.time.setMinimum(0.001)
        self.time.setSingleStep(0.001)
        self.time.setDecimals(3)
        self.time.setValue(0.1)
        
        self.cb = QtGui.QComboBox()
        self.cb.addItems(["National Instruments box", "PicoHarp", "Swabian"])
        self.cb.setCurrentIndex(self.SWABIAN)
        self.detCb = QtGui.QComboBox()
        self.detCb.addItems(["Channel 0", "Channel 1", "Both channels summed"])
        self.detCb.setCurrentIndex(0)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.lcd)
        vbox.addWidget(self.graph)
        hbox = QtGui.QGridLayout()
        hbox.addWidget(QtGui.QLabel("Integration time (s)"))
        hbox.addWidget(self.time)
        hbox.addWidget(self.cb)
        hbox.addWidget(self.detCb)
        hbox.addWidget(self.btn)
        hbox.addWidget(self.stp)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)

        self.setGeometry(200, 150, 956, 800)
        self.setWindowTitle("Counter")
        
        # connecting signals and sockets
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        
        self.time.valueChanged.connect(self.val_change)
        self.cb.currentIndexChanged.connect(self.val_change)
        self.detCb.currentIndexChanged.connect(self.val_change)
        
        # graph style
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        plotPen = pg.mkPen({'width': 1, 'color': 'y'})
        
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
        

    def val_change(self):
        self.dt = int(self.time.value() * 1000)  # self.dt is in milliseconds
        self.counterDev = self.cb.currentIndex()
        self.detID = self.detCb.currentIndex()
        if self.counterDev == self.NI_BOX:
            self.detCb.setDisabled(True)
        else:
            self.detCb.setDisabled(False)
        
    def start(self):
        """Called upon start button press - initialises data then starts run thread"""
        self.buff = []
        self.gotdata = False
        self.running = True
        self.btn.setDisabled(True)
        if self.counterDev == self.NI_BOX:
            self.NI_init_ctr(intTime=self.dt)
            self.runThread = threading.Thread(target=self.NI_run)  
        elif self.counterDev == self.PICOHARP:
            self.runThread = threading.Thread(target=self.PH_run)
        else:
            self.runThread = threading.Thread(target=self.SW_run)
              
        self.runThread.start()  
        while self.running:
            if self.gotdata:
                self.plot.setData(self.measure_data)
                self.lcd.display(self.measure_data[-1])
                self.gotdata = False
            self.app.processEvents()
        
    def stop(self):
        """Prematurely stops run thread"""
        self.running = False
        
    def NI_init_ctr(self, intTime=100):
        # intTime in milliseconds
        frequency = int(pl.ceil(1.0e7 / float(intTime)))
        self.trig = Trigger(0, frequency)
        self.trig.StartTask()
        self.ctr = InputCounter(self.trig.get_term(), 1)
        
    def NI_run(self):   
        """Runs in own thread - reads data via input counter task"""
        self.measure_data = pl.zeros((50,))
        dt = self.dt
        try:            
            while self.running:
                self.ctr.data = pl.zeros((10000,), dtype=pl.uint32)
                self.ctr.ReadCounterU32(10000, 10., self.ctr.data, 10000, None, None)
                self.ctr.StopTask()
                self.measure_data[0] = float((self.ctr.data[-1])) / dt * 1000
                self.measure_data[pl.isinf(self.measure_data)] = pl.nan
                self.measure_data = pl.roll(self.measure_data, -1)
                #print self.measure_data
                self.gotdata = True
        finally:
            self.running = False
            self.ctr.StopTask()
            self.ctr.ClearTask()
            self.trig.ClearTask()
            self.btn.setEnabled(True)       
    
    def PH_run(self):   
        """Runs in own thread - reads data via Picoharp counters"""
        self.measure_data = pl.zeros((50,))
        try:
            self.ph = ph.PicoHarp()
            if self.dt < 0.1:
                print ("Integration time too short! Changed to 0.1s")
                self.dt = 0.1
                self.time.setValue(0.1)
            while self.running:
                nbOfIntegrations = self.dt / 100
                newCount = 0
                for i in range(nbOfIntegrations):
                    time.sleep(0.1)  # 100 ms gate time on PicoHarp counters
                    rates = self.ph.getCountRates()
                    if self.detID == 0:
                        newCount += rates[0] * 0.1  # counts on 100 ms integration bin
                    elif self.detID == 1:
                        newCount += rates[1] * 0.1  # counts on 100 ms integration bin
                    else:
                        newCount += sum(rates) * 0.1  # counts on 100 ms integration bin
                self.measure_data[0] = newCount / (float(self.dt) / 1000)
                self.measure_data = pl.roll(self.measure_data, -1)
                #print (self.measure_data)
                self.gotdata = True
        finally:
            self.running = False
            self.ph.close()
            self.btn.setEnabled(True)     
        
    def SW_run(self):
        """Runs in own thread - reads data via Swabian box"""
        self.measure_data = pl.zeros((50,))
        try:
            self.tag = createTimeTagger()
            self.tag.setTriggerLevel(0, 0.15)
            self.tag.setTriggerLevel(1, 0.15)
            self.ctr = Counter(self.tag, [0,1], int(1e9), int(self.dt))
            while self.running:
                time.sleep(self.dt/1000.)
                rates = self.ctr.getData()
                if self.detID == 0:
                    newCount = pl.mean(rates[0])*1000
                elif self.detID == 1:
                    newCount = pl.mean(rates[1])*1000
                else:
                    newCount = (pl.mean(rates[0]) + pl.mean(rates[1]))*1000
                self.measure_data[0] = newCount
                self.measure_data = pl.roll(self.measure_data, -1)
                print (self.measure_data)
                self.gotdata = True
                
        finally:
            self.ctr.stop()
            self.tag.reset()
            self.running = False
            self.btn.setEnabled(True)
                
    
    
if __name__ == "__main__":       
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    myapp = MapWindow(app)
    myapp.show()
    app.exec_()
