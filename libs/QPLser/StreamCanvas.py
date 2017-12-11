# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QPLser_view.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
import random

class MplCanvas(Canvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self._w_inches = width
        self._h_inches = height
        self._dpi = dpi

        Canvas.__init__(self, self.fig)
        self.setParent(parent)

        Canvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)

    def update (self):
        pass


class StreamCanvas(MplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        self._stream = None
        self._pdict = None
        self._channels = None
        self._labels = None
        self._colors = None

    def upload_stream (self, stream):
        self._stream = stream
        self._stream.set_plot(channels = self._channels,
                    labels = self._labels, colors = self._colors)
        self._pdict = None

    def set_view_channels(self, channels_idx):
        self._view_chs = channels_idx
        self.draw()

    def set_time_interval (self, t):
        self._t = t

    def _plot_channels (self):

        if (self._pdict == None):
            self._pdict = self._stream.get_plot_dict()
        
        curr_offset = 0
        tick_pos = []
        offset = 2

        for ind, ch in enumerate(self._stream.ch_list):

            if (int(self._view_chs[ind]) == 1):

                t = self._pdict[ch]['time']
                y = self._pdict[ch]['y']
                c = self._pdict[ch]['color']

                if (ch[0] == 'D'):
                    self.axes.plot (t, y+curr_offset*np.ones(len(y)), linewidth = 3, color = c)
                    self.axes.fill_between (t, curr_offset, y+curr_offset*np.ones(len(y)), color = c, alpha=0.2)
                    tick_pos.append (curr_offset)
                    self.axes.plot (t, curr_offset*np.ones(len(y)), '--', linewidth = 2, color = 'gray')
                    self.axes.plot (t, (0.5+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'gray')
                    curr_offset += 0.5*offset
                elif (ch[0] == 'A'):
                    curr_offset += 0.25*offset
                    self.axes.plot (t, 0.75*y+curr_offset*np.ones(len(y)), linewidth = 3, color = c)
                    self.axes.plot (t, curr_offset*np.ones(len(y)), '--', linewidth = 2, color = 'gray')
                    tick_pos.append (curr_offset)
                    self.axes.plot (t, (-0.75+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'r')
                    self.axes.plot (t, (0.75+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'r')

                    curr_offset += 0.5*offset
        
        self.axes.yaxis.set_ticks([0, len(self._stream.labels_list)]) 
        self.axes.yaxis.set(ticks=tick_pos, ticklabels=self._stream.labels_list)

        for label in (self.axes.get_xticklabels() + self.axes.get_yticklabels()):
            #label.set_fontname('Arial')
            label.set_fontsize(10)
        
    def update_figure (self):
        self.axes.cla()
        self._plot_channels()
        self.draw()

    def resize_canvas (self, w, h):
        self._w_inches = w/float(self._dpi)
        self._h_inches = h/float(self._dpi)
        self.fig.set_size_inches (self._w_inches, self._h_inches)
        self.update_figure()


class TestCanvas(MplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()

