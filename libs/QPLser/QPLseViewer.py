
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs.QPLser import ui_QPLseViewer as uM
from importlib import reload
reload (uM)


class QPLviewGUI(QtWidgets.QMainWindow):
    def __init__(self, stream_dict):

        QtWidgets.QWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uM.Ui_Panel()
        self.ui.setupUi(self)
        self._stream_dict = stream_dict
        self._available_chs = self._stream_dict['plot-channels']

        # setup transparent rectangle for zoom
        self.rect = Rectangle((0,0), 0, 0, alpha=0.3)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.ui.canvas.axes.add_patch(self.rect)

        #SETTINGS EVENTS
        self.ui.sb_rep_nr.setRange(1, 999)
        self.ui.dsb_t0.setRange (0.001, 99.)
        self.ui.dsb_t0.setDecimals(3)
        self.ui.dsb_t1.setRange (0.001, 99.)
        self.ui.dsb_t1.setDecimals(3)
        for j in ['ns', 'us', 'ms', 's']:
            self.ui.comboBox_units_t1.addItem (j)
            self.ui.comboBox_units_t0.addItem (j)
         
        # connect to mouse events for zoom
        self.ui.canvas.mpl_connect('button_press_event', self.mouseClick)
        self.ui.canvas.mpl_connect('motion_notify_event', self.mouseMove)
        self.ui.canvas.mpl_connect('button_release_event', self.mouseRelease)
        self.mouse_clicked = False

        # initialize values
        for ch in self._available_chs:
            # dynamically create _view_DX and _view_AX
            self._make_view_channel (ch = ch)

            # Initialize in "checked" state
            a = getattr (self.ui, 'cb_'+ch, None)
            a.setChecked (True)
        self.ui.canvas.set_view_channels (np.ones(len(self._available_chs)))
        self._t0_units = 1
        self._t1_units = 1
        self._t0 = 0
        self._t1 = 0

        #CONNECT SIGNALS TO EVENTS
        self.ui.sb_rep_nr.valueChanged.connect (self._set_curr_rep)
        self.ui.dsb_t0.valueChanged.connect (self._set_t0)
        self.ui.dsb_t1.valueChanged.connect (self._set_t1)
        self.ui.comboBox_units_t0.currentIndexChanged.connect (self._set_units_t0)
        self.ui.comboBox_units_t1.currentIndexChanged.connect (self._set_units_t1)
        # connect checkbox signals for available checkboxes
        for ch in self._available_chs:
            a = getattr (self.ui, 'cb_'+ch, None)
            fn = getattr (self, '_view_'+ch, None)
            if callable (fn):
                a.stateChanged.connect (fn)
        #self.ui.button_save.clicked.connect(self._save_view)
        #self.ui.lineEdit_fileName.textChanged.connect(self.set_file_tag)

        #INITIALIZATIONS:
        self.units_list = ['ns','us', 'ms', 's']
        self._total_reps = self._stream_dict['nr_reps']
        self._set_curr_rep(1)

        self.ui.sb_rep_nr.setValue(1)

        self.ui.canvas._colors = self._stream_dict['plot-colors']
        self.ui.canvas._channels = self._stream_dict['plot-channels']
        self.ui.canvas._labels = self._stream_dict['plot-labels']
        print (self._stream_dict)
        #self.ui.canvas.update_figure()

    def resizeEvent( self, event ):
        QtWidgets.QWidget.resizeEvent (self, event )
        w = event.size().width()
        h = event.size().height()
        self.w = w
        self.h = h
        self.ui.canvas.resize_canvas (w=w, h=h*0.8)

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

    def _find_t_scaling (self):
        dt = self._time_window[1]
        q = 10
        i = 0
        d = dt
        while ((q>0) and (i<3)):
            d = d/1000
            q = int(d)
            i += 1
            #r = dt - q*i*1000
        return (i-1)

    def _update_figure (self):
        i = self._find_t_scaling()
        self.time_unit = self.units_list[i]
        self.scaling_factor = 10**(i*3)
        self.ui.canvas.time_unit = self.time_unit
        self.ui.canvas.scaling_factor = self.scaling_factor
        self.ui.canvas.set_time_range (self._time_window[0], self._time_window[1])
        # updates hscrollbar
    
    def _set_curr_rep (self, n):
        if ((n>0) and ( n < self._total_reps+1)):
            self._curr_rep = n-1
            self._max_t = self._stream_dict['rep_'+str(self._curr_rep)].get_max_time()
            self.ui.canvas.upload_stream (self._stream_dict['rep_'+str(self._curr_rep)])
            self._set_t0 (0)
            self._set_units_t0 ('ns')
            self._set_t1 (self._max_t)
            self._set_units_t1 ('ns')            
            self._update_figure()
            self.ui.sb_rep_nr.setValue(n)
        else:
            self._set_curr_rep(self._total_reps)
        
    def _set_t0 (self, t):
        self._t0 = t
        self._time_window = [self._t0*self._t0_units, self._t1*self._t1_units]

    def _set_units_t0 (self, index):
        i = self.units_list.index(index)
        a = self.ui.comboBox_units_t0.itemText (i)
        exp_list = [1, 1e3, 1e6, 1e9]
        self._t0_units = exp_list[i]
        self._time_window = [self._t0*self._t0_units, self._t1*self._t1_units]

    def _set_t1 (self, t):
        self._t1 = t
        self._time_window = [self._t0*self._t0_units, self._t1*self._t1_units]

    def _set_units_t1 (self, index):
        i = self.units_list.index(index)
        a = self.ui.comboBox_units_t1.itemText (i)
        exp_list = [1, 1e3, 1e6, 1e9]
        self._t1_units = exp_list[i]
        self._time_window = [self._t0*self._t0_units, self._t1*self._t1_units]

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def mouseClick(self, event):
        if (event.xdata != None):
            self.x0 = event.xdata
            if (event.ydata != None):
                self.y0 = event.ydata
                self.mouse_clicked = True

    def mouseMove(self, event):
        if self.mouse_clicked:
            if (event.xdata != None):
                self.x1 = event.xdata
                if (event.ydata != None):
                    self.y1 = event.ydata
            self.rect.set_width(self.x1 - self.x0)
            self.rect.set_height(self.y1 - self.y0)
            self.rect.set_xy((self.x0, self.y0))
            self.ui.canvas.axes.figure.canvas.draw()
            self.ui.canvas.repaint()

    def mouseRelease(self, event):
        if self.mouse_clicked:
            if (event.xdata != None):
                self.x1 = event.xdata
                if (event.ydata != None):
                    self.y1 = event.ydata

        self.mouse_clicked = False
        self.rect.set_width(0)
        self.rect.set_height(0)
        self.ui.canvas.set_time_range (self.x0, self.x1)




