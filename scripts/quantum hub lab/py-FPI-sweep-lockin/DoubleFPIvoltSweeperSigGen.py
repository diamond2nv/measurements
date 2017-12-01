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
from NIBox import TrigReceiver
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

# VISA_LOCKIN_ADDRESS = r'GPIB0::12::INSTR'
#
# class Trigger(daq.Task):
#     def __init__(self, ctr, freq):
#         daq.Task.__init__(self)
#         self.ctr = str(ctr)
#         self.freq = freq
#
#         self.CreateCOPulseChanFreq("/Weetabix/ctr"+self.ctr, "trigger_"+self.ctr,
#                                    daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low, 0,
#                                    self.freq, 0.5)
#         self.CfgImplicitTiming(daq.DAQmx_Val_ContSamps, 1000)
#
#
#     def get_term(self):
#         n = c_char_p(" ")
#         self.GetCOPulseTerm("/Weetabix/ctr"+self.ctr, n, 20)
#         return n.value
#
#
# class InputCounter(daq.Task):
#     def __init__(self, gate_term, ctr="1"):
#         daq.Task.__init__(self)
#         self.ctr = str(ctr)
#         self.data = pl.zeros((10,),dtype=pl.uint32)
#         self.CreateCICountEdgesChan("Weetabix/ctr"+self.ctr, "ctr"+self.ctr,
#                                     daq.DAQmx_Val_Rising, 0,
#                                     daq.DAQmx_Val_CountUp)
#         self.CfgSampClkTiming(gate_term, 10000, daq.DAQmx_Val_Rising,
#                               daq.DAQmx_Val_ContSamps, 10000)
#         self.SetCICountEdgesTerm("/Weetabix/ctr"+self.ctr, "/Weetabix/PFI1")
#
#
#     def read_counts(self):
#         self.StopTask()
#         self.data = pl.zeros((10000,),dtype=pl.uint32)
#         self.ReadCounterU32(10000, 10., self.data, 10000, None, None)
#         return self.data

