# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:20:31 2016

@author: raphael proux
"""

from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

import json
import visa
import pyqtgraph as pg
from Keithley import Keithley
import pylab as py
import threading
import time
from UiMultimeterOscillo import Ui_multimeterOscillo

# For working with python, pythonw and ipython
import sys, os
if sys.executable.endswith("pythonw.exe"):  # this allows pythonw not to quit immediately
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")

class VoltmeterThread (threading.Thread):
    def __init__(self, GPIBAddress=r'ASRL15::INSTR', timeStep=1):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.timeStep = timeStep
        try:
            self.voltmeter = Keithley(GPIBAddress)
        except:
            self.stop(errorHappened=True)
            raise
            
        self.measToRead = False
        self.measurementPoint = 0.
        
    def run(self):
        readTime = time.time() + self.timeStep
        while True:
            curTime = time.time()
            if curTime >= readTime:
                readTime = curTime + self.timeStep
                try:
                    self.measurementPoint = self.voltmeter.read()
                    self.measToRead = True
                except:
                    self.stop()
                    raise
            
            if self.stopped():
                break
            
    def stop(self, errorHappened=False):
        self._stop.set()
        try:
            self.voltmeter.close()
        except:
            if errorHappened:
                pass
            else:
                raise

    def stopped(self):
        return self._stop.isSet()

    
    
class VoltmeterRead(QWidget):
    
    
    def __init__(self, app, config):
        self.dialog = QWidget.__init__(self)
        self.app = app
        
        # Set up the user interface from Designer.
        self.ui = Ui_multimeterOscillo()
        self.ui.setupUi(self)
        
        # initialize gui variables
        self.voltMin = self.ui.min.value()
        self.voltMax = self.ui.max.value()
        self.timeStep = self.ui.tStep.value()
        self.timeWindow = self.ui.tWindow.value()

        # Connect up the buttons.
        self.ui.min.setKeyboardTracking(False)
        self.ui.max.setKeyboardTracking(False)
        self.ui.tStep.setKeyboardTracking(False)
        self.ui.tWindow.setKeyboardTracking(False)
        self.ui.min.valueChanged.connect(self.minMaxChanged)
        self.ui.max.valueChanged.connect(self.minMaxChanged)
        self.ui.tStep.valueChanged.connect(self.timeParamsChanged)
        self.ui.tWindow.valueChanged.connect(self.timeParamsChanged)
        self.ui.scalingFactor.valueChanged.connect(self.scalingFactorChanged)
        self.ui.rangeAutoscaleBox.toggled.connect(self.rangeAutoscaleBoxChanged)
        self.ui.nbMaxReadingReset.clicked.connect(self.nbMaxReadingReset)
        self.ui.nbMaxEnabled.toggled.connect(self.nbMaxEnabledToggled)
        self.ui.nbMinReadingReset.clicked.connect(self.nbMinReadingReset)
        self.ui.nbMinEnabled.toggled.connect(self.nbMinEnabledToggled)
        
        # open instrument using config dict
        try:
            self.voltmeter = VoltmeterThread(GPIBAddress=config['multimeterVisaId'], timeStep=self.timeStep)     
        except visa.VisaIOError:
            errorMessageWindow(self, 'Problem connecting with the multimeter', 'The program could not connect with the multimeter.\nPlease check the address of the device in the config dictionary of your script.')
            raise
            
        
        self.acquire = True
        self.timeParamsChanged = True
        self.scaleRefresh = True
        
        self.scalingFactor = 1.0
        self.maxValue = 0.
        self.maxReadingReset = True
        self.maxEnabled = True
        self.minValue = 0.
        self.minReadingReset = True
        self.minEnabled = True
        
        # launch program automatically
        QTimer.singleShot(100, self.acquisition)
        
    def acquisition(self):
        axisFont = QFont('Lucida')
        axisFont.setPointSize(30)
        
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        plotPen = pg.mkPen({'width': 4, 'color': 'y'})
        self.plotMaxPen = pg.mkPen({'width': 2, 'color': 'r'})
        self.plotMinPen = pg.mkPen({'width': 2, 'color': 'b'})
        
        bottom = self.ui.graphicsView.getPlotItem().getAxis('bottom')
        left = self.ui.graphicsView.getPlotItem().getAxis('left')
        
        bottom.setStyle(tickTextOffset=30, tickLength=10)
        left.setStyle(tickTextOffset=10, tickLength=10)
        
        bottom.setPen(axisPen)
        left.setPen(axisPen)
        
        bottom.tickFont = axisFont
        left.tickFont = axisFont
        
        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom.setLabel(text='Time', units='s', **labelStyle)
        left.setLabel(text='Voltage', units='V', **labelStyle)
        bottom.setHeight(100)
        left.setWidth(120)
        self.ui.graphicsView.setYRange(self.voltMin, self.voltMax)
        
        plot = self.ui.graphicsView.plot(pen=plotPen)
        self.plotMax = self.ui.graphicsView.plot(pen=self.plotMaxPen)
        self.plotMin = self.ui.graphicsView.plot(pen=self.plotMinPen)
        
        self.voltmeter.start()
        while self.acquire:
            
            if self.timeParamsChanged:
                nbOfSteps = int(abs(py.floor(float(self.timeWindow) / self.timeStep)) + 1)
                timeArray = py.linspace(-self.timeWindow, 0, nbOfSteps)
                measurementArray = py.zeros(nbOfSteps)
                
                self.timeParamsChanged = False
            
            if self.voltmeter.measToRead:
                self.voltmeter.measToRead = False
                measurementArray[0] = self.scalingFactor * self.voltmeter.measurementPoint
                measurementArray = py.roll(measurementArray, -1)
                plot.setData(timeArray, measurementArray)
                self.ui.nbReading.display('{:.5f}'.format(measurementArray[-1]))
                
                if self.maxReadingReset or measurementArray[-1] > self.maxValue:
                    self.maxValue = measurementArray[-1]
                    self.ui.nbMaxReading.display('{:.5f}'.format(self.maxValue))
                    self.plotMax.setData(py.array([timeArray[0], timeArray[-1]]), py.array([self.maxValue, self.maxValue]))
                    self.maxReadingReset = False
                
                if self.minReadingReset or measurementArray[-1] < self.minValue:
                    self.minValue = measurementArray[-1]
                    self.ui.nbMinReading.display('{:.5f}'.format(self.minValue))
                    self.plotMin.setData(py.array([timeArray[0], timeArray[-1]]), py.array([self.minValue, self.minValue]))
                    self.minReadingReset = False
                
            self.app.processEvents()
        
        self.voltmeter.stop()
            
    def stop(self):
        self.acquire = False
            
    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def minMaxChanged(self, event):
        if self.scaleRefresh:
            self.voltMin = self.ui.min.value()
            self.voltMax = self.ui.max.value()
            self.ui.graphicsView.setYRange(self.voltMin, self.voltMax)
         
    def timeParamsChanged(self, event):
        self.timeStep = self.ui.tStep.value()
        self.timeWindow = self.ui.tWindow.value()
        self.voltmeter.timeStep = self.timeStep
        self.timeParamsChanged = True
        
    def scalingFactorChanged(self, event):
        self.scalingFactor = event
        
    def rangeAutoscaleBoxChanged(self, event):
        autoscale = event
        YAxis = self.ui.graphicsView.getPlotItem().getViewBox().YAxis
        if autoscale:
            self.ui.graphicsView.enableAutoRange(axis=YAxis)
        else:
            self.ui.graphicsView.disableAutoRange(axis=YAxis)
            self.voltMin, self.voltMax = self.ui.graphicsView.viewRange()[1]
            self.scaleRefresh = False
            self.ui.max.setValue(self.voltMax)
            self.ui.min.setValue(self.voltMin)
            self.scaleRefresh = True
        
    def nbMaxReadingReset(self, event):
        self.maxReadingReset = True
    def nbMinReadingReset(self, event):
        self.minReadingReset = True
        
    def nbMaxEnabledToggled(self, event):
        self.maxEnabled = event
        if self.maxEnabled:
            self.plotMax.setPen(self.plotMaxPen)
            self.maxReadingReset = True
        else:
            self.plotMax.setPen(pg.mkPen(None))
            
    def nbMinEnabledToggled(self, event):
        self.minEnabled = event
        if self.minEnabled:
            self.plotMin.setPen(self.plotMinPen)
            self.minReadingReset = True
        else:
            self.plotMin.setPen(pg.mkPen(None))

    def close_instruments(self):
        self.voltmeter.close()
          
def errorMessageWindow(parentWindow, winTitle, winText):
    """ Displays a QT error message box, with title, text and OK button. """
    msg = QMessageBox(parentWindow)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(winTitle)
    msg.setText(winText)
    msg.exec_()
    
    
def multimeter_oscillo_run(config):
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = VoltmeterRead(app, config)

    try:
        # window.ui.setFocus(True)
        # window.setFocus(True)
        window.show()
        app.exec_()
    except:
        raise
    finally:
        window.closeInstruments()

if __name__ == "__main__":
    config = {"keithleyVisaId": "GPIB1::1::INSTR"}
    multimeter_oscillo_run(config)