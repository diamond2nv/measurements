########################################
# Cristian Bonato, 2015
# cbonato80@gmail.com
########################################

from __future__ import unicode_literals
import os, sys, time
from datetime import datetime
from PySide.QtCore import *
from PySide.QtGui import *
import random
from matplotlib.backends import qt4_compat
use_pyside = qt4_compat.QT_API == qt4_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore, uic
else:
    from PyQt4 import QtGui, QtCore, uic

import pylab as plt
import h5py
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm
from analysis.lib.fitting import fit
import measurement.lib.cavity.cavity_scan_v2
import measurement.lib.cavity.panels.scan_gui_panels 
import measurement.lib.cavity.panels.ui_control_panel_2
import measurement.lib.cavity.panels.ui_scan_panel_v9
import measurement.lib.cavity.panels.slow_piezo_scan_panel
import measurement.lib.cavity.panels.ui_XYscan_panel 


from measurement.lib.cavity.cavity_scan_v2 import CavityExpManager, CavityScan
from measurement.lib.cavity.panels.scan_gui_panels import MsgBox, ScanPlotCanvas
from measurement.lib.cavity.panels.ui_control_panel_2 import Ui_Dialog as Ui_Form
from measurement.lib.cavity.panels.ui_scan_panel_v9 import Ui_Form as Ui_Scan
from measurement.lib.cavity.panels.slow_piezo_scan_panel import Ui_Form as Ui_SlowScan
from measurement.lib.cavity.panels.ui_XYscan_panel import Ui_Form as Ui_XYScan

class SlowPiezoScanGUI (QtGui.QMainWindow):
    def __init__(self, exp_mngr):

        QtGui.QWidget.__init__(self)
        self.ui = Ui_SlowScan()
        self.ui.setupUi(self)
        self._exp_mngr = exp_mngr

        #SETTINGS EVENTS
        self.ui.dsb_min_V.setRange(-2, 10)
        self.ui.dsb_min_V.setDecimals(2)
        self.ui.dsb_min_V.setSingleStep(0.1)
        self.ui.dsb_max_V.setRange(-2, 10)
        self.ui.dsb_max_V.setDecimals(2)
        self.ui.dsb_max_V.setSingleStep(0.1)
        self.ui.sb_nr_steps.setRange(1, 999)
        self.ui.sb_wait_time.setRange(1, 999)

        self.ui.sb_nr_steps.valueChanged.connect(self.set_nr_steps)
        self.ui.sb_wait_time.valueChanged.connect(self.set_wait_time)
        self.ui.dsb_min_V.valueChanged.connect(self.set_min_V)
        self.ui.dsb_max_V.valueChanged.connect(self.set_max_V)
        self.ui.button_start.clicked.connect (self.start)
        self.ui.button_save.clicked.connect (self.stop)

        self._curr_task = None
        #TIMER:
        self.refresh_time = 1
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)

    def manage_tasks (self):
        if (self._curr_task == 'scan'):
            self.set_new_voltage()
        else:
            idle = True

    def set_nr_steps (self, value):
        self._nr_steps = value

    def set_min_V (self, value):
        self._min_V = value

    def set_max_V (self, value):
        self._max_V = value

    def set_wait_time (self, value):
        self._wait_time = value

    def start(self):
        self._curr_task = 'scan'
        self.curr_v = self._min_V
        self.v_step = (self._max_V - self._min_V)/float(self._nr_steps)

    def set_new_voltage (self):
        self.ui.label_ctr_V_2.setText ("V = "+str(self.curr_v)+"V")
        self._exp_mngr.set_piezo_voltage (V=self.curr_v)
        self.curr_v = self.curr_v + self.v_step
        qt.msleep (self._wait_time/1000.)
        if (self.curr_v > self._max_V):
            self.curr_v = self._min_V

    def stop (self):
        self._curr_task = None


