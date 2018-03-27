
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

        self.ui.canvas._colors = self._stream_dict['plot-colors']
        self.ui.canvas._channels = self._stream_dict['plot-channels']
        self.ui.canvas._labels = self._stream_dict['plot-labels']
        self.ui.canvas.upload_stream (self._stream_dict['rep_0'])
        self._max_t = self._stream_dict['rep_0'].get_max_time()
        self._view_range = [0, self._max_t]

        self.add_zoom_rect()

        #SETTINGS EVENTS
        self.ui.sb_rep_nr.setRange(1, 999)
         
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
        self.ui.Hscrollbar.setMinimum(0)
        self.ui.Hscrollbar.setMaximum(0)
        self.ui.Hscrollbar.setPageStep(self._max_t)

        #CONNECT SIGNALS TO EVENTS
        self.ui.sb_rep_nr.valueChanged.connect (self._set_curr_rep)
        # connect checkbox signals for available checkboxes
        for ch in self._available_chs:
            a = getattr (self.ui, 'cb_'+ch, None)
            fn = getattr (self, '_view_'+ch, None)
            if callable (fn):
                a.stateChanged.connect (fn)
        self.ui.botton_zoom_in.clicked.connect (self._zoom_in)
        self.ui.button_full_view.clicked.connect (self._zoom_full)
        self.ui.button_zoom_out.clicked.connect (self._zoom_out)
        self.ui.Hscrollbar.sliderMoved.connect (self._slider_changed)
        #self.ui.button_save.clicked.connect(self._save_view)
        #self.ui.lineEdit_fileName.textChanged.connect(self.set_file_tag)

        #INITIALIZATIONS:
        self.units_list = ['ns','us', 'ms', 's']
        self._total_reps = self._stream_dict['nr_reps']
        self.ui.sb_rep_nr.setValue(1)

        self.ui.canvas.update_figure()

    def resizeEvent( self, event ):
        QtWidgets.QWidget.resizeEvent (self, event )
        w = event.size().width()
        h = event.size().height()
        self.w = w
        self.h = h
        self.ui.canvas.resize_canvas (w=w, h=h*0.8)

    def add_zoom_rect(self):
        # setup transparent rectangle for zoom
        self.rect = Rectangle((0,0), 0, 0, alpha=0.3)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.ui.canvas.axes.add_patch(self.rect)

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

    def _update_figure (self):
        self.ui.canvas.update_figure()
        self._update_view()

    def _update_view(self):
        self.ui.canvas.set_time_range (self._view_range[0],
                                            self._view_range[1])
        self.ui.Hscrollbar.setPageStep(self._view_range[1]-self._view_range[0])
        self.ui.Hscrollbar.setMinimum (self._view_range[1]-self._view_range[0])
        self.ui.Hscrollbar.setMaximum(self._max_t-(self._view_range[1]-self._view_range[0]))

    def _set_curr_rep (self, n):
        if ((n>0) and ( n < self._total_reps+1)):
            self._curr_rep = n-1
            self._max_t = self._stream_dict['rep_'+str(self._curr_rep)].get_max_time()
            self.ui.canvas.upload_stream (self._stream_dict['rep_'+str(self._curr_rep)])    
            self.set_view_range (0, self._max_t)
            self._update_figure()
            self.ui.sb_rep_nr.setValue(n)
        else:
            self._set_curr_rep(self._total_reps)
        
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
                self.add_zoom_rect()

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
        self.set_view_range(self.x0, self.x1)
        self.ui.canvas.set_time_range (self.x0, self.x1)

    def _slider_changed (self, event):
        D = self._view_range[1] - self._view_range[0]
        self.set_view_range (t0=event-D, t1=event)
        self._update_view()

    def set_view_range (self, t0, t1):
        try:
            if (t1>t0):
                if (t0<0):
                    t0 = 0
                if (t1>self._max_t):
                    t1 = self._max_t
                self._view_range = [t0, t1]
        except:
            pass

    def _zoom_full (self):
        self.set_view_range (0, self._max_t)
        self._update_view()

    def _zoom_funct (self, alpha):
        x0 = self._view_range[0]
        x1 = self._view_range[1]
        d0 = 0.5*(x0+x1)-alpha*(x1-x0)
        d1 = 0.5*(x0+x1)+alpha*(x1-x0)
        if (d0<0):
            d0 = 0
        if (d1>self._max_t):
            d1 = self._max_t
        return d0, d1

    def _zoom_out (self):
        d0, d1 = self._zoom_funct (alpha=1.)
        self.set_view_range (d0, d1)
        self._update_view()

    def _zoom_in (self):
        d0, d1 = self._zoom_funct (alpha=0.25)
        self.set_view_range (d0, d1)
        self._update_view()







