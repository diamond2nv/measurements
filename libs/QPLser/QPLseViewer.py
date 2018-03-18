
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs.QPLser import ui_QPLseViewer as uM
from importlib import reload
reload (uM)


class QPLviewGUI(QtWidgets.QMainWindow):
    def __init__(self, stream_dict):

        QtWidgets.QWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setWindowTitle("Laser-Piezo Scan Interface")
        self.ui = uM.Ui_Panel()
        self.ui.setupUi(self)
        self._stream_dict = stream_dict
        self._available_chs = stream_dict['plot-channels']
        #self.ui.plot_canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        #SETTINGS EVENTS
        
        self.ui.sb_rep_nr.setRange(1, 999)
        self.ui.dsb_view_time.setRange (0.001, 99.)
        self.ui.dsb_view_time.setDecimals(3)
        self.ui.comboBox_units.addItem ("ns")
        self.ui.comboBox_units.addItem ("us")
        self.ui.comboBox_units.addItem ("ms")
        self.ui.comboBox_units.addItem ("s")          

        # initialize values
        for ch in self._available_chs:
            # dynamically create _view_DX and _view_AX
            self._make_view_channel (ch = ch)

            # Initialize in "checked" state
            a = getattr (self.ui, 'cb_'+ch, None)
            a.setChecked (True)
        self.ui.canvas.set_view_channels (np.ones(len(self._available_chs)))

        #CONNECT SIGNALS TO EVENTS
        self.ui.sb_rep_nr.valueChanged.connect (self._set_rep_nr)
        self.ui.dsb_view_time.valueChanged.connect (self._set_view_time)
        self.ui.comboBox_units.currentIndexChanged.connect (self._set_time_units)
        # connect checkbox signals for available checkboxes
        for ch in self._available_chs:
            a = getattr (self.ui, 'cb_'+ch, None)
            fn = getattr (self, '_view_'+ch, None)
            if callable (fn):
                a.stateChanged.connect (fn)
        #self.ui.button_save.clicked.connect(self._save_view)
        #self.ui.lineEdit_fileName.textChanged.connect(self.set_file_tag)


        #INITIALIZATIONS:
        self._t = 1
        self._time_units = 1
        self._total_reps = self._stream_dict['nr_reps']
        self._curr_rep = 1

        self.ui.sb_rep_nr.setValue(1)

        self.ui.canvas._colors = self._stream_dict['plot-colors']
        self.ui.canvas._channels = self._stream_dict['plot-channels']
        self.ui.canvas._labels = self._stream_dict['plot-labels']
        self.ui.canvas.upload_stream (stream = self._stream_dict['rep_0'])
        self.ui.canvas.update_figure()

        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()

        
        #TIMER:
        #self.refresh_time = 100
        #self.timer = QtCore.QTimer(self)
        #self.timer.timeout.connect(self.manage_tasks)
        #self.timer.start(self.refresh_time)

    def resizeEvent( self, event ):
        QtWidgets.QWidget.resizeEvent (self, event )
        w = event.size().width()
        h = event.size().height()
        self.w = w
        self.h = h
        self.ui.canvas.resize_canvas (w=w, h=h)

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
            ind = self._available_chs.index(ch)
            if state == QtCore.Qt.Checked:
                self.set_switch_ch_check(index=ind, value=1)
            else:
                self.set_switch_ch_check(index=ind, value=0)
            self.ui.canvas.repaint()

        f.__name__ = funcname
        setattr(self, funcname, f)

    def set_switch_ch_check (self, index, value):
        self.ui.canvas._view_chs[index] = value
        self.ui.canvas.update_figure()
    
    def _set_rep_nr (self, n):
        self._rep_nr = n
        self.ui.canvas.upload_stream (self._stream_dict['rep_'+str(n)])
        self.ui.canvas.update_figure()
        
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

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 40))  
        qp.setBrush(br)   
        qp.drawRect(QtCore.QRect(self.begin, self.end))       

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

