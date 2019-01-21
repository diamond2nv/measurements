# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 15:42:15 2016

@author: Ralph N E Malein

Uses Lockin 7265 DAC 1 to control bias voltage on sample
Sweeps voltage from start to finish values, then reads APD / SNSPD

"""

import pylab as pl
import time
from PyQt4 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg
from os.path import dirname
import hydraHarp as hh

VISA_LOCKIN_ADDRESS = r'GPIB0::12::INSTR'


class MapWindow(QtGui.QWidget):

    
    def __init__(self, app):
        super(MapWindow, self).__init__()
        self.app = app
        self.init_ui()
        
        self.dt = 1
        self.no_of_steps = 1
        
        self.file_path = ""
        self.val_change()
        
    def init_ui(self):
        # defining widgets and layout
        self.graph = pg.PlotWidget()
        
        self.eta_box = QtGui.QStatusBar(self)
        
        self.time = QtGui.QDoubleSpinBox(self)
        self.time.setMaximum(9.9)
        self.time.setMinimum(0.1)
        self.time.setSingleStep(0.1)
        self.time.setDecimals(1)
        self.time.setValue(0.1)
        
        self.steps = QtGui.QSpinBox(self)
        self.steps.setMaximum(99999)
        self.steps.setValue(1)
        
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        self.sav = QtGui.QPushButton("Save", self)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.graph)
        vbox.addWidget(self.eta_box)
        vbox.addWidget(QtGui.QLabel("No. of steps"))
        vbox.addWidget(self.steps)
        vbox.addWidget(QtGui.QLabel("Time (ms)"))
        vbox.addWidget(self.time)
        vbox.addWidget(self.btn)
        vbox.addWidget(self.stp)
        vbox.addWidget(self.sav)
        
        self.setLayout(vbox)
        self.setGeometry(250, 80, 956, 900)
        self.setWindowTitle("Time trace")
        
        # connecting signals and sockets
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        self.sav.clicked.connect(self.save)
        self.time.valueChanged.connect(self.val_change)
        self.steps.valueChanged.connect(self.val_change)
        
        # graph style
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        self.plotPen0 = pg.mkPen({'width': 4, 'color': 'y'})
        self.plotPen1 = pg.mkPen({'width': 4, 'color': 'b'})
        
        bottom = self.graph.getPlotItem().getAxis('bottom')
        left = self.graph.getPlotItem().getAxis('left')
        
        bottom.setStyle(tickTextOffset=15, tickLength=10)
        left.setStyle(tickTextOffset=5, tickLength=10)
        
        bottom.setPen(axisPen)
        left.setPen(axisPen)
        
        bottom.tickFont = axisFont
        left.tickFont = axisFont
        
        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom.setLabel(text='Time', units='s', **labelStyle)
        left.setLabel(text='Counts', units="Hz", **labelStyle)
        bottom.setHeight(70)
        left.setWidth(80)
        YAxis = self.graph.getPlotItem().getViewBox().YAxis
        self.graph.enableAutoRange(axis=YAxis)
        XAxis = self.graph.getPlotItem().getViewBox().XAxis
        self.graph.enableAutoRange(axis=XAxis)
        
        self.show()
        
        
    def val_change(self):
        self.dt = int(self.time.value() * 1000)  # in ms
        self.no_of_steps = self.steps.value()
        
    def start(self):
        self.graph.clear()
        self.plot0 = self.graph.plot(pen=self.plotPen0)
        self.plot1 = self.graph.plot(pen=self.plotPen1)
        self.buff0 = []
        self.buff1 = []
        self.running = False
        self.gotdata = False
        self.btn.setEnabled(False)    
        self.runThread = threading.Thread(target=self.HH_run)
        now = time.time()
        then = now + self.no_of_steps*(float(self.dt) /1000)
        then_str = time.ctime(then)
        self.eta_box.showMessage("Estimated end:" + then_str)
        
        self.runThread.start()
        self.running = True
        while self.running:
            if self.gotdata:  
                self.graph.clear()
                self.plot0.setData(self.t_step[:len(self.buff0)],self.buff0)
                self.plot1.setData(self.t_step[:len(self.buff1)],self.buff1)
                self.gotdata = False
            self.app.processEvents()
            
        self.btn.setEnabled(True)
        
    def stop(self):
        self.running = False
        
        
    def HH_run(self):   
        """Runs in own thread - reads data via Picoharp counters"""
        
        self.t_step = pl.linspace(0, self.dt*self.no_of_steps, self.no_of_steps)
        try:
            self.hh = hh.HydraHarp()
            for t in self.t_step:
                if self.running:                    
                    nbOfIntegrations = self.dt / 100
                    newCount0 = 0
                    newCount1 = 0
                    for i in range(nbOfIntegrations):
                        time.sleep(0.1)  # 100 ms gate time on PicoHarp counters
                        rates = self.hh.getCountRates()
                        newCount0 += rates[0] * 0.1  # counts on 100 ms integration bin
                        newCount1 += rates[1] * 0.1
                    self.buff0.append(newCount0 / (float(self.dt) / 1000))
                    self.buff1.append(newCount1 / (float(self.dt) / 1000))
                    self.gotdata = True
                else:
                    break
                    
        finally:
            self.running = False
            self.hh.close()
            
            
    def save(self):
        if self.running == False:
            filename = QtGui.QFileDialog.getSaveFileName(self, "Save file", self.file_path, "*.txt")
            self.file_path = dirname(str(filename))
            pl.savetxt(str(filename), pl.array([self.t_step, self.buff0, self.buff1]).transpose(), fmt="%10.5f", delimiter=",")
        
        
if __name__ == "__main__":
       
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    myapp = MapWindow(app)
    myapp.show()
    app.exec_()