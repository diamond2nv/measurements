
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

        # here add detector string IDs to combo box
        for det in self._scanner._detectors:
            self.ui.cb_detector.addItem(det.string_id)
            
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

        self.load_settings()

        self._curr_task = None
        #TIMER:
        self.refresh_time = 0.2
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)

    def manage_tasks (self):
        if (self._curr_task == 'scan'):
            self._get_next_point()
        else:
            idle = True

    def _set_scan_axis_1 (self, value):
        self._scan_axis_1 = int(value)

    def _set_scan_axis_2 (self, value):
        self._scan_axis_2 = int(value)

    def _set_fixed_axis (self, value):
        self._fixed_axis = int(value)

    def set_current_point (self, scan1, scan2, fixed):
        values = [0,0,0]
        values[self._scan_axis_1] = scan1
        values[self._scan_axis_2] = scan2
        values[self._fixed_axis] = fixed        
        self.ui.label_view_xCurr.setText (str(values[0]))
        self.ui.label_view_yCurr.setText (str(values[1]))
        self.ui.label_view_zCurr.setText (str(values[2]))      

    def _start_scan (self):
        print ("Starting scan...")

        max_min = ((self._max_1>self._min_1) and (self._max_2>self._min_2))
        axes = ((self._scan_axis_1 != self._scan_axis_2) and 
                    (self._scan_axis_1 != self._fixed_axis) and 
                    (self._scan_axis_2 != self._fixed_axis))
        valid = max_min and axes

        print ("Scan axes: ", self._scan_axis_1, self._scan_axis_2)
        if valid:
            self._scanner.set_scanners (scan1_id=self._scan_axis_1, scan2_id=self._scan_axis_2)
            Lims = [(self._min_1, self._max_1), (self._min_2, self._max_2)]
            StepSizes = [1+(self._max_1 - self._min_1)/self._steps_1, 1+(self._max_2 - self._min_2)/self._steps_2]
            
            # SERVE METTERE VALORE CORRETTO!!!
            self._scanner.set_range (xLims=Lims[self._scan_axis_1], xStep=StepSizes[self._scan_axis_1], 
                    yLims=Lims[self._scan_axis_2], yStep=StepSizes[self._scan_axis_2])
            self._scanner.initialize_scan()

            self._curr_task = 'scan'
        else:
            print ("Scan parameters are set incorrectly!")
            print ("Max > Min: ", max_min) 
            print ("Axes set correctly: ", axes)   

    def _stop_scan (self):
        self._curr_task = None
        print ("Stop scan...")

    def _resume_scan (self):
        self._curr_task = 'scan'
        print ("Resume scan...")

    def _save_scan (self):
        print ("Saving scan...")

    def _get_next_point (self):
        self._scanner.move_to_next()
        xC, yC = self._scanner.get_current_point ()
        self.set_current_point (scan1 = xC, scan2 = yC, fixed = 0)
        done = self._scanner.acquire_data ()
        if done:
            self._curr_task = None

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

    def save_settings (self):
        values = [self._min_1, self._max_1, self._steps_1, self._min_2, self._max_2, self._steps_2, self._fixed_pos, self._scan_axis_1, self._scan_axis_2, self._fixed_axis]
        np.savetxt ('C:/Users/cristian/Research/QPL-code/measurements/scripts/bay5/_settings/set_scan_gui.txt', values, delimiter = ',')

    def load_settings (self):
        try: 
            self._min_1, self._max_1, steps_1, self._min_2, self._max_2, steps_2, self._fixed_pos, scan_axis_1, scan_axis_2, fixed_axis = np.loadtxt('C:/Users/cristian/Research/QPL-code/measurements/scripts/bay5/_settings/set_scan_gui.txt', delimiter = ',')
            self._steps_1 = int(steps_1)
            self._steps_2 = int(steps_2)
            self._scan_axis_1 = int(scan_axis_1)
            self._scan_axis_2 = int(scan_axis_2)
            self._fixed_axis = int(fixed_axis)

            print ("Settings loaded from file.")
        except:
            self._min_1, self._max_1, self._steps_1, self._min_2, self._max_2, self._steps_2, self._fixed_pos, self._scan_axis_1, self._scan_axis_2, self._fixed_axis = [0,0,0,0,0,0,0,0,1,2]
            print ("Settings to zero.")

        self.ui.dsB_max1.setValue(self._max_1)           
        self.ui.dsB_max2.setValue(self._max_2)           
        self.ui.dsB_min1.setValue(self._min_1)           
        self.ui.dsB_min2.setValue(self._min_2)           
        self.ui.dsB_steps1.setValue(self._steps_1)           
        self.ui.dsB_steps2.setValue(self._steps_2)           
        self.ui.dsB_fixed_pos.setValue(self._fixed_pos)
        self.ui.cb_scan1.setCurrentIndex(self._scan_axis_1)         
        self.ui.cb_scan2.setCurrentIndex(self._scan_axis_2)         
        self.ui.cb_fixed.setCurrentIndex(self._fixed_axis)         

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        print ("Close window...")
        self.save_settings()
        ce.accept()



