
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs import UiScanGUI as uM
from importlib import reload
reload (uM)


class ScanGUI(QtWidgets.QMainWindow):

    def __init__(self, scanner = None):

        QtWidgets.QWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uM.Ui_Form()
        self.ui.setupUi(self)

        self._scanner = scanner

        #SETTINGS ELEMENTS
        try:
            if scanner._scan_units == 'um':
                self._units = 'um'
            else:
                self._units = 'V'
        except:
            self._units = 'V'

        self.ui.label_min.setText ("min ("+self._units+")")
        self.ui.label_max.setText ("max ("+self._units+")")
        self.ui.label_xcurr.setText ("curr X ("+self._units+")")
        self.ui.label_ycurr.setText ("curr Y ("+self._units+")")
        self.ui.label_zcurr.setText ("curr Z ("+self._units+")")
        #CONNECT SIGNALS TO EVENTS
        self.ui.pushButton_Start.clicked.connect (self._start_scan)
        self.ui.pushButton_Stop.clicked.connect (self._stop_scan)
        self.ui.pushButton_Resume.clicked.connect (self._resume_scan)
        self.ui.pushButton_Save.clicked.connect (self._save_scan)

        self.ui.dsB_min1.valueChanged.connect (self._set_min_1)
        self.ui.dsB_max1.valueChanged.connect (self._set_max_1)
        self.ui.dsB_steps1.valueChanged.connect (self._set_steps_1)
        self.ui.dsB_min2.valueChanged.connect (self._set_min_2)
        self.ui.dsB_max2.valueChanged.connect (self._set_max_2)
        self.ui.dsB_steps2.valueChanged.connect (self._set_steps_2)
        self.ui.dsB_fixed_pos.valueChanged.connect (self._set_fixed_pos)
        self.ui.cb_scan1.currentIndexChanged.connect (self._set_scan_axis_1)
        self.ui.cb_scan2.currentIndexChanged.connect (self._set_scan_axis_2)
        self.ui.cb_fixed.currentIndexChanged.connect (self._set_fixed_axis)

    def _set_scan_axis_1 (self, value):
        self._scan_axis_1 = value

    def _set_scan_axis_2 (self, value):
        self._scan_axis_2 = value

    def _set_fixed_axis (self, value):
        self._fixed_axis = value

    def _start_scan (self):
        print ("Starting scan...")
        
    def _stop_scan (self):
        print ("Stop scan...")

    def _resume_scan (self):
        print ("Resume scan...")

    def _save_scan (self):
        print ("Saving scan...")

    def _set_min_1 (self, value):
        self._min_1 = value

    def _set_max_1 (self, value):
        self._max_1 = value

    def _set_min_2 (self, value):
        self._min_2 = value

    def _set_max_2 (self, value):
        self._max_2 = value

    def _set_steps_1 (self, value):
        self._steps_1 = value

    def _set_steps_2 (self, value):
        self._steps_2 = value

    def _set_fixed_pos (self, value):
        self._fixed_pos = value
        print (self._fixed_pos)

    def resizeEvent (self, event):
        QtWidgets.QWidget.resizeEvent (self, event )
        w = event.size().width()
        h = event.size().height()
        self.w = w
        self.h = h
        print (w, h)
        #self.ui.canvas.resize_canvas (w=w, h=h*0.8)
        #self._zoom_full()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        print ("Close window...")
        ce.accept()