class MapWindow(QtGui.QWidget):
    def __init__(self, app):
        super(MapWindow, self).__init__()
        self.app = app

        self.f = 40
        self.no_of_steps = 100

        self.nb_of_scans = 0

        self.v_step = []
        self.buffer = []
        self.data = []

        self.stopScans = True
        self.running = False

        self.mustSaveFile = False

        self.file_path = ""

        self.init_ui()
        self.val_change()
        self.SW_init()

    def init_ui(self):
        # defining widgets and layout
        self.graph1 = pg.PlotWidget()
        self.graph2 = pg.PlotWidget()

        self.steps = QtGui.QSpinBox(self)
        self.steps.setMaximum(99999)
        self.steps.setValue(self.no_of_steps)

        self.freq = QtGui.QDoubleSpinBox(self)
        self.freq.setMaximum(100)
        self.freq.setMinimum(1)
        self.freq.setSingleStep(0.001)
        self.freq.setDecimals(3)
        self.freq.setValue(self.f)

        self.scanNb_field = QtGui.QSpinBox(self)
        self.scanNb_field.setMaximum(99999)
        self.scanNb_field.setMinimum(0)
        self.scanNb_field.setValue(self.nb_of_scans)

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
        plotbox = QtGui.QHBoxLayout()
        plotbox.addWidget(self.graph1)
        plotbox.addWidget(self.graph2)
        vbox.addLayout(plotbox)

        vbox.addWidget(QtGui.QLabel("No. of steps"))
        vbox.addWidget(self.steps)
        vbox.addWidget(QtGui.QLabel("Signal Frequency (Hz)"))
        vbox.addWidget(self.freq)

        scanBox = QtGui.QHBoxLayout()
        scanBox.addWidget(QtGui.QLabel("No. of scans (0 for infinite)"))
        scanBox.addWidget(self.scanNb_field)
        scanBox.addWidget(self.statusScanLineEdit)
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
        self.setWindowTitle("FPI Volt Sweep with Signal Generator")

        # connecting signals and sockets
        self.btn.clicked.connect(self.start)
        self.stp.clicked.connect(self.stop)
        self.sav.clicked.connect(self.save)
        self.savePathBut.clicked.connect(self.savePathChange)
        self.freq.valueChanged.connect(self.val_change)
        self.steps.valueChanged.connect(self.val_change)
        self.scanNb_field.valueChanged.connect(self.val_change)
        self.saveCheckBox.toggled.connect(self.saveContChecked)

        # graph style
        axisFont = QtGui.QFont('Lucida')
        axisFont.setPointSize(15)

        axisPen = pg.mkPen({'color': "#FFF", 'width': 2})
        self.plotPen = pg.mkPen({'width': 4, 'color': 'y'})
        self.scanIndicatorPen = pg.mkPen({'width': 4, 'color': 'y'})

        bottom1 = self.graph1.getPlotItem().getAxis('bottom')
        left1 = self.graph1.getPlotItem().getAxis('left')

        bottom1.setStyle(tickTextOffset=15, tickLength=10)
        left1.setStyle(tickTextOffset=5, tickLength=10)

        bottom1.setPen(axisPen)
        left1.setPen(axisPen)

        bottom1.tickFont = axisFont
        left1.tickFont = axisFont

        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom1.setLabel(text='Voltage', units='V', **labelStyle)
        left1.setLabel(text='Signal (V or counts/s)', **labelStyle)
        bottom1.setHeight(70)
        left1.setWidth(80)

        bottom2 = self.graph2.getPlotItem().getAxis('bottom')
        left2 = self.graph2.getPlotItem().getAxis('left')

        bottom2.setStyle(tickTextOffset=15, tickLength=10)
        left2.setStyle(tickTextOffset=5, tickLength=10)

        bottom2.setPen(axisPen)
        left2.setPen(axisPen)

        bottom2.tickFont = axisFont
        left2.tickFont = axisFont

        labelStyle = {'color': '#FFF', 'font-size': '20pt'}
        bottom2.setLabel(text='Voltage', units='V', **labelStyle)
        left2.setLabel(text='Signal (V or counts/s)', **labelStyle)
        bottom2.setHeight(70)
        left2.setWidth(80)
        YAxis1 = self.graph1.getPlotItem().getViewBox().YAxis
        self.graph1.enableAutoRange(axis=YAxis1)
        XAxis1 = self.graph1.getPlotItem().getViewBox().XAxis
        self.graph1.enableAutoRange(axis=XAxis1)
        YAxis2 = self.graph2.getPlotItem().getViewBox().YAxis
        self.graph2.enableAutoRange(axis=YAxis2)
        XAxis2 = self.graph2.getPlotItem().getViewBox().XAxis
        self.graph2.enableAutoRange(axis=XAxis2)
        self.show()


    def val_change(self):
        self.stop()
        self.f = int(self.freq.value())  # in Hz
        self.no_of_steps = self.steps.value()
        self.nb_of_scans = self.scanNb_field.value()

    def start(self):
        self.times = False
        self.graph1.clear()
        self.plot1 = self.graph1.plot(pen=self.plotPen)
        self.graph2.clear()
        self.plot2 = self.graph2.plot(pen=self.plotPen)
        self.buff1 = []
        self.buff2 = []
        self.running = False
        self.gotdata = False
        self.btn.setEnabled(False)
        self.updateStatusScanField('Please wait...')
        self.app.processEvents()
        self.all_data1 = []
        self.all_data2 = []
        self.data1 = pl.zeros(self.no_of_steps)
        self.data2 = pl.zeros(self.no_of_steps)
        self.stopScans = False
        counts = 0
        self.gotdata = False
        self.synchro = threading.Event()
        self.sync_thread = threading.Thread(target=self.sync_run) 
        self.sync_thread.daemon = True
        self.runThread = threading.Thread(target=self.SW_run)
        self.running = True
        self.sync_thread.start()
        time.sleep(0.5)
        self.runThread.start()
        try:
            while True:
                if self.stopScans == True or (self.nb_of_scans > 0 and counts >= self.nb_of_scans):
        #                print 'stopscans', self.stopScans, '   nb_of_scans', self.nb_of_scans, '   counts', counts
                    self.running = False
                if self.gotdata or self.running == False:  # one last check for data if running = False
                    curPointIndex = len(self.buff1) - 1
    #                   print curPointIndex,'/',len(self.data) - 1
    #                   print self.runThread.isAlive()
                    self.data1[0:curPointIndex+1] = pl.array(self.buff1)
                    self.data2[0:curPointIndex+1] = pl.array(self.buff2)
                    self.buff1 = []
                    self.buff2 = []
                    self.plot1.setData(self.data1)
                    self.plot2.setData(self.data2)

                    self.all_data1.append(self.data1)
                    self.all_data2.append(self.data2)
                    self.gotdata = False
                    if self.mustSaveFile:
                        self.all_data1 = pl.sum(pl.array(self.all_data1),axis=0)
                        self.all_data2 = pl.sum(pl.array(self.all_data2),axis=0)
                        self.save()
                        self.all_data1 = []
                        self.all_data2 = []
                    if self.running == False:
                        break
                    counts += 1
                self.app.processEvents()
                
                
        except:
            self.updateStatusScanField('ERROR: Problem communicating with one or several instruments.')
            raise
        else:
            self.updateStatusScanField('No scan happening.')
        finally:
            self.btn.setEnabled(True)

    def stop(self):
        self.running = False
        self.stopScans = True

    def SW_run(self):
        """Runs in own thread - reads data via Swabian box"""
        self.tag.setTriggerLevel(0, 0.1)
        self.tag.setTriggerLevel(1, 0.1)
        sweep_t = 1./(self.f)
        pixel_t = sweep_t/float(self.no_of_steps)
        times = pl.arange(1, self.no_of_steps)
        self.ctr = Counter(self.tag, [0,1],  int(pixel_t*1e12) , int(self.no_of_steps))
        self.ctr.stop()
        self.ctr.clear()
        self.ctr.start()
        try:

            # go smoothly to start position
            self.updateStatusScanField('Please wait, synchronising...')
            self.tag.sync()
            self.synchro.wait()
            self.updateStatusScanField('Scanning...')
            while self.running:
                self.tag.sync()
                self.synchro.wait()
                data = self.ctr.getData()                
                self.synchro.clear()
                for i in times:
                    self.buff1.append(sum(data[0][int(-i-1):int(-i)]))
                    self.buff2.append(sum(data[1][int(-i-1):int(-i)]))
                self.ctr.clear()
                self.gotdata = True
                while self.gotdata:
                    pass
        finally:
            pass

    def SW_init(self):
        self.listener = TrigReceiver('/Weetabix/port1/line0')
        self.tag = createTimeTagger()
        self.tag.setTriggerLevel(0, 0.1)
        self.tag.setTriggerLevel(1, 0.1)
        self.tag.autoCalibration()
        
    def sync_run(self):
        while True:
            while self.listener.listen() == 0:
                pass
            self.synchro.set()
            while self.listener.listen() == 1:
                pass
            self.synchro.clear()

    def save(self, recursive=False):
        savePathStr = str(self.savePath.text())
#            print savePathStr
        if not os.path.isfile(savePathStr):
            self._saveFileXY(savePathStr, self.all_data1, self.all_data2)
            if recursive:
                self.updateStatusFileField('To avoid erasing an old file, your file has been saved as {}'.format(os.path.basename(savePathStr)))
            else:
                self.updateStatusFileField('Your file has been saved as {}'.format(os.path.basename(savePathStr)))
        else:  # increment name
            path_to_file, name_of_file = os.path.split(savePathStr)
            name_of_file, file_ext = os.path.splitext(name_of_file)
#               print name_of_file
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


    def _saveFileXY(self, savePathStr, y1, y2):
        try:
            if self.times:
                pl.savetxt(savePathStr, pl.array([y1, y2, self.times]).transpose(), fmt="%10.5f", delimiter=",")
            else:
                pl.savetxt(savePathStr, pl.array([y1, y2]).transpose(), fmt="%10.5f", delimiter=",")
            pl.savetxt(savePathStr, pl.array([y1, y2]).transpose(), fmt="%10.5f", delimiter=",")
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