class ScanGUI(QtGui.QMainWindow):
    def __init__(self, exp_mngr, slowscan_gui):

        QtGui.QWidget.__init__(self)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setWindowTitle("Laser-Piezo Scan Interface")
        self.ui = Ui_Scan()
        self.ui.setupUi(self)
        self._exp_mngr = exp_mngr
        self._slowscan_gui = slowscan_gui
        self._scan_mngr = CavityScan (exp_mngr = exp_mngr)

        self.ui.plot_canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        #SETTINGS EVENTS
        self.ui.sb_avg.setRange(1, 999)
        self.ui.dsb_minV_pzscan.setRange(-2, 10)
        self.ui.dsb_minV_pzscan.setDecimals(2)
        self.ui.dsb_minV_pzscan.setSingleStep(0.1)
        self.ui.dsb_maxV_pzscan.setRange(-2, 10)
        self.ui.dsb_maxV_pzscan.setDecimals(2)
        self.ui.dsb_maxV_pzscan.setSingleStep(0.1)
        self.ui.dsb_minV_finelaser.setRange(-3, 4)
        self.ui.dsb_minV_finelaser.setDecimals(1)
        self.ui.dsb_minV_finelaser.setSingleStep(0.1)
        self.ui.dsb_maxV_finelaser.setRange(-2, 10)
        self.ui.dsb_maxV_finelaser.setDecimals(1)
        self.ui.dsb_maxV_finelaser.setSingleStep(0.1)
        self.ui.sb_nr_steps_pzscan.setRange(1, 9999)
        self.ui.sb_nr_steps_finelaser.setRange(1, 999)
        self.ui.sb_fine_tuning_steps_LRscan.setRange(1,999)
        self.ui.dsb_min_lambda.setRange(636.0, 640.0)
        self.ui.dsb_min_lambda.setDecimals(2)
        self.ui.dsb_min_lambda.setSingleStep(0.01)
        self.ui.dsb_max_lambda.setRange(636.0, 640.0)
        self.ui.dsb_max_lambda.setDecimals(2)
        self.ui.dsb_max_lambda.setSingleStep(0.01)
        self.ui.sb_nr_calib_pts.setRange(1,99)
        self.ui.sb_wait_cycles.setRange(1,999999)
        self.ui.sb_delay_msync.setRange(0, 9999)
        self.ui.sb_mindelay_msync.setRange(0, 9999)
        self.ui.sb_mindelay_msync.setSingleStep(1)
        self.ui.sb_maxdelay_msync.setRange(0, 9999)
        self.ui.sb_maxdelay_msync.setSingleStep(1)
        self.ui.sb_nr_steps_msyncdelay.setRange(1,99)
        self.ui.sb_nr_scans_msync.setRange(1,999)
        self.ui.sb_nr_repetitions.setRange(1,999)
        #CONNECT SIGNALS TO EVENTS
        #general:
        self.ui.cb_autosave.stateChanged.connect (self.autosave)
        self.ui.cb_autostop.stateChanged.connect (self.autostop)
        self.ui.sb_avg.valueChanged.connect(self.set_avg)
        self.ui.button_save.clicked.connect(self.save_single)
        #JPE piezo-Scan:
        self.ui.dsb_minV_pzscan.valueChanged.connect(self.set_minV_pzscan)
        self.ui.dsb_maxV_pzscan.valueChanged.connect(self.set_maxV_pzscan)
        self.ui.sb_nr_steps_pzscan.valueChanged.connect(self.set_nr_steps_pzscan)
        self.ui.sb_wait_cycles.valueChanged.connect(self.set_wait_cycles)
        self.ui.button_start_pzscan.clicked.connect(self.start_pzscan)
        self.ui.button_stop_pzscan.clicked.connect(self.stop_pzscan)
        #FineLaser-Scan:
        self.ui.dsb_minV_finelaser.valueChanged.connect(self.set_minV_finelaser)
        self.ui.dsb_maxV_finelaser.valueChanged.connect(self.set_maxV_finelaser)
        self.ui.sb_nr_steps_finelaser.valueChanged.connect(self.set_nr_steps_finelaser)
        self.ui.button_start_finelaser.clicked.connect(self.start_finelaser)
        self.ui.button_stop_finelaser.clicked.connect(self.stop_finelaser)
        self.ui.button_calibrate_finelaser.clicked.connect(self.calibrate_finelaser)
        #Long-Range Laser-Scan:
        self.ui.dsb_min_lambda.valueChanged.connect(self.set_min_lambda)
        self.ui.dsb_max_lambda.valueChanged.connect(self.set_max_lambda)
        self.ui.button_start_long_scan.clicked.connect(self.start_lr_scan)
        self.ui.button_resume_long_scan.clicked.connect(self.resume_lr_scan)
        self.ui.button_stop_long_scan.clicked.connect(self.stop_lr_scan)
        self.ui.sb_nr_calib_pts.valueChanged.connect(self.set_nr_calib_pts)
        self.ui.sb_fine_tuning_steps_LRscan.valueChanged.connect(self.set_steps_lr_scan)
        #Sweep sync montana delays:
        self.ui.sb_mindelay_msync.valueChanged.connect(self.set_min_msyncdelay)
        self.ui.sb_maxdelay_msync.valueChanged.connect(self.set_max_msyncdelay)
        self.ui.button_start_sweepdelay.clicked.connect(self.start_sweep_msyncdelay)
        self.ui.button_stop_sweepdelay.clicked.connect(self.stop_sweep_msyncdelay)
        self.ui.sb_nr_steps_msyncdelay.valueChanged.connect(self.set_nr_steps_msyncdelay)


        #Other buttons
        self.ui.lineEdit_fileName.textChanged.connect(self.set_file_tag)
        #self.ui.button_timeseries.clicked.connect (self.activate_timeseries)
        self.ui.button_2D_scan.clicked.connect (self.activate_2D_scan)
        #self.ui.button_track.clicked.connect (self.activate_track)
        self.ui.button_slowscan.clicked.connect (self.activate_slowscan)
        self.ui.cb_montana_sync.stateChanged.connect (self.montana_sync)
        self.ui.sb_delay_msync.valueChanged.connect(self.set_delay_msync)
        self.ui.sb_nr_scans_msync.valueChanged.connect(self.set_nr_scans_msync)
        self.ui.sb_nr_repetitions.valueChanged.connect(self.set_nr_repetitions)

        #INITIALIZATIONS:
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

        #TIMER:
        self.refresh_time = 100
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)


    def manage_tasks (self):
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

    def autosave (self, state):
        if state == QtCore.Qt.Checked:
                self._scan_mngr.autosave = True
        else:
            self._scan_mngr.autosave = False

    def autostop (self, state):
        if state == QtCore.Qt.Checked:
            self._scan_mngr.autostop = True
        else:
            self._scan_mngr.autostop = False

    def montana_sync (self, state):
        if state == QtCore.Qt.Checked:
            self._scan_mngr.use_sync = True
        else:
            self._scan_mngr.use_sync = False

    def set_avg (self, value):
        self._scan_mngr.nr_avg_scans = value

    def set_file_tag (self, text):
        self._scan_mngr.file_tag = str(text)

    def initialize_msmt_params(self):
        #TODO: add wavelength to the params!!
        self.msmt_params = {}
        self.msmt_params['nr_scans_per_sync'] = self._scan_mngr.nr_avg_scans
        self.msmt_params['wait_cycles'] = self._scan_mngr.wait_cycles
        return self.msmt_params

    def save_single(self):
        self.save(data_index = '_single')

    def save(self, **kw):
        data_index = kw.pop('data_index', '')
        fName = kw.pop('fname', None)
        if fName == None:
            if (self._scan_mngr.curr_task == 'lr_scan'):
                minL = str(int(10*self._scan_mngr.min_lambda))
                maxL = str(int(10*self._scan_mngr.max_lambda))
                fName =  datetime.now().strftime ('%H%M%S') + '_' + self._scan_mngr.curr_task+'_'+minL+'_'+maxL
            else:
                fName =  datetime.now().strftime ('%H%M%S') + '_' + self._scan_mngr.curr_task
            if self._scan_mngr.file_tag:
                fName = fName + '_' + self._scan_mngr.file_tag
        
        f0 = os.path.join('D:/measuring/data/', time.strftime('%Y%m%d'))
        directory = os.path.join(f0, fName)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        f5 = h5py.File(os.path.join(directory, fName+'.hdf5'))

        if (self._scan_mngr.curr_task+'_processed_data_'+data_index) not in f5.keys():
            scan_grp = f5.create_group(self._scan_mngr.curr_task+'_processed_data_'+data_index)
        else:
            scan_grp = f5[self._scan_mngr.curr_task+'_processed_data_'+data_index]
        scan_grp.create_dataset(self._scan_mngr.saveX_label, data = self._scan_mngr.saveX_values)
        scan_grp.create_dataset(self._scan_mngr.saveY_label, data = self._scan_mngr.saveY_values)

        try:
            if 'raw_data_'+data_index not in f5.keys():
                data_grp = f5.create_group('raw_data_'+data_index)
            else:
                data_grp = f5['raw_data_'+data_index]
            for j in np.arange (self._scan_mngr.nr_avg_scans):
                data_grp.create_dataset('scannr_'+str(j+1), data = self._scan_mngr.data [j,:])
        except:
            print 'Unable to save data'
        
        try:
            if 'TimeStamps'+data_index not in f5.keys():
                time_grp = f5.create_group('TimeStamps'+data_index)
            else:
                time_grp = f5['TimeStamps'+data_index]
            time_grp.create_dataset('timestamps [ms]', data = self._scan_mngr.tstamps_ms)
        except:
            print 'Unable to save timestamps'

        #The below could be in a function save_msmt_params or so
        try:
            for k in self._scan_mngr.scan_params:
                f5.attrs [k] = self._scan_mngr.scan_params[k]
            for l in self.msmt_params: #ideally msmt_params should replace scan_params.
                f5.attrs [l] = self.msmt_params[l]

        except:
            print 'Unable to save scan params'

        f5.close()
        
        fig = plt.figure(figsize = (15,10))
        plt.plot (self._scan_mngr.saveX_values, self._scan_mngr.saveY_values, 'RoyalBlue')
        plt.plot (self._scan_mngr.saveX_values, self._scan_mngr.saveY_values, 'ob')
        plt.xlabel (self._scan_mngr.saveX_label, fontsize = 15)
        plt.ylabel (self._scan_mngr.saveY_label, fontsize = 15)
        plt.savefig (os.path.join(directory, fName+'_avg.png'))
        plt.close(fig)

        if (self._scan_mngr.nr_avg_scans > 1):
            fig = plt.figure(figsize = (15,10))
            colori = cm.gist_earth(np.linspace(0,0.75, self._scan_mngr.nr_avg_scans))
            for j in np.arange(self._scan_mngr.nr_avg_scans):
                plt.plot (self._scan_mngr.saveX_values, self._scan_mngr.data[j,:], color = colori[j])
                plt.plot (self._scan_mngr.saveX_values, self._scan_mngr.data[j,:], 'o', color = colori[j])
            plt.xlabel (self._scan_mngr.saveX_label, fontsize = 15)
            plt.ylabel (self._scan_mngr.saveY_label, fontsize = 15)
            plt.savefig (os.path.join(directory, fName+'.png'))
            plt.close(fig)     

        return fName

    def save_2D_scan(self):

        fName = time.strftime ('%H%M%S') + '_2Dscan'
        if self._scan_mngr.file_tag:
            fName = fName + '_' + self._scan_mngr.file_tag
        f0 = os.path.join('D:/measuring/data/', time.strftime('%Y%m%d'))
        directory = os.path.join(f0, fName)
        if not os.path.exists(directory):
            os.makedirs(directory)

        f5 = h5py.File(os.path.join(directory, fName+'.hdf5'))
        for k in np.arange (self.idx_2D_scan):
            scan_grp = f5.create_group(str(k))
            scan_grp.create_dataset('frq', data = self.dict_2D_scan ['frq_'+str(k)])
            scan_grp.create_dataset('sgnl', data = self.dict_2D_scan ['sgnl_'+str(k)])
            scan_grp.attrs['pzV'] = self.dict_2D_scan ['pzv_'+str(k)]
        f5.close()

    def set_minV_pzscan (self, value):
        self._scan_mngr.minV_pzscan = value

    def set_maxV_pzscan (self, value):
        self._scan_mngr.maxV_pzscan = value

    def set_nr_steps_pzscan (self, value):
        self._scan_mngr.nr_steps_pzscan = value

    def start_pzscan(self):
        if (self._running_task==None):
            self._running_task = 'pzscan'

    def stop_pzscan(self):
        if (self._running_task=='pzscan'):
            self._running_task = None
            self._2D_scan_is_active = False

    def set_minV_finelaser (self, value):
        self._scan_mngr.minV_finelaser = value

    def set_maxV_finelaser (self, value):
        self._scan_mngr.maxV_finelaser = value

    def set_nr_steps_finelaser (self, value):
        self._scan_mngr.nr_steps_finelaser = value

    def set_wait_cycles (self, value):
        self._scan_mngr.wait_cycles = value        

    def start_finelaser(self):
        if (self._running_task==None):
            self._running_task = 'fine_laser_scan'

    def stop_finelaser(self):
        if (self._running_task == 'fine_laser_scan'):
            self._running_task = None
            self._exp_mngr.set_piezo_voltage (V = self._exp_mngr._fine_piezos)

    def calibrate_finelaser(self):
        print 'CALIBRATE fine scan'

    def set_min_lambda (self, value):
        self._scan_mngr.min_lambda = value

    def set_max_lambda (self, value):
        self._scan_mngr.max_lambda = value

    def set_nr_calib_pts (self, value):
        self._scan_mngr.nr_calib_pts = value

    def set_steps_lr_scan (self, value):
        self._scan_mngr.nr_steps_lr_scan = value

    def set_min_msyncdelay(self,value):
        self._scan_mngr.min_msyncdelay = value

    def set_max_msyncdelay(self, value):
        self._scan_mngr.max_msyncdelay = value

    def set_nr_steps_msyncdelay(self,value):
        self._scan_mngr.nr_steps_msyncdelay = value

    def start_sweep_msyncdelay(self):
        if (self._running_task==None):
            self._running_task = 'sweep_msyncdelay'

    def stop_sweep_msyncdelay(self):
        if (self._running_task=='sweep_msyncdelay'):
            self._running_task = None

    def set_nr_scans_msync (self, value):
        self._scan_mngr.nr_avg_scans = value

    def set_delay_msync (self, value):
        self._scan_mngr.sync_delay_ms = value

    def set_nr_repetitions (self,value):
        self._scan_mngr.nr_repetitions = value

    def start_lr_scan(self):
        if (self._running_task==None):
            if (self._scan_mngr.min_lambda>self._scan_mngr.max_lambda):
                self.curr_l = self._scan_mngr.min_lambda
                self._scan_direction = -1
            else:
                self.curr_l = self._scan_mngr.min_lambda
                self._scan_direction = +1

            print 'Scan direction: ', self._scan_direction
            print self.curr_l
            self.lr_scan_frq_list = []
            self.lr_scan_sgnl_list = []
            self._running_task = 'lr_laser_scan'

    def resume_lr_scan(self):
        if (self._running_task==None):
            self._running_task = 'lr_laser_scan'

    def stop_lr_scan(self):
        if (self._running_task == 'lr_laser_scan'):
            self._running_task = None
            self._2D_scan_is_active = False
            print 'Stopping!'

    def activate_slowscan(self):
        self._slowscan_gui.show()

    def activate_2D_scan (self):
        if (self._running_task==None):
            self.curr_pz_volt = self._scan_mngr.minV_pzscan
            self._exp_mngr.set_piezo_voltage (self.curr_pz_volt) 
            self.pzV_step = (self._scan_mngr.maxV_pzscan-self._scan_mngr.minV_pzscan)/float(self._scan_mngr.nr_steps_pzscan)
            self.dict_2D_scan = {}
            self.dict_pzvolt = {}
            self._2D_scan_is_active = True
            if (self._scan_mngr.min_lambda>self._scan_mngr.max_lambda):
                self.curr_l = self._scan_mngr.min_lambda
                self._scan_direction = -1
            else:
                self.curr_l = self._scan_mngr.min_lambda
                self._scan_direction = +1            
            self.lr_scan_frq_list = np.array([])
            self.lr_scan_sgnl_list = np.array([])
            self._running_task = 'lr_laser_scan'
            self.idx_2D_scan = 0

    def run_update_2D_scan (self):

        #store current laserscan in dictionary
        self.dict_2D_scan ['pzv_'+str(self.idx_2D_scan)] = self.curr_pz_volt
        self.dict_2D_scan ['frq_'+str(self.idx_2D_scan)] = np.asarray(self._scan_mngr.saveX_values).flatten()
        self.dict_2D_scan ['sgnl_'+str(self.idx_2D_scan)] = np.asarray(self._scan_mngr.saveY_values).flatten()

        #update paramter values
        self.idx_2D_scan = self.idx_2D_scan + 1
        self.curr_pz_volt = self.curr_pz_volt + self.pzV_step

        if (self.curr_pz_volt<self._scan_mngr.maxV_pzscan):
            self._exp_mngr.set_piezo_voltage (self.curr_pz_volt)
            print 'New pzV = ', self.curr_pz_volt
            self.curr_l = self._scan_mngr.min_lambda
            self.lr_scan_frq_list = np.array([])
            self.lr_scan_sgnl_list = np.array([])
            self._running_task = 'lr_laser_scan'
        else:
            self.curr_pz_volt = self.curr_pz_volt - self.pzV_step
            self.save_2D_scan()
            self._running_task = None
            self._2D_scan_is_active = False

    def run_new_pzscan(self, **kw):
        enable_autosave = kw.pop('enable_autosave',True)
        self.reinitialize()
        self.ui.label_status_display.setText("<font style='color: red;'>SCANNING PIEZOs</font>")
        self._scan_mngr.set_scan_params (v_min=self._scan_mngr.minV_pzscan, v_max=self._scan_mngr.maxV_pzscan, nr_points=self._scan_mngr.nr_steps_pzscan)
        self._scan_mngr.initialize_piezos(wait_time=1)

        #self._scan_mngr.sync_delays_ms = np.ones(self._scan_mngr.nr_avg_scans)*sync_delay_ms

        self._scan_mngr.piezo_scan ()
        self.ui.label_status_display.setText("<font style='color: red;'>idle</font>")
        if self._scan_mngr.success:
            self.ui.plot_canvas.update_plot (x = self._scan_mngr.v_vals, y=self._scan_mngr.data[0], x_axis = 'piezo voltage [V]', 
                        y_axis = 'photodiode signal (a.u.)', color = 'RoyalBlue')
            self._scan_mngr.saveX_values = self._scan_mngr.v_vals
            self._scan_mngr.saveY_values = self._scan_mngr.PD_signal
            self._scan_mngr.save_tstamps_ms = self._scan_mngr.tstamps_ms                  
            self._scan_mngr.saveX_label = 'piezo_voltage'
            self._scan_mngr.saveY_label = 'PD_signal'
            self._scan_mngr.save_scan_type = 'msync'
            self._scan_mngr.curr_task = 'piezo_scan'
        else:        
            msg_text = 'Cannot Sync to Montana signal!'
            ex = MsgBox(msg_text = msg_text)
            ex.show()
            self._scan_mngr.curr_task = None
      
        if self._scan_mngr.autosave and enable_autosave:
            self.save()
        if self._scan_mngr.autostop:
            self._running_task = None
            self._exp_mngr.set_piezo_voltage (V = self._exp_mngr._fine_piezos)

        return self._scan_mngr.success

    def run_new_fine_laser_scan(self):

        self.reinitialize()
        self.ui.label_status_display.setText("<font style='color: red;'>FINE LASER SCAN</font>")
        self._scan_mngr.set_scan_params (v_min=self._scan_mngr.minV_finelaser, v_max=self._scan_mngr.maxV_finelaser, nr_points=self._scan_mngr.nr_steps_finelaser)
        self._scan_mngr.laser_scan(use_wavemeter = False)
        self.ui.plot_canvas.update_plot (x = self._scan_mngr.v_vals, y=self._scan_mngr.data[0], x_axis = 'laser-tuning voltage [V]', 
                    y_axis = 'photodiode signal (a.u.)', color = 'b')
        self._scan_mngr.saveX_values = self._scan_mngr.v_vals
        self._scan_mngr.saveY_values = self._scan_mngr.PD_signal  
        self._scan_mngr.saveX_label = 'laser_tuning_voltage'
        self._scan_mngr.saveY_label = 'PD_signal'        
        self._scan_mngr.curr_task = 'fine_laser_scan'
        self.ui.label_status_display.setText("<font style='color: red;'>idle</font>")

        if self._scan_mngr.autosave:
            self.save()
        if self._scan_mngr.autostop:
            self._running_task = None

    def run_new_sweep_msyncdelay(self):
        print "starting a new sweep of the montana sync delay"
        self.initialize_msmt_params()
        #calculate nr of sync pulses in which nr_scans = nr_scans, and remainder nr_scans in last sync pulse
        nr_syncs_per_pt,nr_remainder = divmod(self._scan_mngr.nr_repetitions, self._scan_mngr.nr_avg_scans)
        #create the array with the sync_delay values to sweep
        sync_delays = np.linspace(self._scan_mngr.min_msyncdelay,self._scan_mngr.max_msyncdelay,self._scan_mngr.nr_steps_msyncdelay)
        print sync_delays

        self.msmt_params['sync_delays'] = sync_delays
        self.msmt_params['sweep_pts'] = sync_delays
        self.msmt_params['sweep_name'] = 'sync delay (ms)'
        self.msmt_params['sweep_length'] = len(sync_delays)
        self.msmt_params['nr_repetitions'] = self._scan_mngr.nr_repetitions
        if nr_remainder > 0: #then you need one more sync to finish all repetitions
            nr_syncs_per_pt = nr_syncs_per_pt+1
        self.msmt_params['nr_syncs_per_pt'] = nr_syncs_per_pt
        self.msmt_params['nr_remainder'] = nr_remainder

        #create a local variable of nr_avg_scans and sync_delay_ms to remember the setting
        nr_avg_scans = self._scan_mngr.nr_avg_scans
        sync_delay_ms = self._scan_mngr.sync_delay_ms
        print 'syncs per pt',nr_syncs_per_pt
        print 'remaining',nr_remainder
        print 'scans per sync',nr_avg_scans

        fname = None

        for i in np.arange(nr_syncs_per_pt):
            if self._running_task == None:
                print 'measurement stopping'
                break
            if (i == nr_syncs_per_pt-1): #the last one
                if nr_remainder>0:
                    #set the nr_avg_scans to the remainder number of scans
                    self._scan_mngr.nr_avg_scans = nr_remainder
            print "sync nr ",i+1," of ", nr_syncs_per_pt


            for j,sync_delay_j in enumerate(sync_delays):
                self._scan_mngr.sync_delay_ms = sync_delay_j
                print 'sync delay value ', j+1 ,' of ', len(sync_delays), ': ',sync_delay_j
                first_rep = str(int(i*nr_avg_scans+1))
                last_rep = str(int(i*nr_avg_scans+self._scan_mngr.nr_avg_scans))
                data_index_name = 'sweep_pt_'+str(j)+'_reps_'+first_rep+'-'+last_rep
                self.run_new_pzscan(enable_autosave=False)
                fname = self.save(fname=fname, 
                    data_index = data_index_name)
        
        #reset the nr_avg_scans in the scan_manager
        self._scan_mngr.nr_avg_scans = nr_avg_scans
        self._scan_mngr.sync_delay_ms = sync_delay_ms

        #always stop after the mmt
        self._running_task = None


    def fit_calibration(self, V, freq, fixed):
        guess_b = -21.3
        guess_c = -0.13
        guess_d = 0.48
        guess_a = freq[0] +3*guess_b-9*guess_c+27*guess_d

        a = fit.Parameter(guess_a, 'a')
        b = fit.Parameter(guess_b, 'b')
        c = fit.Parameter(guess_c, 'c')
        d = fit.Parameter(guess_d, 'd')

        p0 = [a, b, c, d]
        fitfunc_str = ''

        def fitfunc(x):
            return a()+b()*x+c()*x**2+d()*x**3


        fit_result = fit.fit1d(V,freq, None, p0=p0, fitfunc=fitfunc, fixed=fixed,
                do_print=False, ret=True)
        if (len(fixed)==2):
            a_fit = fit_result['params_dict']['a']
            c_fit = fit_result['params_dict']['c']
            return a_fit, c_fit
        else:
            a_fit = fit_result['params_dict']['a']
            b_fit = fit_result['params_dict']['b']
            c_fit = fit_result['params_dict']['c']
            d_fit = fit_result['params_dict']['d']
            return a_fit, b_fit, c_fit, d_fit

    def run_new_lr_laser_scan (self):

        #first decide how to approach the calibration, 
        #depending on the number of calibration pts.
        #This is the number of points actually measured on the wavemeter
        #(should be minimized to keep the scan fast)

        self.reinitialize()
        nr_calib_pts = self._scan_mngr.nr_calib_pts
        b0 = -21.3
        c0 = -0.13
        d0 = 0.48
        self._exp_mngr.set_laser_wavelength(self.curr_l)
        qt.msleep (0.1)
        if self._2D_scan_is_active:
            self.ui.label_status_display.setText("<font style='color: red;'>LASER SCAN: "+str(self.curr_l)+"nm - pzV = "+str(self.curr_pz_volt)+"</font>")
        else:
            self.ui.label_status_display.setText("<font style='color: red;'>LASER SCAN: "+str(self.curr_l)+"nm</font>")

        #acquire calibration points
        dac_no = self._exp_mngr._adwin.dacs['newfocus_freqmod']
        print "DAC no ", dac_no
        self._exp_mngr._adwin.start_set_dac(dac_no=dac_no, dac_voltage=-3)
        qt.msleep (0.1)
        V_calib = np.linspace (-3, 3, nr_calib_pts)
        f_calib = np.zeros(nr_calib_pts)
        print "----- Frequency calibration routine:"
        for n in np.arange (nr_calib_pts):
            qt.msleep (0.3)
            self._exp_mngr._adwin.start_set_dac(dac_no = dac_no, dac_voltage = V_calib[n])
            print "Point nr. ", n, " ---- voltage: ", V_calib[n]
            qt.msleep (0.5)
            f_calib[n] = self._exp_mngr._wm_adwin.Get_FPar (self._exp_mngr._wm_port)
            qt.msleep (0.2)
            print "        ", n, " ---- frq: ", f_calib[n]

        print 'f_calib:', f_calib
        #finel laser scan
        self._scan_mngr.set_scan_params (v_min=-3, v_max=3, nr_points=self._scan_mngr.nr_steps_lr_scan) #real fine-scan
        self._scan_mngr.laser_scan(use_wavemeter = False)
        V = self._scan_mngr.v_vals
        if (nr_calib_pts==1):
            V_calib = int(V_calib)
            f_calib = int(f_calib)
            b = b0
            c = c0
            d = d0
            a = f_calib + 3*b - 9*c + 27*d
        elif ((nr_calib_pts>1) and (nr_calib_pts<4)):
            a, c = self.fit_calibration(V = V_calib, freq = f_calib, fixed=[1,3])
            b = b0
            d = d0
        else:
            a, b, c, d = self.fit_calibration(V = V_calib, freq = f_calib, fixed=[])
        freq = a + b*V + c*V**2 + d*V**3

        self.lr_scan_frq_list =  np.append(self.lr_scan_frq_list,freq)
        self.lr_scan_sgnl_list  = np.append(self.lr_scan_sgnl_list, self._scan_mngr.PD_signal)

        if self._2D_scan_is_active and (self.idx_2D_scan != 0):
            if self.lr_scan_sgnl.ndim == 1:
                self.lr_scan_sgnl = np.array([self.lr_scan_sgnl])
            self.lr_scan_sgnl_list = np.array([self.lr_scan_sgnl_list])

            print 'appending ',np.shape(self.lr_scan_sgnl),' to ',np.shape(self.lr_scan_sgnl_list)

            self.lr_scan_sgnl = np.append(self.lr_scan_sgnl,self.lr_scan_sgnl_list,axis=0)
            print 'results in: ',np.shape(self.lr_scan_sgnl)
        else:
            self.lr_scan_frq = (np.array(self.lr_scan_frq_list)).flatten()
            self.lr_scan_sgnl = (np.array(self.lr_scan_sgnl_list)).flatten()

        self.ui.plot_canvas.update_multiple_plots (x = self.lr_scan_frq, y=self.lr_scan_sgnl, x_axis = 'laser frequency (GHz)', 
                y_axis = 'photodiode signal (a.u.)', autoscale=False, color = 'none')

        self._scan_mngr.saveX_values = self.lr_scan_frq
        self._scan_mngr.saveY_values = self.lr_scan_sgnl  
        self._scan_mngr.saveX_label = 'frequency_GHz'
        self._scan_mngr.saveY_label = 'PD_signal'
        self._scan_mngr.curr_task = 'lr_scan'
        self.ui.label_status_display.setText("<font style='color: red;'>idle</font>")

        self.curr_l = self.curr_l + self._scan_direction*self.coarse_wavelength_step
        print 'New wavelength: ', self.curr_l
        if (self._scan_direction > 0):
            print 'Scan cond: l>max_l'
            stop_condition = (self.curr_l>=self._scan_mngr.max_lambda)
        else:
            print 'Scan cond: l<min_l'
            stop_condition = (self.curr_l<=self._scan_mngr.max_lambda)

        if stop_condition:
            if self._2D_scan_is_active:
                self._running_task = 'update_2D_scan'
            else:
                self._running_task = None
                if self._scan_mngr.autosave:
                    self.save()
        else:
            self._running_task = 'lr_laser_scan'

    def reinitialize (self):
        self._scan_mngr.data = None
        self._scan_mngr.PD_signal = None
        self._scan_mngr.tstamps_ms = None
        self._scan_mngr.scan_params = None

    def fileQuit(self):
        self.close()

    def fileSave(self):
        self.dc.save()

    def closeEvent(self, ce):
        self.fileQuit()


