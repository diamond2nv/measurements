# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 09:23:52 2017

@author: cristian bonato
"""

import pylab as pl
import time, sys
from tools import data_object as DO
import numpy as np
import lmfit
from measurements.libs import ScanGUI as SG
from measurements.libs import mapper 
from PyQt5 import QtCore, QtGui, QtWidgets

from measurements.libs.mapper_scanners import move_smooth

if sys.version_info.major == 3:
    from importlib import reload
reload (DO)
reload (SG)

#def move_smooth(scanner_axes, targets = []):
#    pass

#def move_smooth_simple (scanner_axes, targets = []):
#    pass


class Mapper2D_3axes (mapper.XYMapper):
    def __init__(self, scanner_axes=None, detectors=None):
        
        self.trigger_active = True
        self.feedback_active = True
        self._back_to_zero = False

        mapper.XYMapper.__init__ (self, scanner_axes = scanner_axes, detectors = detectors)
        self._iterative = True

        # create a unique ID for each detector, sets additional parameters 
        det_id_list = []
        det_id_counts = []
        for det in self._detectors:
            if det.string_id in det_id_list:
                pos = det_id_list.index(det.string_id)
                det_id_counts[pos]+=1
                det.string_id = det.string_id+'-'+str(det_id_counts[pos])
            else:
                det_id_list = det_id_list + [det.string_id]
                det_id_counts = det_id_counts + [0]
            det._is_changed = False
            det._scan_params_changed = False
            det.readout_values = None
            det.xValues = None
            det.yValues = None

        # creates a list of Saxis objects for the scanners
        self._scAx = self._scanner_axes
        self._scanner_axes = []
        for axes in self._scAx:
            for i, s_axis in enumerate(axes):
                try:
                    s_axis._ids = axes._ids[i]
                except:
                    s_axis._ids = 'axis_'+str(i)
                self._scanner_axes.append(s_axis)

        # default values for scanner axes
        self._x_scan_id = 0
        self._x_scan_id = 1

    def set_work_folder (self, folder):
        self._work_folder = folder

    def set_back_to_zero(self):
        # to go back to 0 V at the end of a scan
        self._back_to_zero = True

    def set_trigger(self, trigger=True, feedback=True):
        self.trigger_active = trigger
        self.feedback_active = feedback

    def set_range(self, xLims, xStep, yLims=None, yStep=None):

        # sets the scanning range
        self._set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
        
        # creates, for each detectors, variable for X, Y, roeadout
        if self._detectors is None:
            self.counts = None
        else:
            a = pl.zeros([self.xNbOfSteps, self.yNbOfSteps])
            for i in range(self.xNbOfSteps):
                for j in range (self.yNbOfSteps):
                    a[i,j] = None
            for idx, d in enumerate (self._detectors):
                setattr (d, '_scan_params_changed', True)
                setattr (self, 'detector_readout_'+str(idx), a)
                setattr (d, 'readout_values', a)
                setattr (d, 'xValues', self.xPositions)
                setattr (d, 'yValues', self.yPositions)
                try:
                    setattr (d, '_scan_units', self._scan_units)
                except:
                    setattr (d, '_scan_units', 'V')


    def set_scanners (self, scan1_id, scan2_id):
        self._x_scan_id = scan1_id
        self._y_scan_id = scan2_id

    def initialize_scan (self):         
        self.init_detectors(self._detectors)
        self.init_scanners(self._scanner_axes)

        print('Total number of steps: {}\n'.format(self.totalNbOfSteps) +
              'X number of steps:     {}\n'.format(self.xNbOfSteps) +
              'Y number of steps:     {}'.format(self.yNbOfSteps))

        self._start_time = 0
        self._first_point = True
        self._idx = 0
        self._id_x = 0
        self._id_y = 0
        self._firstInRow = True

        move_smooth(self._scanner_axes, targets=[self.xPositions[0], self.yPositions[0]])

        print('\nScanners are at start position. Waiting for acquisition.\n')
        print('step \tx (V)\ty (V)')

    def get_current_point (self):
        return self._curr_x, self._curr_y

    def move_to_next (self, verbose = False):
        y = self.yPositions[self._id_y]
        x = self.xPositions[self._id_x]
        self._curr_x = x
        self._curr_y = y

        self._idx += 1
       
        self._scanner_axes[self._x_scan_id].move(x)
        try:
            self._scanner_axes[self._y_scan_id].move(y)
        except IndexError:
            pass

        # display update
        if verbose:
            print('{}/{} \t{:.1f} \t{:.1f}'.format(self._idx, self.totalNbOfSteps, x, y))


    def acquire_data (self):

        # For first point may wait for a reaction 
        # (when acquisition is launched in WinSpec and the old Acton spectrometers)
        if self._first_point:
            self.wait_first_point(self._detectors)
            start_time = time.time()
            first_point = False
        else:
            if idx % 10 == 0:
                self.print_elapsed_time(start_time=start_time, current_index=idx, total_nb_of_steps=self.totalNbOfSteps)

        # delay between rows
        if self._firstInRow:
            time.sleep(self.delayBetweenRows)
            self._firstInRow = False

        # delay between points
        time.sleep(self.delayBetweenPoints)

        # trigger exposure / detector measurement
        if self._detectors is not None:
            for i, detector in enumerate (self._detectors):
                a = detector.readout()
                getattr (self, 'detector_readout_'+str(i))[self._id_x, self._id_y] = a
                getattr (detector, 'readout_values')[self._id_x, self._id_y] = a
                setattr (detector, '_is_changed', True)

        time.sleep(self.max_delay_after_readout)

        # wait for detector to say it finished
        self.wait_for_ready(self._detectors)

        done = self._prepare_next_point()

        return done

    def _prepare_next_point (self):

        # selects the values of (x,y) for the next scan point
        done = False
        self._id_x +=1

        if (self._id_x >= self.xNbOfSteps):
            self._id_x = 0
            self._id_y +=1

            if (self._id_y >= self.yNbOfSteps):        
                done = True
                self.close_scan()
            else:
                # move back to first point of row smoothly
                if self.yPositions[self._id_y] != self.yPositions[-1]:
                    self._scanner_axes[self._x_scan_id].move_smooth(target=self.xPositions[0])
        return done

    def open_GUI (self):
        '''
        Opens Graphical User Interface to manage scan.
        '''

        qApp=QtWidgets.QApplication.instance() 
        if not qApp: 
            qApp = QtWidgets.QApplication(sys.argv)

        self._guiCtrl = SG.ScanGUI (scanner=self)
        self._guiCtrl.setWindowTitle('QPL-ScanGUI')
        self._guiCtrl.show()
        
        for idx, d in enumerate(self._detectors):
            setattr (self, '_guiDetector_'+str(idx), SG.CanvasGUI(detector=d))
            obj = getattr(self, '_guiDetector_'+str(idx))
            getattr (obj, 'setWindowTitle')('QPL-detector_'+str(idx))
            getattr (obj, 'show')()

        #sys.exit(qApp.exec_())

    def close_scan(self):
        # go smoothly to start position
        if self._back_to_zero:
            print('\nGoing back to 0 V on scanners...')
            move_smooth(self._scanner_axes, targets=[0, 0])

        print('\nSCAN COMPLETED\n' +
              'X from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.xPositions[0], self.xPositions[-1], self.xStep, self.xNbOfSteps) +
              'Y from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.yPositions[0], self.yPositions[-1], self.yStep, self.yNbOfSteps) +
              'Total number of steps: {}'.format(self.totalNbOfSteps))

        self.close_instruments()

