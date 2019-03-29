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
try:
    from measurements.libs.QPLMapper import ScanGUI as SG
    from PyQt5 import QtCore, QtGui, QtWidgets
except:
    print ("GUI not available!")
#from measurements.libs.mapper_scanners import move_smooth

if sys.version_info.major == 3:
    from importlib import reload
reload (DO)
try:
    reload (SG)
except:
    pass


try: 
    from measurements.libs.QPLMapper.mapper_scanners import move_smooth
except:
    def move_smooth(scanner_axes, targets = []):
        pass

    def move_smooth_simple (scanner_axes, targets = []):
        pass

    print ("Simulation mode. Pay attention that the move_smooth function is not implemented!")



class MultiAxisOptimizer ():

    def __init__ (self, scanner_axes, detector):
        self._scanner_axes = scanner_axes
        if len(detector)>1:
            print "[Optimizer]: Only one detector allowed!"
            detector = detector[0]
        self._detector = detector
        self._nr_axes = len (scanner_axes)

        self._scan_range = []
        self._scan_step = 1

        self._fit_points = 1000

    def _optimize (self, axis_id):
        # code to optimize one axis
        time.sleep(self.delayBetweenRows)
        counts = np.zeros (self._scan_steps)

        for id_x, x in enumerate(self._scan_positions[axis_id,:]):
            
            self._scanner_axes[axis_id].move(x)
            time.sleep(self.delayBetweenPoints)

            counts[id_x] = self._detectors.readout()

            time.sleep(self.max_delay_after_readout)
            self.wait_for_ready(self._detector)
            
        fit_result, fit_plot_x, fit_plot_y = self._fit_gaussian (scan_array=self._scan_positions[axis_id,:], counts=counts)

        return counts, fit_result, fit_plot_x, fit_plot_y
    
    def _fit_gaussian (self, scan_array, counts, do_fit = True, 
                       do_print_fit_report= False):
        p = counts/np.sum(counts)
        x0 = np.sum (p*scan_array)
        v0 = np.sum (p*(scan_array**2)) - x0**2
        s0 = v0**0.5
        ampl0 = 0.5*(counts[0]+counts[-1])
        ampl = max(counts)-ampl0

        fit_params = [ampl0, ampl, x0, s0]

        def _gaussian(x, A0, A, x0, sigma):
            return np.abs(A0) + np.abs(A)*np.exp(-(x-x0)**2 / (2*sigma**2))

        if do_fit:
            x = scan_array
            y = counts
            gmodel = lmfit.Model(_gaussian)
            result = gmodel.fit(y, x=x, A0=ampl0, A=ampl, x0=x0, sigma=s0)
            A = result.params['A'].value
            A0 = result.params['A0'].value
            x0 = result.params['x0'].value
            sigma = result.params['sigma'].value
            fit_params = [A0, A, x0, sigma]
            
            x_fit = np.linspace (x[0], x[-1], self._fit_points)
            y_fit = _gaussian (x=x_fit, A0=A0, A=A, x0=x0, sigma=sigma )

            if do_print_fit_report:
                print(result.fit_report())
        
        return result, x_fit, y_fit
    
    def set_scan_range (self, scan_range=[], scan_steps=1):
        self._scan_range = scan_range
        self._scan_steps = scan_steps
        
    def initialize(self, x0):
        self._x_init = x0
        self._scan_positions  = np.zeros([self._nr_axes, self._scan_steps])
        for i in range(self._nr_axes):
            self._scan_positions [i, :] = np.linspace(x0[i]-0.5*self._scan_range[i], x0[i]+0.5*self._scan_range[i], self._scan_steps)
                                  
    def run_optimizer (self, close_instruments=False, silence_errors=True):
        try:
            print ('Running position optimizer...')
            print ('Current position: ', self._x_init)
            self.init_detectors(self._detector)
            self.init_scanners(self._scanner_axes)

            opt_posit = np.zeros (self._nr_axes)
            sigmas = np.zeros(self._nr_axes)

            if do_plot:
                pl.figure (figsize = (8,5))

            for i in arange(self._nr_axes):
                self._scanner_axes[i].move_smooth(self._x_init[i])

            for i in arange (self._nr_axes):
                counts, fit_result, fit_plot_x, fit_plot_y = self._optimize (axis_id = i, scan_array = self._scan_positions[i, :])
                x_opt = fit_result.params['x0'].value
                self._scanner_axes[i].move_smooth(x_opt)
                s = fit_result.params['sigma'].value
                opt_posit [i] = x_opt
                sigmas [i] = s

                if do_plot:
                    pl.subplot(100+self._nr_axes*10+i)
                    pl.plot (self._scan_positions [i, :], counts, color='RoyalBlue', marker='o')
                    pl.plot (fit_plot_x, fit_plot_y, color='crimson')
                    pl.ylabel ('counts', fontsize=15)

            if do_plot:
                pl.show()

            self.set_scan_range (scan_range = 4*sigmas, scan_steps = self._scan_steps)
            self.initialize (x0 = opt_posit)
            print ('New position: ', self._x_init)

            for i in arange(self._nr_axes):
                self.scanner_axes[i].move_smooth(opt_posit[i])

        except KeyboardInterrupt:
            print('\n####  Program interrupted by user.  ####')
            close_instruments = True
        except:
            close_instruments = True
            if not silence_errors:
                raise
        finally:
            if close_instruments:
                self.close_instruments()

