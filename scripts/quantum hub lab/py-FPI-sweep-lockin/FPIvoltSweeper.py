# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 15:42:15 2016

@author: Ralph N E Malein

Uses Lockin 7265 DAC 1 to control bias voltage on sample
Sweeps voltage from start to finish values, then reads APD / SNSPD

"""

import PyDAQmx as daq
from LockIn7265 import LockIn7265
from AgilentMultimeter import AgilentMultimeter

import pylab as pl
import time
from PyQt4 import QtCore, QtGui
import threading
import sys
from ctypes import *
import pyqtgraph as pg
import os.path
import picoHarp as ph
import re
from TimeTagger import createTimeTagger, Counter

VISA_LOCKIN_ADDRESS = r'GPIB0::12::INSTR'

class Trigger(daq.Task):
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
    def __init__(self, gate_term, ctr="1"):
        daq.Task.__init__(self)
        self.ctr = str(ctr)
        self.data = pl.zeros((10,),dtype=pl.uint32)
        self.CreateCICountEdgesChan("Weetabix/ctr"+self.ctr, "ctr"+self.ctr, 
                                    daq.DAQmx_Val_Rising, 0, 
                                    daq.DAQmx_Val_CountUp)
        self.CfgSampClkTiming(gate_term, 10000, daq.DAQmx_Val_Rising, 
                              daq.DAQmx_Val_ContSamps, 10000)
        self.SetCICountEdgesTerm("/Weetabix/ctr"+self.ctr, "/Weetabix/PFI0")

        
    def read_counts(self):
        self.StopTask()
        self.data = pl.zeros((10000,),dtype=pl.uint32)
        self.ReadCounterU32(10000, 10., self.data, 10000, None, None)
        return self.data
    
class MapWindow(QtGui.QWidget):
    NI_BOX = 0
    PICOHARP = 1
    MULTIMETER = 2
    SWABIAN = 3
    
    def __init__(self, app):
        super(MapWindow, self).__init__()
        self.app = app
        
        self.v_i = -0.5
        self.v_f = 0.5
        self.dt = 0.01
        self.no_of_steps = 2
        self.step_size = 10
        
        self.nb_of_scans = 1
        
        self.v_step = []
        self.buffer = []
        self.data = []
        
        self.stopScans = True
        self.running = False
        
        self.backAndForthMode = False
        self.goBack = False
        
        self.mustSaveFile = False
        
        self.file_path = ""
        
        self.init_ui()
        self.val_change()
        
    def init_ui(self):
        # defining widgets and layout
        self.graph = pg.PlotWidget()
        
        self.start_v = QtGui.QDoubleSpinBox(self)
        self.start_v.setMinimum(-10.000)
        self.start_v.setMaximum(10.000)
        self.start_v.setDecimals(3)
        self.start_v.setSingleStep(0.100)
        self.start_v.setValue(self.v_i)
        
        self.end_v = QtGui.QDoubleSpinBox(self)
        self.end_v.setMinimum(-10.000)
        self.end_v.setMaximum(10.000)
        self.end_v.setDecimals(3)
        self.end_v.setSingleStep(0.100)
        self.end_v.setValue(self.v_f)
        
        self.steps = QtGui.QSpinBox(self)
        self.steps.setMaximum(99999)
        self.steps.setValue(self.no_of_steps)
        
        self.step_size_field = QtGui.QSpinBox(self)
        self.step_size_field.setMaximum(10000)
        self.step_size_field.setMinimum(1)
        self.step_size_field.setSingleStep(1)
        self.step_size_field.setValue(self.step_size)
        
        self.time = QtGui.QDoubleSpinBox(self)
        self.time.setMaximum(9.9)
        self.time.setMinimum(0.001)
        self.time.setSingleStep(0.001)
        self.time.setDecimals(3)
        self.time.setValue(self.dt)
        
        self.cb = QtGui.QComboBox()
        self.cb.addItems(["National Instruments box", "PicoHarp", "Agilent multimeter", "Swabian"])
        self.cb.setCurrentIndex(self.SWABIAN)
        
        self.scanNb_field = QtGui.QSpinBox(self)
        self.scanNb_field.setMaximum(99999)
        self.scanNb_field.setMinimum(0)
        self.scanNb_field.setValue(self.nb_of_scans)
        self.backAndForthCheckBox = QtGui.QCheckBox("Back and forth", self)
        
                
        self.btn = QtGui.QPushButton("Start", self)
        self.stp = QtGui.QPushButton("Stop", self)
        
        self.saveCheckBox = QtGui.QCheckBox("Save continuously", self)
        self.savePath = QtGui.QLineEdit(self)
        self.savePath.setPlaceholderText("Filepath")
        self.savePathBut = QtGui.QPushButton("Select file name", self)
        self.sav = QtGui.QPushButton("Save", self)
        
        self.statusFileLineEdit = QtGui.QLineEdit(self)
        self.statusFileLineEdit.setPlaceholderText("File status messages")
        self.statusFileLineEdit.setContentsMargins(0,10,0,0)
        self.statusFileLineEdit.setStyleSheet("background-color: rgb(240, 240, 240);")
        self.statusFileLineEdit.setReadOnly(True)
        
        self.statusScanLineEdit = QtGui.QLineEdit(self)
        self.statusScanLineEdit.setPlaceholderText("Scan status messages")
        self.statusScanLineEdit.setStyleSheet("background-color: rgb(240, 240, 240);")
#        self.statusScanLineEdit.setContentsMargins(0,0,0,10)
        self.statusScanLineEdit.setReadOnly(True)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.graph)
        
        vbox.addWidget(QtGui.QLabel("Start Voltage"))
        vbox.addWidget(self.start_v)
        vbox.addWidget(QtGui.QLabel("End Voltage"))
        vbox.addWidget(self.end_v)
        vbox.addWidget(QtGui.QLabel("No. of steps"))
        vbox.addWidget(self.steps)
        vbox.addWidget(QtGui.QLabel("Step size (mV)"))
        vbox.addWidget(self.step_size_field)
        vbox.addWidget(self.cb)
        vbox.addWidget(QtGui.QLabel("Time (s)"))
        vbox.addWidget(self.time)
        
        scanBox = QtGui.QHBoxLayout()
        scanBox.addWidget(QtGui.QLabel("No. of scans (0 for infinite)"))
        scanBox.addWidget(self.scanNb_field)
        scanBox.addWidget(self.backAndForthCheckBox)
        
        scanBox.addWidget(self.statusScanLineEdit)
#        scanBox.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        vbox.addLayout(scanBox)
        
        buttonsBox = QtGui.QHBoxLayout()
        buttonsBox.addWidget(self.btn)
        self.btn.setMinimumHeight(35)
        self.btn.setFont(QtGui.QFont("MS Shell Dlg 2", 15) )
        buttonsBox.addWidget(self.stp)
        self.stp.setMinimumHeight(35)
        self.stp.setFont(QtGui.QFont("MS Shell Dlg 2", 15) )
        buttonsBox.setContentsMargins(0,10,0,0)
        
        
        
        saveBox = QtGui.QHBoxLayout()
        saveBox.addWidget(self.saveCheckBox)
        saveBox.addWidget(self.savePath)
        saveBox.addWidget(self.savePathBut)
        saveBox.setContentsMargins(0,20,0,0)
        
        vbox.addLayout(buttonsBox)
        vbox.addLayout(saveBox)
        
        vbox.addWidget(self.sav)
        vbox.addWidget(self.statusFileLineEdit)
        
        self.setLayout(vbox)
        self.setGeometry(250, 80, 956, 900)
        self.setWindowTitle("FPI Volt Sweep with lockin")
        
        # connecting signals and sockets
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        self.sav.clicked.connect(self.save)
        self.savePathBut.clicked.connect(self.savePathChange)
        self.start_v.valueChanged.connect(self.val_change)
        self.end_v.valueChanged.connect(self.val_change)
        self.time.valueChanged.connect(self.val_change)
        self.steps.valueChanged.connect(self.val_change)
        self.step_size_field.valueChanged.connect(self.val_change)
        self.cb.currentIndexChanged.connect(self.val_change)
        self.scanNb_field.valueChanged.connect(self.val_change)
        self.saveCheckBox.toggled.connect(self.saveContChecked)
        self.backAndForthCheckBox.toggled.connect(self.val_change)
        
        # graph style
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)
    
        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        self.plotPen = pg.mkPen({'width': 4, 'color': 'y'})
        self.scanIndicatorPen = pg.mkPen({'width': 4, 'color': 'y'})
        
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
        left.setLabel(text='Signal (V or counts/s)', **labelStyle)
        bottom.setHeight(70)
        left.setWidth(80)
        YAxis = self.graph.getPlotItem().getViewBox().YAxis
        self.graph.enableAutoRange(axis=YAxis)
        XAxis = self.graph.getPlotItem().getViewBox().XAxis
        self.graph.enableAutoRange(axis=XAxis)
        
        self.show()
        
        
    def val_change(self):
        self.stop()
        self.v_i = int(pl.floor(self.start_v.value() * 1000))  # in mV
        self.v_f = int(pl.ceil(self.end_v.value() * 1000))  # in mV
        self.dt = int(self.time.value() * 1000)  # in ms
        if self.no_of_steps == self.steps.value():  # step_size was modified
            self.step_size = self.step_size_field.value()  # in mV
            self.no_of_steps = int(abs(float(self.v_f - self.v_i)) // self.step_size) + 1
            self.steps.setValue(self.no_of_steps)
        else:  # no_of_steps was modified
            self.no_of_steps = self.steps.value()
            self.step_size = int(abs(float(self.v_f - self.v_i)) / (self.no_of_steps - 1))
            self.step_size_field.setValue(self.step_size)
        
        self.counterDev = self.cb.currentIndex()
        self.nb_of_scans = self.scanNb_field.value()
        self.backAndForthMode = self.backAndForthCheckBox.isChecked()
        
    def start(self):
        self.times = False
        self.graph.clear()
        self.plot = self.graph.plot(pen=self.plotPen)
        self.scanIndicator = self.graph.plot(symbolPen=self.scanIndicatorPen)
        self.buff = []
        self.running = False
        self.gotdata = False
        self.btn.setEnabled(False)
        self.updateStatusScanField('Please wait...')
        self.app.processEvents()
        
        self.v_step = pl.linspace(self.v_i, self.v_i + self.step_size * (self.no_of_steps - 1), self.no_of_steps)#, dtype=int)
        self.data = pl.zeros(len(self.v_step))
        
        self.stopScans = False
        counts = 0
        self.goBack = False
        
        # start instruments before the loop
        try:
            self.voltT = LockIn7265(VISA_LOCKIN_ADDRESS)
            self.res_v = self.voltT.getDACvoltage(outputId=1)
            self.startSelectedInstrument(self.counterDev)
        
            while True:
                if self.stopScans == True or (self.nb_of_scans > 0 and counts >= self.nb_of_scans):
    #                print 'stopscans', self.stopScans, '   nb_of_scans', self.nb_of_scans, '   counts', counts
                    break
                
                if self.counterDev == self.NI_BOX:
                    self.runThread = threading.Thread(target=self.NI_run)  
                elif self.counterDev == self.MULTIMETER:
                    self.runThread = threading.Thread(target=self.Voltmeter_run)
                elif self.counterDev == self.PICOHARP:
                    self.runThread = threading.Thread(target=self.PH_run)
                else:
                    self.runThread = threading.Thread(target=self.SW_run)
                
                self.buff = []
                self.runThread.start()
                self.running = True
                while True:
                    if self.gotdata or self.running == False:  # one last check for data if running = False
                        curPointIndex = len(self.buff) - 1
    #                    print curPointIndex,'/',len(self.data) - 1
    #                    print self.runThread.isAlive()
                        if self.goBack:
                            curPointIndex = -curPointIndex-1
                            self.data[curPointIndex:] = pl.array(self.buff[::-1])
                        else:
                            self.data[0:curPointIndex+1] = pl.array(self.buff)
                        self.plot.setData(self.v_step.astype(float) / 1000, self.data)
                        self.scanIndicator.setData([float(self.v_step[curPointIndex])/1000], [self.data[curPointIndex]])
                        self.gotdata = False
                        if self.running == False:
                            break
                    self.app.processEvents()
                    
                
                while self.runThread.isAlive():  # should be pretty fast
                    pass
                
                if self.mustSaveFile:
                    self.save()
                    
                counts += 1
                
                if self.backAndForthMode:
                    self.goBack = not self.goBack
        except:
            self.updateStatusScanField('ERROR: Problem communicating with one or several instruments.')
            raise
        else:
            self.updateStatusScanField('No scan happening.')
        finally:
            try:
                try:
                    self.voltT.close()
                except:
                    raise
                finally:
                    self.closeSelectedInstrument(self.counterDev)
                
            except:
                self.updateStatusScanField('ERROR: Problem communicating with one or several instruments.')
            finally:
                self.scanIndicator.setData([],[])
                self.btn.setEnabled(True)
        
    def stop(self):
        self.running = False
        self.stopScans = True
        
    def startSelectedInstrument(self, counterDevice):
        if counterDevice == self.NI_BOX:
            self.NI_init_ctr(intTime=self.dt) 
        elif counterDevice == self.MULTIMETER:
            self.multi = AgilentMultimeter(r'GPIB0::23::INSTR')
        elif counterDevice == self.PICOHARP:
            self.ph = ph.PicoHarp()
        else:
            self.tag = createTimeTagger()
            self.tag.setTriggerLevel(0, 0.1)
            self.tag.setTriggerLevel(1, 0.1)
            self.tag.autoCalibration()
            
    def closeSelectedInstrument(self, counterDevice):
        if counterDevice == self.NI_BOX:
            self.ctr.StopTask()
            self.ctr.ClearTask()
            self.trig.ClearTask()
        elif counterDevice == self.MULTIMETER:
            self.multi.close()
        elif counterDevice == self.PICOHARP:
            self.ph.close()
        else:
            self.tag.reset()
        
        
        
    def NI_init_ctr(self, intTime=100):
        # intTime in milliseconds
        frequency = int(pl.ceil(1.0e7 / float(intTime)))
        self.trig = Trigger(0, frequency)
        self.trig.StartTask()
        self.ctr = InputCounter(self.trig.get_term(), 1)
        
    def NI_run(self):
        
        try:
            # change messages and step vector if back and forth mode activated
            if self.goBack:
                voltSteps = self.v_step[::-1]
                scanMessage = 'Scanning backwards...'
            else:
                voltSteps = self.v_step
                if self.backAndForthMode:
                    scanMessage = 'Scanning forward...'
                else:
                    scanMessage = 'Scanning...'
            
            # go smoothly to start position 
            self.updateStatusScanField('Please wait, going to start position.')
            self.voltT.lockinGoSmoothlyToVoltage(voltSteps[0], outputId=2, delay=0.01)
            
            # start measurement scan
            self.updateStatusScanField(scanMessage)
            for v in voltSteps:
                if self.running:
                    self.voltT.setDACvoltage(outputId=2, voltage=float(v) / 1000)
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
        
    def Voltmeter_run(self):   
        """Runs in own thread - reads data via Voltmeter value"""
        
        try:
            # change messages and step vector if back and forth mode activated
            if self.goBack:
                voltSteps = self.v_step[::-1]
                scanMessage = 'Scanning backwards...'
            else:
                voltSteps = self.v_step
                if self.backAndForthMode:
                    scanMessage = 'Scanning forward...'
                else:
                    scanMessage = 'Scanning...'
            
            # go smoothly to start position 
            self.updateStatusScanField('Please wait, going to start position.')
            self.voltT.lockinGoSmoothlyToVoltage(voltSteps[0], outputId=2, delay=0.01)
            
            # start measurement scan
            self.updateStatusScanField(scanMessage)
            for v in voltSteps:
                if self.running:
                    self.voltT.setDACvoltage(outputId=2, voltage=float(v) / 1000)
                    time.sleep(float(self.dt) / 1000)
                    
                    self.buff.append(self.multi.read())
                    self.gotdata = True
                else:
                    break
#            time.sleep(0.05)  # to recover the last point
        finally:
            self.running = False
            
    def PH_run(self):   
        """Runs in own thread - reads data via Picoharp counters"""
        
        try:
            # change messages and step vector if back and forth mode activated
            if self.goBack:
                voltSteps = self.v_step[::-1]
                scanMessage = 'Scanning backwards...'
            else:
                voltSteps = self.v_step
                if self.backAndForthMode:
                    scanMessage = 'Scanning forward...'
                else:
                    scanMessage = 'Scanning...'
            
            # go smoothly to start position 
            self.updateStatusScanField('Please wait, going to start position.')
            self.voltT.lockinGoSmoothlyToVoltage(voltSteps[0], outputId=2, delay=0.01)
            
            # start measurement scan
            self.updateStatusScanField(scanMessage)
            for v in voltSteps:
                if self.running:
#                    print v, repr(self.voltT), self.voltT.dev.resource_info
                    self.voltT.setDACvoltage(outputId=2, voltage=float(v) / 1000)
                    time.sleep(self.dt)
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
            
    def SW_run(self):
        """Runs in own thread - reads data via Swabian box"""
        self.ctr = Counter(self.tag, [0],  int(1000000000) , int(30*self.no_of_steps))
        self.ctr.clear()
        
        try:
            
            if self.goBack:
                voltSteps = self.v_step[::-1]
                scanMessage = 'Scanning backwards... (off resonance)'
                self.voltT.setDACvoltage(outputId=1, voltage=self.res_v+0.1)
            else:
                voltSteps = self.v_step
                if self.backAndForthMode:
                    scanMessage = 'Scanning forward.. (on resonance)'
                    self.voltT.setDACvoltage(outputId=1, voltage=self.res_v)
                else:
                    scanMessage = 'Scanning...'
                    
            # go smoothly to start position
            self.updateStatusScanField('Please wait, going to start position.')
            self.voltT.lockinGoSmoothlyToVoltage(voltSteps[0], outputId=2, delay=0.001)
            
            # start measurement scan
            self.updateStatusScanField(scanMessage)
            
            start = time.clock()
            self.times = []
            self.tag.sync()
            start = time.clock()
            self.ctr.clear()
            for v in voltSteps:
                if self.running:
                    self.voltT.setDACvoltage(outputId=2, voltage=float(v)/1000)
                    self.times.append((time.clock()-start)*1000)
                    time.sleep(self.dt/1000.)
                                                            
                else:
                    break
            data = self.ctr.getData()[0]
            for i in self.times:
                self.buff.append(sum(data[int(-i-self.dt):int(-i)]))
                print i, i+self.dt
            print data
            self.gotdata = True
        finally:
            self.running = False
            
    def save(self, recursive=False):
            
        if self.running == False:
            savePathStr = str(self.savePath.text())
#            print savePathStr
            if not os.path.isfile(savePathStr):
                self._saveFileXY(savePathStr, self.v_step, self.data)
                if recursive:
                    self.updateStatusFileField('To avoid erasing an old file, your file has been saved as {}'.format(os.path.basename(savePathStr)))
                else:
                    self.updateStatusFileField('Your file has been saved as {}'.format(os.path.basename(savePathStr)))
            else:  # increment name
                path_to_file, name_of_file = os.path.split(savePathStr)
                name_of_file, file_ext = os.path.splitext(name_of_file)
#                print name_of_file
                reFileName = re.search('(?P<mainText>.*)_IT(?P<iterNb>\d+)', name_of_file)
                if reFileName is None:
                    newFilename = '{}_IT{}{}'.format(name_of_file, 0, file_ext)
                else:
                    resdic = reFileName.groupdict()
                    newFilename = '{}_IT{}{}'.format(resdic['mainText'], int(resdic['iterNb'])+1, file_ext)
                savePathStr = os.path.join(path_to_file, newFilename)
                self.savePath.setText(savePathStr)
                self.save(recursive=True)
                
    def saveContChecked(self, event):
        if self.running == False:
            if event:
                self.mustSaveFile = True
                filename = str(self.savePath.text())
                path_to_file, name_of_file = os.path.split(filename)
                name_of_file, file_ext = os.path.splitext(name_of_file)
                reFileName = re.search('(?P<mainText>.*)_IT(?P<iterNb>\d+)', name_of_file)
                if reFileName is None:
                    newFilename = '{}_IT{}{}'.format(name_of_file, 0, file_ext)
                    self.savePath.setText(os.path.join(path_to_file, newFilename))
            else:
                self.mustSaveFile = False
                
#            print self.mustSaveFile
                
    
    def _saveFileXY(self, savePathStr, x, y):
        try:
            if self.times:
                pl.savetxt(savePathStr, pl.array([x, y, self.times]).transpose(), fmt="%10.5f", delimiter=",")
            else:
                pl.savetxt(savePathStr, pl.array([x, y]).transpose(), fmt="%10.5f", delimiter=",")
            pl.savetxt(savePathStr, pl.array([x, y]).transpose(), fmt="%10.5f", delimiter=",")
        except IOError:
            self.updateStatusFileField('The file could not be saved. Is the path and name valid?')
            
    def savePathChange(self):
        if self.running == False:
            filename = str(QtGui.QFileDialog.getSaveFileName(self, "Save file", self.file_path, "*.txt", options=QtGui.QFileDialog.DontConfirmOverwrite))
            if self.mustSaveFile:
                path_to_file, name_of_file = os.path.split(filename)
                name_of_file, file_ext = os.path.splitext(name_of_file)
                reFileName = re.search('(?P<mainText>.*)_IT(?P<iterNb>\d+)', name_of_file)
                if reFileName is None:
                    filename = os.path.join(path_to_file, '{}_IT{}{}'.format(name_of_file, 0, file_ext))
            if os.path.splitext(filename)[1] == '':
                filename = filename + '.txt'
            self.savePath.setText(filename)
    
    def updateStatusFileField(self, message):
        self.statusFileLineEdit.setText('#####################')
        self.app.processEvents()
        time.sleep(0.1)
        self.statusFileLineEdit.setText(message)
        
    def updateStatusScanField(self, message):
        self.statusScanLineEdit.setText(message)
        self.app.processEvents()
        
    def closeEvent(self, event):
        self.stop()
        event.accept()
        
        
if __name__ == "__main__":
       
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    myapp = MapWindow(app)
    myapp.show()
    app.exec_()