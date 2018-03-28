
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
        self.fig.subplots_adjust(left=0.05,right=0.95,
                            bottom=0.1,top=0.98,
                            hspace=0,wspace=0)

        Canvas.__init__(self, self.fig)
        self.setParent(parent)

        Canvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)

    def update (self):
        pass

class StreamCanvas(MplCanvas):

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        self._stream = None
        self._pdict = None
        self._channels = None
        self._labels = None
        self._colors = None
        self.scaling_factor = 1

    def upload_stream (self, stream):
        self._stream = stream
        self._stream.set_plot(channels = self._channels,
                    labels = self._labels, colors = self._colors)
        self._pdict = None

    def set_view_channels(self, channels_idx):
        self._view_chs = channels_idx
        self._nr_chans_in_view = sum(self._view_chs)
        self.axes.figure.canvas.draw()

    def set_time_interval (self, t):
        self._t = t

    def clear (self):
        self.axes.clear()

    def _plot_channels (self):

        self.axes.cla()

        if (self._pdict == None):
            self._pdict = self._stream.get_plot_dict()
        
        curr_offset = 0
        tick_pos = []
        offset = 2

        for ind, ch in enumerate(self._stream.ch_list):

            if (int(self._view_chs[ind]) == 1):

                t = self._pdict[ch]['time']*1000
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
            label.set_fontsize(6)
        
    def update_figure (self):
        self._plot_channels()
        self.axes.figure.canvas.draw()
        self.repaint()

    def resize_canvas (self, w, h):
        self._w_inches = w/float(self._dpi)
        self._h_inches = h/float(self._dpi)
        self.fig.set_size_inches (self._w_inches, self._h_inches)
        self.update_figure()

    def set_time_range(self, t0, t1):
        self.axes.set_xlim ([t0, t1])
        self.axes.figure.canvas.draw()
        self.repaint()

class MultiStreamCanvas (StreamCanvas):

    def __init__(self, *args, **kwargs):
        StreamCanvas.__init__(self, *args, **kwargs)

    def _define_canvas_plots (self):
        self.fig, self.axes = plt.subplots (self._nr_chans_in_view, sharex = True)
        self.fig.subplots_adjust(hspace=0)

    def _plot_channels (self):

        # make each channel on an independent subplot
        # with its own y-axis scal (0 to 1, or -1 to +1)
        # and a grid for easier viewing

        self.fig.clf()

        if (self._pdict == None):
            self._pdict = self._stream.get_plot_dict()
        
        curr_offset = 0
        tick_pos = []
        offset = 2

        for ind, ch in enumerate(self._stream.ch_list):

            if (int(self._view_chs[ind]) == 1):

                t = self._pdict[ch]['time']*1000
                y = self._pdict[ch]['y']
                c = self._pdict[ch]['color']

                if (ch[0] == 'D'):
                    self.axes[ind].plot (t, y, linewidth = 3, color = c)
                    self.axes[ind].fill_between (t, 0, y, color = c, alpha=0.2)
                    self.axes[ind].set_ylim ([-0.1, 1.1])
                elif (ch[0] == 'A'):
                    self.axes[ind].plot (t, y, linewidth = 3, color = c)
                    self.axes[ind].set_ylim ([-1.1, 1.1])
         
        #self.axes.yaxis.set_ticks([0, len(self._stream.labels_list)]) 
        #self.axes.yaxis.set(ticks=tick_pos, ticklabels=self._stream.labels_list)

        for label in (self.axes.get_xticklabels() + self.axes.get_yticklabels()):
            #label.set_fontname('Arial')
            label.set_fontsize(6)
