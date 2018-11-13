
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs import ui_scan_gui_ctrl as uScan
from measurements.libs import ui_scan_gui_canvas as uCanvas

from tools import QPL_viewGUI as qplGUI
from tools import data_object as DO

from importlib import reload
reload (uScan)
reload (uCanvas)
reload (qplGUI)
reload (DO)

class ScanGUI(QtWidgets.QMainWindow):

    def __init__(self, scanner = None):

        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uScan.Ui_MainWindow()
        self.ui.setupUi(self)

        self._scanner = scanner
        self._work_folder = scanner._work_folder
        print ("Work folder: ", self._work_folder)

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

        # add detector string IDs and scanner axes to respective combo boxes
        for det in self._scanner._detectors:
            self.ui.cb_detector.addItem(det.string_id)

        self._nr_scanner_axes = len(self._scanner._scanner_axes)
        print ("Nr scanner axes: ", self._nr_scanner_axes)

        for saxes in self._scanner._scanner_axes:
            s = saxes._ids
            self.ui.cB_scanner1.addItem(s)
            self.ui.cB_scanner2.addItem(s)
            self.ui.cB_scanner3.addItem(s)
        self.ui.cB_scanner3.addItem('None') #disables fixed axis

        self._curr_APD = 0
        self._autosave = True
        self._fixed_axis_enabled = True

        #CONNECT SIGNALS TO EVENTS
        self.ui.pushButton_Start.clicked.connect (self._start_scan)
        self.ui.pushButton_Stop.clicked.connect (self._stop_scan)
        self.ui.pushButton_Resume.clicked.connect (self._resume_scan)
        self.ui.pushButton_Save.clicked.connect (self._save_scan)

        self.ui.dsB_min1.valueChanged.connect (self._set_min_1)
        self.ui.dsB_max1.valueChanged.connect (self._set_max_1)
        self.ui.dsB_stepsize1.valueChanged.connect (self._set_stepsize_1)
        self.ui.dsB_min2.valueChanged.connect (self._set_min_2)
        self.ui.dsB_max2.valueChanged.connect (self._set_max_2)
        self.ui.dsB_stepsize2.valueChanged.connect (self._set_stepsize_2)
        self.ui.dsB_fixed_pos.valueChanged.connect (self._set_fixed_pos)
        self.ui.sB_APD.valueChanged.connect (self._set_APD_time)
        self.ui.cB_scanner1.currentIndexChanged.connect (self._set_scan_axis_1)
        self.ui.cB_scanner2.currentIndexChanged.connect (self._set_scan_axis_2)
        self.ui.cB_scanner3.currentIndexChanged.connect (self._set_fixed_axis)
        self.ui.cb_detector.currentIndexChanged.connect (self._set_view_detector)
        self.ui.checkBox_autosave.stateChanged.connect (self._set_autosave)

        self._set_view_detector(self._curr_APD)
        self.load_settings()

        #TIMER:
        # periodically runs "manage_tasks"
        self._curr_task = None
        self.refresh_time = 0.2
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)

    def manage_tasks (self):

        '''     
        Check what the current task is. If the task is 'scan', moves to the next point
        '''
        if (self._curr_task == 'scan'):
            self._get_next_point()
        else:
            idle = True

    def _set_autosave (self, value):
        if value>0:
            self._autosave = True
        else:
            self._autosave = False

    def _set_view_detector (self, value):
        a = int(self._scanner._detectors[value]._ctr_time_ms)
        self._curr_APD = value
        self.ui.sB_APD.setValue(a)

    def _set_APD_time (self, value):
        self._scanner._detectors[self._curr_APD]._ctr_time_ms = value

    def _set_scan_axis_1 (self, value):
        self._scan_axis_1 = int(value)

    def _set_scan_axis_2 (self, value):
        self._scan_axis_2 = int(value)

    def _set_fixed_axis (self, value):
        self._fixed_axis = int(value)
        if (value >= self._nr_scanner_axes):
            self._fixed_axis_enabled = False
        else:
            self._fixed_axis_enabled = True

    def set_current_point (self, scan1, scan2, fixed):
        values = [0,0,0]
        values[self._scan_axis_1] = scan1
        values[self._scan_axis_2] = scan2
        values[self._fixed_axis] = fixed        
        self.ui.label_view_xCurr.setText (str(int(10*values[0])/10))
        self.ui.label_view_yCurr.setText (str(int(10*values[1])/10))
        self.ui.label_view_zCurr.setText (str(int(10*values[2])/10)) 
        self.ui.label_done.setText(str(self._scanner._idx)+'/'+str(self._scanner.totalNbOfSteps))   

    def _start_scan (self):
        print ("Starting scan...")

        max_min = ((self._max_1>self._min_1) and (self._max_2>self._min_2))
        axes = ((self._scan_axis_1 != self._scan_axis_2) and 
                    (self._scan_axis_1 != self._fixed_axis) and 
                    (self._scan_axis_2 != self._fixed_axis))
        valid = max_min and axes

        if valid:
            self._scanner.set_scanners (scan1_id=self._scan_axis_1, scan2_id=self._scan_axis_2)

            if self._fixed_axis_enabled:
                self._scanner._scanner_axes [self._fixed_axis].move(target = self._fixed_pos)

            Lims = [(self._min_1, self._max_1), (self._min_2, self._max_2)]
            StepSizes = [self._stepsize_1, self._stepsize_2]
            
            self._scanner.set_range (xLims=Lims[0], xStep=StepSizes[0], 
                    yLims=Lims[1], yStep=StepSizes[1])
            self._scanner.initialize_scan()

            self._curr_task = 'scan'
            self.ui.label_status.setText ("Scanning")
        else:
            print ("Scan parameters are set incorrectly!")
            print ("Max > Min: ", max_min) 
            print ("Axes set correctly: ", axes)   

    def _stop_scan (self):
        self._curr_task = None
        self.ui.label_status.setText ("Status: Stopped")
        print ("Stop scan...")

    def _resume_scan (self):
        self._curr_task = 'scan'
        self.ui.label_status.setText ("Status: Scanning")

    def _save_scan (self):
        
        # save hdf5 file with scan parameters and detector maps
        tstamp = time.strftime ('%Y%m%d_%H%M%S')
        subf = os.path.join (self._work_folder, tstamp + '_mapper/')
        if not(os.path.exists(subf)):
            os.mkdir(subf)
        fname = os.path.join (subf, tstamp+'_map_data.hdf5')
        f = h5py.File (fname, 'w')
        obj = DO.DataObjectHDF5 ()
        
        try:
            obj.save_object_all_vars_to_file (obj = self, f = f)
        except:
            print ("Scan parameters not saved.")

        try:
            for idx, s in enumerate(self._scanner._scanner_axes):
                grp = f.create_group('scanner_'+str(idx))
                obj.save_object_all_vars_to_file (obj = s, f = grp)
        except:
            print ("Scanner axes not saved.")

        try:    
            for idx, d in enumerate(self._scanner._detectors):
                grp = f.create_group('detector_'+str(idx))
                obj.save_object_to_file (obj = d, f = grp)
        except:
            print ("Detectors not saved.")

        f.close()


        # save plots of spatial maps
        for idx, d in enumerate(self._scanner._detectors):

            x = d.xValues
            y = d.yValues
            value = d.readout_values

            dy = 10*len(y)/len(x)
            fig = plt.figure(figsize= (10, dy))
            ax = fig.add_subplot(111)
            ax.tick_params(labelsize=18)

            if ((x is not None) and (y is not None)):
                [X, Y] = np.meshgrid (self._recalculate(x),self._recalculate(y))
                ax.pcolor (X, Y, np.transpose(value))
                ax.xaxis.set_ticks (x)
                ax.yaxis.set_ticks (y)
            else:
                ax.pcolor (value)
            fig.savefig (os.path.join (subf, 'map_detector'+str(idx)+'_'+d.string_id+'.png'))
            fig.savefig (os.path.join (subf, 'map_detector'+str(idx)+'_'+d.string_id+'.svg'))
            plt.close(fig)

    def _recalculate (self, values):
        x0 =  values[0]
        x1 = values[-1]
        dx = values[1]-values[0]
        N = len(values)
        return np.linspace (x0-dx/2, x1+dx/2, N+1)

    def _get_next_point (self):
        self._scanner.move_to_next()
        xC, yC = self._scanner.get_current_point ()
        self.set_current_point (scan1 = xC, scan2 = yC, fixed = 0)
        done = self._scanner.acquire_data ()
        if done:
            self._curr_task = None
            self.ui.label_status.setText ("Status: Idle")
            if self._autosave:
                self._save_scan()


    def _set_min_1 (self, value):
        self._min_1 = value

    def _set_max_1 (self, value):
        self._max_1 = value

    def _set_min_2 (self, value):
        self._min_2 = value

    def _set_max_2 (self, value):
        self._max_2 = value

    def _set_stepsize_1 (self, value):
        self._stepsize_1 = value

    def _set_stepsize_2 (self, value):
        self._stepsize_2 = value

    def _set_fixed_pos (self, value):
        self._fixed_pos = value
        print (self._fixed_pos)

    def save_settings (self):
        values = [self._min_1, self._max_1, self._stepsize_1, self._min_2, self._max_2, self._stepsize_2, self._fixed_pos, self._scan_axis_1, self._scan_axis_2, self._fixed_axis]
        subf = os.path.join (self._work_folder, '_settings')
        if not(os.path.exists(subf)):
            os.mkdir(subf)

        np.savetxt (os.path.join (subf, 'set_scan_gui.txt'), values, delimiter = ',')

    def load_settings (self):
        try: 
            fname = os.path.join (os.path.join (self._work_folder, '_settings'), 'set_scan_gui.txt')
            self._min_1, self._max_1, stepsize_1, self._min_2, self._max_2, stepsize_2, self._fixed_pos, scan_axis_1, scan_axis_2, fixed_axis = np.loadtxt(fname, delimiter = ',')
            self._stepsize_1 = stepsize_1
            self._stepsize_2 = stepsize_2
            self._scan_axis_1 = int(scan_axis_1)
            self._scan_axis_2 = int(scan_axis_2)
            self._fixed_axis = int(fixed_axis)

            print ("Settings loaded from file.")
        except:
            self._min_1, self._max_1, self._stepsize_1, self._min_2, self._max_2, self._stepsize2, self._fixed_pos, self._scan_axis_1, self._scan_axis_2, self._fixed_axis = [0,0,0,0,0,0,0,0,1,2]
            print ("Settings to zero.")

        self.ui.dsB_max1.setValue(self._max_1)           
        self.ui.dsB_max2.setValue(self._max_2)           
        self.ui.dsB_min1.setValue(self._min_1)           
        self.ui.dsB_min2.setValue(self._min_2)           
        self.ui.dsB_stepsize1.setValue(self._stepsize_1)           
        self.ui.dsB_stepsize2.setValue(self._stepsize_2)           
        self.ui.dsB_fixed_pos.setValue(self._fixed_pos)
        self.ui.cB_scanner1.setCurrentIndex(self._scan_axis_1)         
        self.ui.cB_scanner2.setCurrentIndex(self._scan_axis_2)         
        self.ui.cB_scanner3.setCurrentIndex(self._fixed_axis)         

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.save_settings()
        ce.accept()


