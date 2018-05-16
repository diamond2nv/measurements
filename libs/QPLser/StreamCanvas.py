
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


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

        self._cursor_x0 = 0
        self._cursor_x1 = 0

    def upload_stream (self, stream):
        self._stream = stream
        self._stream.set_plot(channels = self._channels,
                    labels = self._labels, colors = self._colors)
        self._pdict = None

    def set_view_channels(self, channels_idx):
        self._view_chs = channels_idx
        self._nr_chans_in_view = sum(self._view_chs)
        self.axes.figure.canvas.draw_idle()

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
        self.axes.figure.canvas.draw_idle()
        self.repaint()

    def resize_canvas (self, w, h):
        self._w_inches = w/float(self._dpi)
        self._h_inches = h/float(self._dpi)
        self.fig.set_size_inches (self._w_inches, self._h_inches)
        self.update_figure()

    def set_time_range(self, t0, t1):
        self.axes.set_xlim ([t0, t1])
        self._cursor_x0 = t0
        self._scursor_x1 = t1
        self._draw_cursors()
        self.axes.figure.canvas.draw_idle()
        self.repaint()

    def _draw_cursors (self):
        pass

    def make_phantom_axis(self):
        # phantom axis to draw sliders, zoom rectangle, etc..
        self.phax = self.fig.add_axes([0,0,1.,1.])
        self.phax.xaxis.set_visible(False)
        self.phax.yaxis.set_visible(False)
        self.phax.set_zorder(1000)
        self.phax.patch.set_alpha(0.1)

    def add_zoom_rect(self):
        pass

    def draw_1D_zoom_rect (self, x0, x1):
        pass

    def close_zoom_rect(self):
        pass


class MultiStreamCanvas (StreamCanvas):

    def __init__(self, *args, **kwargs):
        StreamCanvas.__init__(self, *args, **kwargs)
        self._lines0 = []
        self._lines1 = []
        self._cursors_enabled = False

    def reset_cursors(self):
        self._cursor_x0 = self._x_min + 5
        self._cursor_x1 = self._x_max - 5

        self._draw_cursor0()
        self._draw_cursor1()

    def enable_cursors (self, value):
        self._cursors_enabled = value

    def reset_canvas (self):
        self.fig.clf()

        #self.make_phantom_axis()
        
        self.axes = []
        self._nr_chans_in_view = int(sum(self._view_chs))

        for i in range(self._nr_chans_in_view):
            num = self._nr_chans_in_view*100+10+i+1
            self.axes.append(self.fig.add_subplot (num))
        self.fig.subplots_adjust(hspace=0)

    def set_cursor (self, cursor, position):
        position = int(position)
        if (cursor == "c0"):
            self._cursor_x0 = position
            self._draw_cursor0()
        elif (cursor == "c1"):
            self._cursor_x1 = position
            self._draw_cursor1()

    def get_cursors (self):
        return self._cursor_x0, self._cursor_x1

    def _draw_cursor0 (self):

        try:
            while (len(self._lines0)>0):
                self._lines0.pop().remove()
        except:
            pass

        if self._cursors_enabled:
            print ("drawing cursor 0!!")
            if (self._pdict == None):
                self._pdict = self._stream.get_plot_dict()

            i = 0
            for ind, ch in enumerate(self._stream.ch_list):

                if (int(self._view_chs[ind]) == 1):
                    self._lines0.append(self.axes[i].axvline(x=self._cursor_x0, color='yellow', linestyle='--'))
                    i+=1

        self.repaint()

    def _draw_cursor1 (self):

        try:
            while (len(self._lines1)>0):
                self._lines1.pop().remove()
        except:
            pass

        if self._cursors_enabled:
            print ("drawing cursor 0!!")

            if (self._pdict == None):
                self._pdict = self._stream.get_plot_dict()

            i = 0
            for ind, ch in enumerate(self._stream.ch_list):

                if (int(self._view_chs[ind]) == 1):
                    self._lines1.append(self.axes[i].axvline(x=self._cursor_x1, color='yellow', linestyle='--'))
                    i+=1

        self.repaint()

    def set_view_channels(self, channels_idx):
        self._view_chs = channels_idx
        self.reset_canvas ()

    def update_figure (self):
        self.clear()
        self._plot_channels()
        for i in range(self._nr_chans_in_view):
            self.axes[i].figure.canvas.draw_idle()
        self.repaint()

    def clear (self):
        for i in range(self._nr_chans_in_view):
            self.axes[i].cla()

    def set_time_range(self, t0, t1):
        self._x_min = t0
        self._x_max = t1
        for i in range(self._nr_chans_in_view):
            self.axes[i].set_xlim ([t0, t1])
            self.axes[i].figure.canvas.draw_idle()
        #self.phax.set_xlim([t0, t1])
        self.repaint()

    def _plot_channels (self):

        self.clear()

        if (self._pdict == None):
            self._pdict = self._stream.get_plot_dict()
        
        curr_offset = 0
        tick_pos = []
        offset = 2

        try:
            while (len(self._lines0)>0):
                self._lines0.pop().remove()
        except:
            pass

        try:
            while (len(self._lines1)>0):
                self._lines1.pop().remove()
        except:
            pass

        i = 0 #index that runs over the axes that are actually plotted
        for ind, ch in enumerate(self._stream.ch_list):

            if (int(self._view_chs[ind]) == 1):
                t = self._pdict[ch]['time']*1000
                y = self._pdict[ch]['y']
                c = self._pdict[ch]['color']

                self.axes[i].set_facecolor('k')
                if (ch[0] == 'D'):
                    self.axes[i].plot (t, y, linewidth = 2, color = c)
                    self.axes[i].fill_between (t, 0, y, color = c, alpha=0.3)
                    self.axes[i].set_ylim ([-0.1, 1.1])
                    ymin=0
                    ymax=1
                elif (ch[0] == 'A'):
                    self.axes[i].plot (t, y, linewidth = 2, color = c)
                    self.axes[i].set_ylim ([-1.1, 1.1])
                    ymin = -1
                    ymax = 1
                if (ind%2==1):
                    self.axes[i].yaxis.tick_right()
                
                xticks = self.axes[i].get_xticks()
                d = xticks[1]-xticks[0]
                xminor_ticks = np.arange (self._x_min, self._x_max, d/4)
                self.axes[i].set_xticks(xminor_ticks, minor=True)
                yticks = self.axes[i].get_yticks()
                d = yticks[1]-yticks[0]
                yminor_ticks = np.arange (ymin, ymax, d/4)
                self.axes[i].set_yticks(yminor_ticks, minor=True)
                self.axes[i].grid(which='major', color='white', linestyle='--', alpha = 0.3)
                self.axes[i].grid(which='minor', color='lightyellow', linestyle=':', alpha = 0.15)

                if self._cursors_enabled:
                    self._lines0.append(self.axes[i].axvline(x=self._cursor_x0, color='yellow', linestyle='--'))
                    self._lines1.append(self.axes[i].axvline(x=self._cursor_x1, color='yellow', linestyle='--'))

                for label in (self.axes[i].get_xticklabels() + self.axes[i].get_yticklabels()):
                    label.set_fontsize(7)

                i += 1