class XYScanGUI (QtGui.QMainWindow):
    def __init__(self, exp_mngr):

        QtGui.QWidget.__init__(self)
        self.ui = Ui_XYScan()
        self.ui.setupUi(self)
        self._exp_mngr = exp_mngr
        self.ui.dsb_set_x_min.setMinimum(-999.0)
        self.ui.dsb_set_x_max.setMinimum(-999.0)
        self.ui.dsb_set_y_min.setMinimum(-999.0)
        self.ui.dsb_set_y_max.setMinimum(-999.0)
        self.ui.dsb_set_x_min.setMaximum(999.0)
        self.ui.dsb_set_x_max.setMaximum(999.0)
        self.ui.dsb_set_y_min.setMaximum(999.0)
        self.ui.dsb_set_y_max.setMaximum(999.0)

        #SETTINGS EVENTS
        self.ui.dsb_set_nr_steps_x.valueChanged.connect(self.set_nr_steps_x)
        self.ui.dsb_set_nr_steps_y.valueChanged.connect(self.set_nr_steps_y)
        self.ui.dsb_set_x_min.valueChanged.connect(self.set_x_min)
        self.ui.dsb_set_x_max.valueChanged.connect(self.set_x_max)
        self.ui.dsb_set_y_min.valueChanged.connect(self.set_y_min)
        self.ui.dsb_set_y_max.valueChanged.connect(self.set_y_max)
        self.ui.dsb_set_acq_time.valueChanged.connect (self.set_acq_time)
        
        self.ui.pushButton_scan.clicked.connect (self.start_scan)
        self.ui.pushButton_stop.clicked.connect (self.stop_scan)
        self.ui.pushButton_save.clicked.connect (self.save_scan)

        #self.ui.button_save.clicked.connect (self.stop)

        self._curr_task = None
        self._x_min = 0
        self._x_max = 0
        self._y_min = 0
        self._y_max = 0
        self._nr_steps_x = 0
        self._nr_steps_y = 0

        #TIMER:
        self.refresh_time = 50
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.manage_tasks)
        self.timer.start(self.refresh_time)
        self._exp_mngr._ctr.set_is_running (True)


    def save_scan (self):
        fName = time.strftime ('%H%M%S') + '_XYScan'
        f0 = os.path.join('D:/measuring/data/', time.strftime('%Y%m%d'))
        directory = os.path.join(f0, fName)
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            f5 = h5py.File(os.path.join(directory, fName+'.hdf5'))
            scan_grp = f5.create_group('XYScan')
            scan_grp.create_dataset('X', data = self.X)
            scan_grp.create_dataset('Y', data = self.Y)
            scan_grp.create_dataset('cts', data = self._counts)
            f5.close()
        except:
            print("datafile not saved!")

        try:
            fig = plt.figure()
            plt.pcolor (self.X, self.Y, self._counts, cmap = 'gist_earth')
            plt.colorbar()
            plt.xlabel ('x [$\mu$m', fontsize = 15)
            plt.ylabel ('y [$\mu$m', fontsize = 15)
            plt.axis ('equal')
            plt.savefig (os.path.join(directory, fName+'.png'))
            plt.close(fig)
        except:
            print("figure not saved!")

    def manage_tasks (self):
        if (self._curr_task == 'scan'):
            self.acquire_new_point()
        else:
            idle = True

    def set_nr_steps_x (self, value):
        self._nr_steps_x = value

    def set_nr_steps_y (self, value):
        self._nr_steps_y = value

    def set_x_min (self, value):
        self._x_min = value

    def set_x_max (self, value):
        self._x_max = value

    def set_y_min (self, value):
        self._y_min = value

    def set_y_max (self, value):
        self._y_max = value

    def set_acq_time (self, value):
        self._acq_time = value
        self._exp_mngr._ctr.set_integration_time (value)

    def settings_correct (self):
        return (self._x_max>= self._x_min) and (self._y_max>= self._y_min) and (self._nr_steps_x > 0) and (self._nr_steps_y > 0)

    def initialize_arrays(self):
        self._x_points = np.linspace (self._x_min, self._x_max, self._nr_steps_x)
        self._y_points = np.linspace (self._y_min, self._y_max, self._nr_steps_y)
        self.X, self.Y = np.meshgrid (self._x_points, self._y_points)


        print self._x_points, self._y_points
        print "X:"
        print self.X
        print "Y:"
        print self.Y
        self._counts = np.zeros(np.shape (self.X))

    def start_scan (self):

        if (self._exp_mngr.room_T == None and self._exp_mngr.low_T == None):
            msg_text = 'Set temperature before moving PiezoKnobs!'
            ex = MsgBox(msg_text=msg_text)
            ex.show()
        else:            
            if self.settings_correct():
                print 'Settings correct!'
                self.initialize_arrays()
                self._curr_row = 0
                self._curr_col = 0
                self._scan_step = +1
                self._curr_task = 'scan'
            else:
                print 'Check settings!'

    def acquire_new_point (self):
        #print "Curr pos: ", self._curr_row, self._curr_col
        #
        # ---------- TO FIX: -------------
        #imgshow in scan_panel_gui, which plots the 2D plot, has "shifted axes"
        #need to calculate what to feed in, instaed of self._x_points and self._y_points
        x = self.X[self._curr_row, self._curr_col]
        y = self.Y[self._curr_row, self._curr_col]
        print 'Point:', x, y
        self.move_pzk (x=x, y=y)
        cts = self.get_counts ()
        self._counts [self._curr_row, self._curr_col] = cts
        self._curr_col = self._curr_col + self._scan_step
        if (self._curr_col>=self._nr_steps_x):
            self._curr_col = int(self._nr_steps_x-1)
            self._curr_row = int(self._curr_row + 1)
            self._scan_step = self._scan_step*(-1) #start scanning in the oposite direction
            self.ui.xy_plot.update_plot(x = self.X, y = self.Y, cts = self._counts)
        elif (self._curr_col<0):
            self._curr_col = 0
            self._curr_row = int(self._curr_row + 1)
            self._scan_step = self._scan_step*(-1)
            self.ui.xy_plot.update_plot(x = self.X, y = self.Y, cts = self._counts)
        if (self._curr_row >= self._nr_steps_y):
            #self.ui.xy_plot.colorbar()
            self._curr_task = None
            self.save_scan()

    def stop_scan (self):
        self._curr_task = None
        self.save_scan()

    def move_pzk (self, x, y):
        #x, yt are in microns. We need to divide by 1000 because MOC works in mm.
        curr_x, curr_y, curr_z = self._exp_mngr._moc.get_position() #here positions are in mm
        print "JPE MOVING!"
        print "Now we are in ", curr_x, curr_y, curr_z
        print "we will move to ", x/1000., y/1000., curr_z
        s1, s2, s3 = self._exp_mngr._moc.motion_to_spindle_steps (x=x/1000., y=y/1000., z=curr_z, update_tracker=False)
        self._exp_mngr._moc.move_spindle_steps (s1=s1, s2=s2, s3=s3, x=x/1000., y=y/1000., z=curr_z)
        self._exp_mngr._moc_updated = True

    def get_counts (self):
        #if not(self._exp_mngr._ctr.get_is_running()):
        #    self._exp_mngr._ctr.set_is_running()
        #cts = self._exp_mngr._ctr.get_cntr1_countrate()
        #cts = int(random.random()*1000)
        #print 'counts...', cts
        cts = self._exp_mngr._adwin.read_photodiode()
        return cts


