
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import h5py

from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs.QPLser import ui_QPLseViewer as uM
reload (uM)

class QPLviewGUI(QtWidgets.QMainWindow):
    def __init__(self, stream_dict):

        QtWidgets.QWidget.__init__(self)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setWindowTitle("Laser-Piezo Scan Interface")
        self.ui = uM.Ui_Panel()
        self.ui.setupUi(self)
        self._stream_dict = stream_dict

        #self.ui.plot_canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        #SETTINGS EVENTS
        
        self.ui.sb_rep_nr.setRange(1, 999)
        self.ui.dsb_view_time.setRange (0.001, 99.)
        self.ui.dsb_view_time.setDecimals(3)
        self.ui.comboBox_units.addItem ("ns")
        self.ui.comboBox_units.addItem ("us")
        self.ui.comboBox_units.addItem ("ms")
        self.ui.comboBox_units.addItem ("s")

        # dynamically create _view_DX and _view_AX
        for c in ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A0', 'A1']:
            self._make_view_channel (ch = c)

        #CONNECT SIGNALS TO EVENTS
        self.ui.sb_rep_nr.valueChanged.connect (self._set_rep_nr)
        self.ui.dsb_view_time.valueChanged.connect (self._set_view_time)
        self.ui.comboBox_units.currentIndexChanged.connect (self._set_time_units)
        self.ui.cb_D0.stateChanged.connect (self._view_D0)
        self.ui.cb_D1.stateChanged.connect (self._view_D1)
        self.ui.cb_D2.stateChanged.connect (self._view_D2)
        self.ui.cb_D3.stateChanged.connect (self._view_D3)
        self.ui.cb_D4.stateChanged.connect (self._view_D4)
        self.ui.cb_D5.stateChanged.connect (self._view_D5)
        self.ui.cb_D6.stateChanged.connect (self._view_D6)
        self.ui.cb_D7.stateChanged.connect (self._view_D7)
        self.ui.cb_A0.stateChanged.connect (self._view_A0)
        self.ui.cb_A1.stateChanged.connect (self._view_A1)
        #self.ui.button_save.clicked.connect(self._save_view)
        #self.ui.lineEdit_fileName.textChanged.connect(self.set_file_tag)


        #INITIALIZATIONS:
        self._ch_view = []
        self._t = 1
        self._time_units = 1

        '''
        #JPE piezo-scan
        self.ui.dsb_minV_pzscan.setValue(1.00)
        self.set_minV_pzscan(1.00)
        self.ui.dsb_maxV_pzscan.setValue(2.00)
        self.set_maxV_pzscan(2.00)
        self.ui.sb_nr_steps_pzscan.setValue(999)
        self.set_nr_steps_pzscan(999)
        #general
        self._running_task = None
        self._scan_mngr.averaging_samples = 1
        self.ui.sb_avg.setValue(1)
        self._scan_mngr.autosave = False
        self._scan_mngr.autostop = False
        #fine laser scan
        self.ui.dsb_minV_finelaser.setValue(-3)
        self._scan_mngr.minV_finelaser = -3
        self.ui.dsb_maxV_finelaser.setValue(3)
        self._scan_mngr.maxV_finelaser = 3
        self.ui.sb_nr_steps_finelaser.setValue(100)
        self._scan_mngr.nr_steps_finelaser = 100
        self.ui.sb_wait_cycles.setValue(1)
        self.set_wait_cycles(1)
        #long range laser scan
        self.ui.sb_fine_tuning_steps_LRscan.setValue(100)
        self._scan_mngr.nr_steps_lr_scan = 100
        self.ui.dsb_min_lambda.setValue (637.0)
        self.set_min_lambda(637.0)
        self.ui.dsb_max_lambda.setValue (637.1)
        self.set_max_lambda(637.1)
        self.ui.sb_nr_calib_pts.setValue(1)
        self.set_nr_calib_pts(1)
        self.coarse_wavelength_step = 0.1 
        #sweep montana sync delays
        self.ui.sb_mindelay_msync.setValue(0)
        self.set_min_msyncdelay (0)
        self.ui.sb_maxdelay_msync.setValue(1000)
        self.set_max_msyncdelay (1000)
        self.ui.sb_nr_steps_msyncdelay.setValue(11)
        self.set_nr_steps_msyncdelay(11)

        #others
        self._scan_mngr.file_tag = ''
        self._2D_scan_is_active = False
        self._use_sync = False
        self.ui.sb_nr_scans_msync.setValue(1)
        self.set_nr_scans_msync(1)
        self.ui.sb_delay_msync.setValue(0)
        self.set_delay_msync(0)
        self.ui.sb_nr_repetitions.setValue(1)
        self.set_nr_repetitions(1)

        '''

        #TIMER:
        self.refresh_time = 100
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)


    def manage_tasks (self):
        pass
        '''
        if (self._running_task == 'pzscan'):
            self.run_new_pzscan()
        elif (self._running_task == 'lr_laser_scan'):
            self.run_new_lr_laser_scan()
        elif (self._running_task == 'fine_laser_scan'):
            self.run_new_fine_laser_scan()
        elif (self._running_task == 'fine_laser_calib'):
            self.run_new_laser_calibration()
        elif (self._running_task == 'timeseries'):
            self.run_new_timeseries()
        elif (self._running_task == 'update_2D_scan'):
            self.run_update_2D_scan()            
        elif (self._running_task == 'sweep_msyncdelay'):
            self.run_new_sweep_msyncdelay()            
        else:
            idle = True
        '''


    def _make_view_channel (self, ch):
        
        #Dynamically create functions that control "tick-box"
        # with selection of which channels to show

        funcname = '_view_'+ch

        def f(state):
            if state == QtCore.Qt.Checked:
                self._ch_view.append(ch)
                print "Add: ", ch
            else:
                self._ch_view.remove(ch)
                print "Remove: ", ch

        f.__name__ = funcname
        setattr(self, funcname, f)
    
    def _set_rep_nr (self, n):
        self._rep_nr = n
        print "Rep nr: ", self._rep_nr

    def _set_view_time (self, t):
        self._t = t
        self.time_window = self._t*self._time_units

    def _set_time_units (self, index):
        a = self.ui.comboBox_units.itemText (index)
        if (a=='ns'):
            self._time_units = 1
        elif (a=='us'):
            self._time_units = 1e3
        elif (a=='ms'):
            self._time_units = 1e6
        elif (a=='s'):
            self._time_units = 1e9

        self.time_window = self._t*self._time_units


    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()
