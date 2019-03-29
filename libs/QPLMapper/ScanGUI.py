import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs.QPLMapper import ui_scan_gui_ctrl as uScan
from measurements.libs.QPLMapper import ui_optimizer_gui as uOpt
from measurements.libs.QPLMapper import ui_scan_gui_canvas as uCanvas
from tools import QPL_viewGUI as qplGUI
from tools import data_object as DO

from importlib import reload
reload (uScan)
reload (uCanvas)
reload (uOpt)
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
        self.ui.pushButton_optimizer.clicked.connect (self._open_optimizer_gui)

        self.ui.dsB_min1.valueChanged.connect (self._set_min_1)
        self.ui.dsB_max1.valueChanged.connect (self._set_max_1)
        self.ui.dsB_steps1.valueChanged.connect (self._set_steps_1)
        self.ui.dsB_min2.valueChanged.connect (self._set_min_2)
        self.ui.dsB_max2.valueChanged.connect (self._set_max_2)
        self.ui.dsB_steps2.valueChanged.connect (self._set_steps_2)
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

        if hasattr (self, '_opt_gui'):
            self._opt_gui._scan_axis_1 = self._scan_axis_1

    def _set_scan_axis_2 (self, value):
        self._scan_axis_2 = int(value)

        if hasattr (self, '_opt_gui'):
            self._opt_gui._scan_axis_2 = self._scan_axis_2

    def _set_fixed_axis (self, value):
        self._fixed_axis = int(value)
        if (value >= self._nr_scanner_axes):
            self._fixed_axis_enabled = False
        else:
            self._fixed_axis_enabled = True

        if hasattr (self, '_opt_gui'):
            self._opt_gui._fixed_axis = self._fixed_axis


    def set_current_point (self, scan1, scan2, fixed):
        values = [0,0,0]
        values[self._scan_axis_1] = scan1
        values[self._scan_axis_2] = scan2
        values[self._fixed_axis] = fixed        
        self.ui.label_view_xCurr.setText (str(int(10*values[0])/10))
        self.ui.label_view_yCurr.setText (str(int(10*values[1])/10))
        self.ui.label_view_zCurr.setText (str(int(10*values[2])/10)) 
        self.ui.label_done.setText(str(self._scanner._idx)+'/'+str(self._scanner.totalNbOfSteps))   

        if hasattr (self, '_opt_gui'):
            self._opt_gui.curr_position = values

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
            StepSizes = [(self._max_1 - self._min_1)/(self._steps_1-1), (self._max_2 - self._min_2)/(self._steps_2-1)]
            
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
        #tstamp = time.strftime ('%Y%m%d_%H%M%S')
        #subf = os.path.join (self._work_folder, tstamp + '_mapper/')
        #if not(os.path.exists(subf)):
        #    os.mkdir(subf)
        #fname = os.path.join (subf, tstamp+'_map_data.hdf5')
        #f = h5py.File (fname, 'w')
        DOobj = DO.DataObjectHDF5 ()
        f = DOobj.create_file (folder = self._work_folder, name = 'map_data')
        
        try:
            DOobj.save_object_all_vars_to_file (obj = self, f = f)
        except:
            print ("Scan parameters not saved.")

        try:
            for idx, s in enumerate(self._scanner._scanner_axes):
                DOobj.save_object_all_vars_to_file (obj = s, f = f, group_name = 'scanner_'+str(idx))
        except:
            print ("Scanner axes not saved.")

        try:    
            for idx, d in enumerate(self._scanner._detectors):
                DOobj.save_object_to_file (obj = d, f = f, group_name = 'detector_'+str(idx))
        except:
            print ("Detectors not saved.")


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
                ax.pcolor (X, Y, value)
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

    def _set_steps_1 (self, value):
        self._steps_1 = value

    def _set_steps_2 (self, value):
        self._steps_2 = value

    def _set_fixed_pos (self, value):
        self._fixed_pos = value
        print (self._fixed_pos)

    def save_settings (self):
        values = [self._min_1, self._max_1, self._steps_1, self._min_2, self._max_2, self._steps_2, self._fixed_pos, self._scan_axis_1, self._scan_axis_2, self._fixed_axis]
        subf = os.path.join (self._work_folder, '_settings')
        if not(os.path.exists(subf)):
            os.mkdir(subf)

        np.savetxt (os.path.join (subf, 'set_scan_gui.txt'), values, delimiter = ',')

    def load_settings (self):
        try: 
            fname = os.path.join (os.path.join (self._work_folder, '_settings'), 'set_scan_gui.txt')
            self._min_1, self._max_1, steps_1, self._min_2, self._max_2, steps_2, self._fixed_pos, scan_axis_1, scan_axis_2, fixed_axis = np.loadtxt(fname, delimiter = ',')
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
        self.ui.cB_scanner1.setCurrentIndex(self._scan_axis_1)         
        self.ui.cB_scanner2.setCurrentIndex(self._scan_axis_2)         
        self.ui.cB_scanner3.setCurrentIndex(self._fixed_axis)        

    def _open_optimizer_gui (self):
        #qApp=QtWidgets.QApplication.instance() 
        #if not qApp: 
        #    qApp = QtWidgets.QApplication(sys.argv)

        self._opt_gui = OptimizerGUI (scanner=self._scanner)
        self._opt_gui.setWindowTitle('QPL-OptimizerGUI')
        self._opt_gui.show()
        #sys.exit(qApp.exec_())
 

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