class ControlPanelGUI (QtGui.QMainWindow):
    def __init__(self, exp_mngr, parent=None):

        self._moc = exp_mngr._moc
        self._wm = exp_mngr._wm_adwin
        self._laser = exp_mngr._laser
        self._exp_mngr = exp_mngr
        QtGui.QWidget.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setWindowTitle("Laser-Piezo Scan Interface")
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.p1_V = 0
        self.p2_V = 0
        self.p3_V = 0
        self._exp_mngr.update_fine_piezos (0)
        self.piezo_locked = False
        self.pzk_X = self._moc.get_track_curr_x()*1000
        self.pzk_Y = self._moc.get_track_curr_y()*1000
        self.pzk_Z = self._moc.get_track_curr_z()*1000
        self.use_wm = False
        self._exp_mngr.room_T = None
        self._exp_mngr.low_T = None        
        self.ui.label_curr_pos_readout.setText('[ '+str(self.pzk_X)+' ,'+str(self.pzk_Y)+' ,'+str(self.pzk_Z)+'] um')
        self._exp_mngr.update_coarse_piezos (x=self.pzk_X, y=self.pzk_Y, z=self.pzk_Z)
        #Set all parameters and connect all events to actions
        # LASER
        self.ui.dSBox_coarse_lambda.setRange (635.00, 640.00)
        self.ui.dSBox_coarse_lambda.setSingleStep (0.01)
        self.ui.dSBox_coarse_lambda.setValue(637.0)
        self.ui.dSBox_coarse_lambda.valueChanged.connect(self.set_laser_coarse)
        self.ui.dsBox_fine_laser_tuning.setDecimals(1)
        self.ui.dsB_power.setRange (0.0, 15.0)
        self.ui.dsB_power.setSingleStep(0.1)     
        self.ui.dsB_power.setValue(0)   
        self.ui.dsB_power.valueChanged.connect(self.set_laser_power)
        self.ui.dsBox_fine_laser_tuning.setRange (0, 100)
        self.ui.dsBox_fine_laser_tuning.setDecimals(2)
        self.ui.dsBox_fine_laser_tuning.setSingleStep(0.01)
        self.ui.dsBox_fine_laser_tuning.setValue(50)
        self.ui.dsBox_fine_laser_tuning.valueChanged.connect(self.set_fine_laser_tuning)
        self.set_laser_coarse(637.0)
        #self.set_laser_power(0)
        self.set_fine_laser_tuning(50)

        # FINE PIEZOS
        self.ui.doubleSpinBox_p1.setRange (-2, 10)
        self.ui.doubleSpinBox_p1.setDecimals (3)        
        self.ui.doubleSpinBox_p1.setSingleStep (0.001)
        self.ui.doubleSpinBox_p1.setValue(self.p1_V)
        self.ui.doubleSpinBox_p1.valueChanged.connect(self.set_dsb_p1)
        self.ui.horizontalSlider_p1.setRange (0, 10000)
        self.ui.horizontalSlider_p1.setSingleStep (1)        
        self.ui.horizontalSlider_p1.valueChanged.connect(self.set_hsl_p1)
        self.set_dsb_p1 (self.p1_V)
        
        # PiezoKnobs
        self.ui.spinBox_X.setRange (-999, 999)
        self.ui.spinBox_X.setValue(self.pzk_X)
        self.ui.spinBox_X.valueChanged.connect(self.set_pzk_X)
        self.ui.spinBox_Y.setRange (-999, 999)
        self.ui.spinBox_Y.setValue(self.pzk_Y)
        self.ui.spinBox_Y.valueChanged.connect(self.set_pzk_Y)
        self.ui.spinBox_Z.setRange (-999, 999)
        self.ui.spinBox_Z.setValue(self.pzk_Z)
        self.ui.spinBox_Z.valueChanged.connect(self.set_pzk_Z)
        self.ui.pushButton_activate.clicked.connect (self.move_pzk)
        self.ui.pushButton_set_as_origin.clicked.connect (self.pzk_set_as_origin)

        #Temperature
        self.ui.radioButton_roomT.toggled.connect (self.room_T_button)
        self.ui.radioButton_lowT.toggled.connect (self.low_T_button)

        #Wavemeter
        self.ui.checkBox_wavemeter.stateChanged.connect (self.use_wavemeter)
        self._exp_mngr._system_updated = True
        self.refresh_time = 100

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(self.refresh_time)

        a = self._moc.status()
        if (a[:5]=='ERROR'):
            msg_text = 'JPE controller is OFF or in manual mode!'
            ex = MsgBox(msg_text=msg_text)
            ex.show()

    def set_laser_coarse (self, value):
        self._exp_mngr.set_laser_wavelength (value)

    def set_laser_power (self, value):
        self._laser.set_power_level (value)

    def set_fine_laser_tuning (self, value):
        voltage = 3*(value-50)/50.
        ### self._ HERE WE SET THE ADWIN VOLTAGE #####

    def set_dsb_p1 (self, value):
        self.set_fine_piezos (value)
        self.ui.horizontalSlider_p1.setValue (int(10000*(value+2.)/12.))

    def set_fine_piezos (self, value):
        self.p1_V = value
        self._moc.set_fine_piezo_voltages (v1 = self.p1_V, v2 = self.p1_V, v3 = self.p1_V)

    def set_hsl_p1 (self, value):
        value_V = 12*value/10000.-2.
        self.ui.doubleSpinBox_p1.setValue(value_V)
        self.set_fine_piezos (value_V)

    def set_pzk_X (self, value):
        self.pzk_X = value

    def set_pzk_Y (self, value):
        self.pzk_Y = value

    def set_pzk_Z (self, value):
        self.pzk_Z = value

    def move_pzk(self):
        """function to move the piezoknobs.
        """
        a = self._moc.status()
        if (self._exp_mngr.room_T == None and self._exp_mngr.low_T == None):
            msg_text = 'Set temperature before moving PiezoKnobs!'
            ex = MsgBox(msg_text=msg_text)
            ex.show()
        elif (a[:5]=='ERROR'): #SvD: this error handling should perhaps be done in the JPE_CADM instrument itself
            msg_text = 'JPE controller is OFF or in manual mode!'
            ex = MsgBox(msg_text=msg_text)
            ex.show()
        else:
            print 'Current JPE position: ', self._moc.print_current_position(), self._moc.print_tracker_params()
            s1, s2, s3 = self._moc.motion_to_spindle_steps (x=self.pzk_X/1000., y=self.pzk_Y/1000., z=self.pzk_Z/1000., update_tracker=False)

            msg_text = 'Moving the spindles by ['+str(s1)+' , '+str(s2)+' , '+str(s3)+' ] steps. Continue?'
            ex = MsgBox(msg_text=msg_text)
            ex.show()
            print ex.ret
            if (ex.ret==0):
                self._moc.move_spindle_steps (s1=s1, s2=s2, s3=s3, x=self.pzk_X/1000., y=self.pzk_Y/1000., z=self.pzk_Z/1000.)
                self.ui.label_curr_pos_readout.setText('[ '+str(self.pzk_X)+' ,'+str(self.pzk_Y)+' ,'+str(self.pzk_Z)+'] um')
                self._exp_mngr.update_coarse_piezos (x = self.pzk_X, y = self.pzk_Y, z = self.pzk_Z)

    def pzk_set_as_origin(self):
        self._moc.set_as_origin()
        self.ui.label_curr_pos_readout.setText('[ '+str(0)+' ,'+str(0)+' ,'+str(0)+'] um')

    def use_wavemeter (self):
        if self.ui.checkBox_wavemeter.isChecked():
            self.use_wm = True           
        else:
            self.use_wm = False

    def update (self):
        if self.use_wm:
            wm_read = self._wm.Get_FPar (45)
            self.ui.label_wavemeter_readout.setText (str(wm_read)+ ' GHz')
        if self._exp_mngr._laser_updated:
            print 'Laser params changed... updating Control Panel'
            try:
                l = self._exp_mngr.get_laser_wavelength()
                self.ui.dSBox_coarse_lambda.setValue(l)
            except:
                print 'Laser problem: wavelength'
            try:
                p = self._exp_mngr.get_laser_power()
                self.ui.dsB_power.setValue(p)   
            except:
                print 'Laser problem: power'
            self._exp_mngr._laser_updated = False
        if self._exp_mngr._moc_updated:
            curr_x, curr_y, curr_z =self._moc.get_position()
            #self.pzk_X, self.pzk_Y, self.pzk_Z = self._exp_mngr._coarse_piezos
            self.ui.label_curr_pos_readout.setText('[ '+str(int(curr_x*1000))+' ,'+str(int(curr_y*1000))+' ,'+str(int(curr_z*1000))+'] um')
            self._exp_mngr._moc_updated = False


    def room_T_button (self):
        if self.ui.radioButton_roomT.isChecked():
            self._exp_mngr.room_T =  True
            self.ui.radioButton_lowT.setChecked(False)
            self._moc.set_temperature(300)
        else:
            self._exp_mngr.room_T =  False
            self.ui.radioButton_lowT.setChecked(True)
            self._moc.set_temperature(4)

    def low_T_button (self):
        if self.ui.radioButton_lowT.isChecked():
            self._exp_mngr.low_T =  True
            self.ui.radioButton_roomT.setChecked(False)
            self._moc.set_temperature(4)
        else:
            self._exp_mngr.room_T =  True
            self.ui.radioButton_roomT.setChecked(True)
            self._moc.set_temperature(300)

    def fileQuit(self):
        print 'Closing!'
        self.set_dsb_p1 (0)
        #self.set_laser_power(0)
        self.set_fine_laser_tuning(0)
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

adwin = qt.instruments.get_instruments()['adwin']
wm_adwin = qt.instruments.get_instruments()['physical_adwin']
moc = qt.instruments.get_instruments()['master_of_cavity']
newfocus1 = qt.instruments.get_instruments()['newfocus1']
ctr = qt.instruments.get_instruments()['counters']


qApp = QtGui.QApplication(sys.argv)
expMngr = CavityExpManager (adwin=adwin, wm_adwin=wm_adwin, laser=newfocus1, moc=moc, counter = ctr)

xyscan_gui = XYScanGUI (exp_mngr = expMngr)
xyscan_gui.setWindowTitle('XY Scan')
xyscan_gui.show()

slowscan_gui = SlowPiezoScanGUI(exp_mngr = expMngr)
aw_scan = ScanGUI(exp_mngr = expMngr, slowscan_gui = slowscan_gui)
aw_scan.setWindowTitle('Laser & Piezo Scan Interface')
aw_scan.show()

aw_ctrl = ControlPanelGUI(exp_mngr = expMngr)
aw_ctrl.setWindowTitle ('Control Panel')
aw_ctrl.show()
sys.exit(qApp.exec_())