class CanvasGUI(qplGUI.QPLZoomableGUI):

    def __init__(self, detector = None):

        ui = uCanvas.Ui_MainWindow()
        qplGUI.QPLZoomableGUI.__init__(self, ui_panel = ui)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self._detector = detector
        self.ui.label.setText(self._detector.string_id)
        self.ui.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        #SETTINGS ELEMENTS
        try:
            if scanner._scan_units == 'um':
                self._units = 'um'
            else:
                self._units = 'V'
        except:
            self._units = 'V'
            
        self._curr_task = None
        self.ui.pushButton.clicked.connect (self._zoom_out)
        self.ui.canvas.set_format_axes_ticks(1)

        #TIMER:
        self.refresh_time = 0.3
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_new_readout)
        self.timer.start(self.refresh_time)

    def _is_click_near_cursor(self, x = None):
        return False

    def _zoom_out(self):
        xVals = self._detector.xValues
        dx = (xVals[1]-xVals[0])/2
        yVals = self._detector.yValues
        dy = (yVals[1]-yVals[0])/2
        self.ui.canvas.set_range (axis1 = [min(xVals)-dx, max(xVals)+dx], 
                                    axis2 = [min(yVals)-dy, max(yVals)]+dy)

    def check_new_readout (self):
        resize = False
        if (self._detector._scan_params_changed):
            self._xValues = self._detector.xValues
            self._yValues = self._detector.yValues
            self.ui.canvas.reinitialize()
            self._detector._scan_params_changed = False
            resize = True
        if (self._detector._is_changed):
            self.ui.canvas.set_2D_data (x = self._xValues, y = self._yValues,
                                            value = self._detector.readout_values,
                                            scan_units = self._detector._scan_units)
            if resize:
                self._resize_canvas_to_fit_map (w=self.width(), h=self.height())
                resize = False

            self._detector._is_changed = False

    def _resize_canvas_to_fit_map (self, w, h):
        try:
            dX = abs(self._xValues[-1] - self._xValues[-0])
            dY = abs(self._yValues[-1] - self._yValues[-0])
            p = min(w/dX, h/dY)
            w1 = p*dX
            h1 = p*dY
        except:
            w1 = w
            h1 = h
        self.w = w1
        self.h = h1
        self.ui.canvas.resize_canvas (w=w1, h=h1)

    def resizeEvent (self, event):
        QtWidgets.QWidget.resizeEvent (self, event)
        w = event.size().width()
        h = event.size().height()
        self._resize_canvas_to_fit_map (w=w, h=h)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        print ("Close window...")
        ce.accept()
