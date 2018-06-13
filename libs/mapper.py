# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 09:23:52 2017

@author: cristian bonato
"""

import pylab as pl
import time
from tools import data_object as DO
import numpy as np
import lmfit
from measurements.libs.mapper_scanners import move_smooth

class XYMapper ():
    def __init__(self, scanner_axes=None, detectors=None):
        self._scanner_axes = scanner_axes
        self._detectors = detectors

        self.delayBetweenPoints = 1
        self.delayBetweenRows = 0.5

        # determine the longest test delay in the detectors
        if self._detectors is not None:
            self.max_delay_state_check = max([detector.delay_state_check for detector in self._detectors])
            self.max_delay_after_readout = max([detector.delay_after_readout for detector in self._detectors])
        else:
            self.max_delay_state_check = 0
            self.max_delay_after_readout = 0

    def set_delays(self, between_points, between_rows):
        self.delayBetweenPoints = between_points
        self.delayBetweenRows = between_rows

    def _set_range(self, xLims, xStep, yLims=None, yStep=None):

        self.xNbOfSteps = int(abs(pl.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
        self.xPositions = pl.linspace(xLims[0], xLims[1], self.xNbOfSteps)
        self.xStep = xStep
        if yLims is not None or yStep is not None:
            self.yNbOfSteps = int(abs(pl.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
            self.yPositions = pl.linspace(yLims[0], yLims[1], self.yNbOfSteps)
            self.yStep = yStep
        else:
            self.yNbOfSteps = 1
            self.yPositions = pl.array([0])
            self.yStep = 0
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps


    def seconds_in_HMS(self, nbOfSeconds):
        hours = pl.floor(nbOfSeconds / 3600)
        minutes = pl.floor(nbOfSeconds % 3600 / 60)
        seconds = nbOfSeconds - minutes*60 - hours*3600
        return hours, minutes, seconds

    def print_elapsed_time(self, start_time, current_index, total_nb_of_steps):
        elapsedTime = float(time.time() - start_time)
        remainingTime = elapsedTime / current_index * (total_nb_of_steps - (current_index-1))
        
        hoursE, minutesE, secondsE = self.seconds_in_HMS(elapsedTime)
        hoursR, minutesR, secondsR = self.seconds_in_HMS(remainingTime)

        print('Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR))

    def init_detectors(self, detectors):
        if detectors is not None:
            for detector in detectors:
                detector.initialize()

    def init_scanners(self, scanner_axes):
        if scanner_axes is not None:
            for scanner_axis in scanner_axes:
                scanner_axis.initialize()

    def close_instruments(self):
        for scanner in self._scanner_axes:
            scanner.close()
        if self._detectors is not None:
            for detector in self._detectors:
                detector.close()

    def wait_first_point(self, detectors):
        if detectors is not None:
            while not all([detector.first_point() for detector in detectors]):
                time.sleep(self.max_delay_state_check)

    def wait_for_ready(self, detectors):
        if detectors is not None:
            while not all([detector.is_ready() for detector in detectors]):
                time.sleep(self.max_delay_state_check)

class XYScan (XYMapper):
    def __init__(self, scanner_axes=None, detectors=None):
        
        self.trigger_active = True
        self.feedback_active = True
        self._back_to_zero = False

        XYMapper.__init__ (self, scanner_axes = scanner_axes, detectors = detectors)

    def set_back_to_zero(self):
        # to go back to 0 V at the end of a scan
        self._back_to_zero = True

    def set_trigger(self, trigger=True, feedback=True):
        self.trigger_active = trigger
        self.feedback_active = feedback

    def set_range(self, xLims, xStep, yLims=None, yStep=None):
        self._set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
        
        if self._detectors is None:
            self.counts = None
        else:
            self.counts = [pl.zeros([self.xNbOfSteps, self.yNbOfSteps]) for detector in self._detectors]
            # print(self.counts)



    def run_scan(self, close_instruments=True, silence_errors=True):

        try:
            self.init_detectors(self._detectors)
            self.init_scanners(self._scanner_axes)

            print('Total number of steps: {}\n'.format(self.totalNbOfSteps) +
                  'X number of steps:     {}\n'.format(self.xNbOfSteps) +
                  'Y number of steps:     {}'.format(self.yNbOfSteps))

            start_time = 0
            first_point = True
            idx = 0

            move_smooth(self._scanner_axes, targets=[self.xPositions[0], self.yPositions[0]])

            print('\nScanners are at start position. Waiting for acquisition.\n')
            print('step \tx (V)\ty (V)')

            for id_y, y in enumerate(self.yPositions):
                firstInRow = True
                
                for id_x, x in enumerate(self.xPositions):
                    idx += 1
                    
                    self._scanner_axes[0].move(x)
                    try:
                        self._scanner_axes[1].move(y)
                    except IndexError:
                        pass

                    # display update
                    print('{}/{} \t{:.1f} \t{:.1f}'.format(idx, self.totalNbOfSteps, x, y))

                    # For first point may wait for a reaction 
                    # (when acquisition is launched in WinSpec and the old Acton spectrometers)
                    if first_point:
                        self.wait_first_point(self._detectors)
                        start_time = time.time()
                        first_point = False
                    else:
                        if idx % 10 == 0:
                            self.print_elapsed_time(start_time=start_time, current_index=idx, total_nb_of_steps=self.totalNbOfSteps)

                        # delay between rows
                        if firstInRow:
                            time.sleep(self.delayBetweenRows)
                            firstInRow = False

                        # delay between points
                        time.sleep(self.delayBetweenPoints)

                    # trigger exposure / detector measurement
                    if self._detectors is not None:
                        for counts, detector in zip(self.counts, self._detectors):
                            counts[id_x, id_y] = detector.readout()   # POSSIBLE BLOCKING BEHAVIOUR HERE! put non blocking (spectros...) before blocking (apds...) in the detectors list

                    time.sleep(self.max_delay_after_readout)  # some old devices will not react immediately to say they are integrating

                    # wait for detector to say it finished
                    self.wait_for_ready(self._detectors)

                # move back to first point of row smoothly
                if y != self.yPositions[-1]:
                    self._scanner_axes[0].move_smooth(target=self.xPositions[0])

            # go smoothly to start position
            if self._back_to_zero:
                print('\nGoing back to 0 V on scanners...')
                move_smooth(self._scanner_axes, targets=[0, 0])

            print('\nSCAN COMPLETED\n' +
                  'X from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.xPositions[0], self.xPositions[-1], self.xStep, self.xNbOfSteps) +
                  'Y from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.yPositions[0], self.yPositions[-1], self.yStep, self.yNbOfSteps) +
                  'Total number of steps: {}'.format(self.totalNbOfSteps))

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


    def save_to_hdf5(self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print("File saved")

    def save_to_npz(self, file_name):
        np.savez(file_name+'.npz', self.counts)

    def plot_counts(self):

        #if ('APD' in self.string_id):
        pl.figure(figsize=(10, 10))
        [X, Y] = pl.meshgrid (self.xPositions, self.yPositions)
        pl.pcolor(X, Y, self.counts[0])
        pl.colorbar()
        pl.show()
        #else:
        #    print("No counts available.. use APD")

    def save_to_txt(self, file_name, array=None, flatten=True):
        if array is None:
            array = self.counts
        if flatten:
            pl.savetxt(file_name, np.array(array).flatten().transpose())
        else:
            pl.savetxt(file_name, array)
        print("\nPower as volts saved in file.")



class XYOptimizer (XYMapper):

    def _optimize (self, axis_id, scan_array):
        # here code to optimize one axis
        time.sleep(self.delayBetweenRows)
        counts = np.zeros (len(scan_array))

        for id_x, x in enumerate(scan_array):
            
            self._scanner_axes[axis_id].move(x)
            time.sleep(self.delayBetweenPoints)

            # trigger exposure / detector measurement
            counts[id_x] = self._detectors[0].readout()   # removed some generality in here

            time.sleep(self.max_delay_after_readout)  # some old devices will not react immediately to say they are integrating

            # wait for detector to say it finished
            self.wait_for_ready(self._detectors)

        fit_params = self._fit_gaussian (scan_array=scan_array, counts=counts)
        return counts, fit_params

    def _fit_gaussian (self, scan_array, counts, do_fit = True):
        p = counts/np.sum(counts)
        x0 = np.sum (p*scan_array)
        v0 = np.sum (p*(scan_array**2)) - x0**2
        s0 = v0**0.5
        ampl0 = 0.5*(counts[0]+counts[-1])
        ampl = max(counts)-ampl0

        fit_params = [ampl0, ampl, x0, s0]

        def gaussian(x, A0, A, x0, sigma):
            return A0 + A*np.exp(-(x-x0)**2 / (2*sigma**2))

        if do_fit:
            x = scan_array
            y = counts
            gmodel = lmfit.Model(gaussian)
            result = gmodel.fit(y, x=x, A0=ampl0, A=ampl, x0=x0, sigma=s0)
            A = result.params['A'].value
            A0 = result.params['A0'].value
            x0 = result.params['x'].value
            sigma = result.params['sigma'].value
            fit_params = [A0, A, x0, sigma]
            
            x_fit = np.linspace (x[0], x[-1], 1000)
            y_fit = gaussian (x_fit)

            #print(result.fit_report())

            pl.plot(x, y, 'o', color='royalblue')
            pl.plot(x_fit, y_fit, color = 'crimson')
            pl.show()
        
        return fit_params
    
    def set_scan_range (self, scan_range=10, scan_step=1):
        self._scan_range = scan_range
        self._scan_step = scan_step
        
    def initialize(self, x0, y0):
        self._x_init = x0
        self._y_init = y0
        xLims = [x0-0.5*self._scan_range, x0+0.5*self._scan_range]
        yLims = [y0-0.5*self._scan_range, y0+0.5*self._scan_range]
        xStep = self._scan_step
        yStep = self._scan_step
        
        self._set_range (xLims=xLims, xStep=xStep, yLims=yLims, yStep=yStep)
        
        
    def _plot_optimization (self):
        
        #x = pl.linspace (self.xPositions[0], self.xPositions[-1], 1000)
        #y = pl.linspace (self.yPositions[0], self.yPositions[-1], 1000)
        #xFit = pl.exp(-(x-self._xm)**2/(2*self._sx**2))
        #yFit = pl.exp(-(y-self._xm)**2/(2*self._sx**2))      
        
        print ('Optimization result: x0 = ', self._xm, ' y0 = ', self._ym)
     
        pl.figure (figsize = (8,5))
        pl.subplot(121)
        pl.plot (self.xPositions, self._xCounts, color='RoyalBlue', marker='o')
        pl.vlines (self._xm, 0.9*min (self._xCounts), 1.1*max(self._xCounts), color='crimson', linewidth=2, linestyles='--')
        pl.xlabel ('voltage (V)', fontsize= 15)       
        pl.ylabel ('counts', fontsize=15)
        pl.subplot(122)
        pl.plot (self.yPositions, self._yCounts, color='RoyalBlue', marker='o')
        pl.vlines (self._ym, 0.9*min (self._xCounts), 1.1*max(self._xCounts), color='crimson', linewidth=2, linestyles='--')
        pl.xlabel ('voltage (V)', fontsize= 15)       
        pl.show()

    def run_optimizer (self, close_instruments=True, silence_errors=True):
        try:
            print ('Running position optimizer...')
            self.init_detectors(self._detectors)
            self.init_scanners(self._scanner_axes)

            #start_time = 0
            #first_point = True
            #idx = 0

            #print ('Moving to start position: ', self._x_init, self._y_init)
            #move_smooth(self._scanner_axes, targets=[self.xPositions[0], self.yPositions[0]])
            self._scanner_axes[0].move_smooth([self._x_init])
            self._scanner_axes[1].move_smooth([self._y_init])

            #print ('Optimizing...')
            self._xCounts, [A0x, Ax, x0, sigma_x] = self._xm, self._sx = self._optimize (axis_id = 0, scan_array = self.xPositions)
            self._xm = x0
            self._scanner_axes[0].move_smooth(self._xm)
            self._yCounts, [A0y, Ay, y0, sigma_y] = self._optimize (axis_id = 1, scan_array = self.yPositions)
            self._ym = y0
            self._scanner_axes[1].move_smooth(self._ym)

            #print ('Done!')
            self._plot_optimization ()
            self.initialize (x0 = self._xm, y0 = self._ym)

            # move to the centre of the gaussian
            #move_smooth(self._scanner_axes, targets=[self.xPositions[0], self.yPositions[0]])

            # here we need to redefine the scan interval

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