class OptimizerGUI(QtWidgets.QMainWindow):

    def __init__(self, scanner = None):

        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uOpt.Ui_MainWindow()
        self.ui.setupUi(self)

        self._scanner = scanner

        # add detector string IDs and scanner axes to respective combo boxes
        for det in self._scanner._detectors:
            self.ui.cB_detector.addItem(det.string_id)

        self._nr_scanner_axes = len(self._scanner._scanner_axes)

        self.ui.cB_X.addItem('None')
        self.ui.cB_Y.addItem('None')
        self.ui.cB_Z.addItem('None')
        for saxes in self._scanner._scanner_axes:
            s = saxes._ids
            self.ui.cB_X.addItem(s)
            self.ui.cB_Y.addItem(s)
            self.ui.cB_Z.addItem(s)

        self.ui.cB_X.currentIndexChanged.connect (self._set_opt_axis_X)
        self.ui.cB_Y.currentIndexChanged.connect (self._set_opt_axis_Y)
        self.ui.cB_Z.currentIndexChanged.connect (self._set_opt_axis_Z)
        self.ui.cB_detector.currentIndexChanged.connect (self._select_detector)

        self.ui.dsB_X0.valueChanged.connect (self._set_X0)
        self.ui.dsB_Xrange.valueChanged.connect (self._set_Xrange)
        self.ui.sB_Xsteps.valueChanged.connect (self._set_Xsteps)
        self.ui.dsB_Y0.valueChanged.connect (self._set_Y0)
        self.ui.dsB_Yrange.valueChanged.connect (self._set_Yrange)
        self.ui.sB_Ysteps.valueChanged.connect (self._set_Ysteps)
        self.ui.dsB_Z0.valueChanged.connect (self._set_Z0)
        self.ui.dsB_Zrange.valueChanged.connect (self._set_Zrange)
        self.ui.sB_Zsteps.valueChanged.connect (self._set_Zsteps)

        self.ui.optimize_button.clicked.connect (self._start_optimization)

        #initialize values
        self.ui.cB_X.setCurrentIndex(0)         
        self.ui.cB_Y.setCurrentIndex(0)         
        self.ui.cB_Z.setCurrentIndex(0)        
        self._opt_axis_X = None
        self._opt_axis_Y = None
        self._opt_axis_Z = None
        self._x0 = [0,0,0]
        self._opt_range = [0,0,0]
        self._opt_steps = [1,1,1]
        self._detector_id = 0

        self.ui.viewX.set_tick_fontsize(10)
        self.ui.viewY.set_tick_fontsize(10)
        self.ui.viewZ.set_tick_fontsize(10)
        self.ui.dsB_X0.setMaximum (99)
        self.ui.dsB_X0.setMinimum (-99)
        self.ui.dsB_Y0.setMaximum (99)
        self.ui.dsB_Y0.setMinimum (-99)
        self.ui.dsB_Z0.setMaximum (99)
        self.ui.dsB_Z0.setMinimum (-99)

    def _select_detector (self, value):
        self._detector_id = value

    def _set_opt_axis_X (self, scanner_id):
        self._opt_axis_X = scanner_id

    def _set_opt_axis_Y (self, scanner_id):
        self._opt_axis_Y = scanner_id

    def _set_opt_axis_Z (self, scanner_id):
        self._opt_axis_Z = scanner_id

    def _set_X0 (self, value):
        self._x0[0] = value

    def _set_Y0 (self, value):
        self._x0[1] = value

    def _set_Z0 (self, value):
        self._x0[2] = value

    def _set_Xrange (self, value):
        self._opt_range[0] = value

    def _set_Yrange (self, value):
        self._opt_range[1] = value

    def _set_Zrange (self, value):
        self._opt_range[2] = value

    def _set_Xsteps (self, value):
        self._opt_steps[0] = value

    def _set_Ysteps (self, value):
        self._opt_steps[1] = value

    def _set_Zsteps (self, value):
        self._opt_steps[2] = value

    def _get_active_axes (self):
        xyz = np.array([self._opt_axis_X, self._opt_axis_Y, self._opt_axis_Z])
        idx = np.where (xyz>0)[0]
        return [x for x in idx]

    def _start_optimization_multiple (self):
        ids = self._get_active_axes()
        #x0_array = np.array(self._x0)[ids]
        #range_array = np.array(self._opt_range)[ids]
        #step_array = np.array (self._opt_steps)[ids]
        #self._scanner.initialize_optimizer (x0 = x0_array, 
        #        opt_range = range_array, opt_steps = step_array, ids = ids)
        #self._scanner.run_optimizer (detector_id = self._detector_id, close_instruments=False, silence_errors=False)
        #print (self._scanner.fit_dict)

        # maybe this is not the best way to deal with it
        # may be more handy that the multi-axis optimizer just deals with one axis
        # and this program deals with the interplay between axes
        # i.e. first set to (X0, Y0, Z0) and then scan each axis on its own, updating the plot

    def _plot_fit (self, axis, fit_dict):
        axis_id = fit_dict['axis_id']
        scan_array = fit_dict['x']
        counts = fit_dict['y']
        fit_x = fit_dict['x_fit']
        fit_y = fit_dict['y_fit']

        plot_ax = [self.ui.viewX, self.ui.viewY, self.ui.viewZ]
        plot_ax[axis].axes.cla()
        plot_ax[axis].axes.plot (scan_array, counts, 'o', color='RoyalBlue')
        plot_ax[axis].axes.plot (fit_x, fit_y, color='crimson', linewidth = 2)
        plot_ax[axis].draw()

    def _set_new_position (self, axis, value):

        if (axis==0):
            self.ui.dsB_X0.setValue (value)
            self._x0[0] = value
        elif (axis==1):
            self.ui.dsB_Y0.setValue (value)
            self._x0[1] = value
        elif (axis==2):
            self.ui.dsB_Z0.setValue (value)
            self._x0[2] = value

    def _set_new_range (self, axis, value):

        if (axis==0):
            self.ui.dsB_Xrange.setValue (value)
            self._opt_range [0] = value
        elif (axis==1):
            self.ui.dsB_Yrange.setValue (value)
            self._opt_range [1] = value
        elif (axis==2):
            self.ui.dsB_Zrange.setValue (value)
            self._opt_range [2] = value

    def _start_optimization (self):
        ids = np.array([self._opt_axis_X, self._opt_axis_Y, self._opt_axis_Z])
        # move to current optimal position

        # REMOVE FOR LOOP - gets everything stuck
        for i, axis in enumerate(ids):
            if (axis != None):
                fit_dict = self._scanner.optimize_single_axis (axis=i, x0=self._x0[i], 
                        range=self._opt_range[i], nr_points=self._opt_steps[i], detector_id = 0)
                self._plot_fit (axis = i, fit_dict = fit_dict)
                x_opt = fit_dict['x_opt']
                print ("Optimal position: axis=",i," -- x_opt=", x_opt)
                sigma = abs(fit_dict ['sigma'])
                self._set_new_position (axis=i, value=x_opt)
                self._set_new_range (axis=i, value = 4*sigma)


