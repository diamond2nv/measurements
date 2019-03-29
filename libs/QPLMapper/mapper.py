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
#try:
from measurements.libs.QPLMapper import ScanGUI as SG
from PyQt5 import QtCore, QtGui, QtWidgets
#except:
#    print ("GUI not available!")
#from measurements.libs.mapper_scanners import move_smooth

if sys.version_info.major == 3:
    from importlib import reload
reload (DO)
reload (SG)


try: 
    from measurements.libs.QPLMapper.mapper_scanners import move_smooth
except:
    def move_smooth(scanner_axes, targets = []):
        pass

    def move_smooth_simple (scanner_axes, targets = []):
        pass

    print ("Simulation mode. Pay attention that the move_smooth function is not implemented!")

class MultiAxisMapper ():
    def __init__(self, scanner_axes=None, detectors=None):
        self._scanner_axes = scanner_axes
        self._detectors = detectors
        self._nr_axes = len(scanner_axes)

        self.delayBetweenPoints = 1
        self.delayBetweenRows = 0.5

        # determine the longest test delay in the detectors
        if self._detectors is not None:
            self.max_delay_state_check = max([detector.delay_state_check for detector in self._detectors])
            self.max_delay_after_readout = max([detector.delay_after_readout for detector in self._detectors])
        else:
            self.max_delay_state_check = 0
            self.max_delay_after_readout = 0

        self._nr_steppers = 0

    def add_stepper (self, stepper):
        self._nr_steppers += 1
        setattr (self, '_stepper_'+str(self._nr_steppers), stepper)

    def set_delays(self, between_points, between_rows):
        self.delayBetweenPoints = between_points
        self.delayBetweenRows = between_rows

    def _calculate_range(self, lims, step):

        nbOfSteps = int(abs(pl.floor((float(lims[1]) - float(lims[0])) / float(step))) + 1)
        positions = pl.linspace(lims[0], lims[1], nbOfSteps)
        return positions

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

class OptimizeableMapper (MultiAxisMapper):

    def __init__ (self, scanner_axes, detectors):
        super().__init__ (scanner_axes = scanner_axes, detectors = detectors)

        self._opt_range = []
        self._opt_steps = 1
        self._opt_fit_points = 100
        self._optimizer_ready = False

    def _optimize (self, axis_id, detector_id):

        print ("Optimize-FULL")
        # code to optimize one axis
        time.sleep(self.delayBetweenRows)
        counts = np.zeros (self._opt_steps[axis_id])

        for id_x, x in enumerate(self._opt_positions[str(axis_id)]):
            
            self._scanner_axes[axis_id].move(x)
            time.sleep(self.delayBetweenPoints)

            counts[id_x] = self._detectors[detector_id].readout()

            time.sleep(self.max_delay_after_readout)
            self.wait_for_ready([self._detectors[detector_id]])
            
        fit_result, fit_plot_x, fit_plot_y = self._fit_gaussian (scan_array=self._opt_positions[str(axis_id)], counts=counts)

        return counts, fit_result, fit_plot_x, fit_plot_y

    def _optimize_single (self, axis_id, detector_id, scan_array):

        print ("Optimize-SINGLE")
        # code to optimize one axis
        time.sleep(self.delayBetweenRows)
        counts = np.zeros (len(scan_array))

        for id_x, x in enumerate(scan_array):
            
            self._scanner_axes[axis_id].move(x)
            time.sleep(self.delayBetweenPoints)

            counts[id_x] = self._detectors[detector_id].readout()

            time.sleep(self.max_delay_after_readout)
            self.wait_for_ready([self._detectors[detector_id]])
            
        fit_result, fit_plot_x, fit_plot_y = self._fit_gaussian (scan_array=scan_array, counts=counts)

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
            
            x_fit = np.linspace (x[0], x[-1], self._opt_fit_points)
            y_fit = _gaussian (x=x_fit, A0=A0, A=A, x0=x0, sigma=sigma )

            if do_print_fit_report:
                print(result.fit_report())
        
        return result, x_fit, y_fit
    
       
    def initialize_optimizer (self, x0, opt_range=[], opt_steps=[], ids = None):

        if (ids == None):
            self._ids = np.arange(len(self._scanner_axes))
        else:
            self._ids = ids

        ids = self._ids
        if ((len(ids)==len(x0)) and (len(ids)==len(opt_range)) and (len(ids)==len(opt_steps))):

            self._nr_ids = len(ids)
            self._x_init = np.array([None]*len(self._scanner_axes))
            self._opt_range = np.array([None]*len(self._scanner_axes))
            self._opt_steps = np.array([None]*len(self._scanner_axes))
            self._opt_range[ids] = opt_range
            self._opt_steps[ids] = opt_steps
            self._x_init[ids] = x0

            self._opt_positions = {}

            for i in ids:
                self._opt_positions [str(i)] = np.linspace(self._x_init[i]-0.5*self._opt_range[i], 
                            self._x_init[i]+0.5*self._opt_range[i], self._opt_steps[i])
            self._optimizer_ready = True

        else:
            print ("Incorrect optimizer initialization settings!")
            self._optimizer_ready = False
                                  
    def run_optimizer (self, detector_id = 0, close_instruments=False, silence_errors=True):

        if self._optimizer_ready:        
            try:
                print ('Running position optimizer...')
                print ('Current position: ', self._x_init)
                self.init_detectors([self._detectors[detector_id]])
                selected_axes = [self._scanner_axes[i] for i in self._ids]
                self.init_scanners(selected_axes)

                opt_x = np.array([None]*len(self._scanner_axes))
                sigmas = np.array([None]*len(self._scanner_axes))
                self.fit_dict = {}

                for i in self._ids:
                    self._scanner_axes[i].move_smooth(self._x_init[i])

                for i in self._ids:
                    counts, fit_result, fit_plot_x, fit_plot_y = self._optimize (axis_id = i, detector_id = detector_id)
                    x_opt = fit_result.params['x0'].value
                    self._scanner_axes[i].move_smooth(x_opt)
                    s = fit_result.params['sigma'].value
                    opt_x [i] = x_opt
                    sigmas [i] = s

                    self.fit_dict [str(i)] = {}
                    self.fit_dict [str(i)] ['x'] = self._opt_positions [str(i)]
                    self.fit_dict [str(i)] ['y'] = counts
                    self.fit_dict [str(i)] ['x_fit'] = fit_plot_x
                    self.fit_dict [str(i)] ['y_fit'] = fit_plot_y
                    self.fit_dict [str(i)] ['x_opt'] = x_opt
                    self.fit_dict [str(i)] ['sigma'] = s

                #self.scanner_axes[i].move_smooth(x_opt)

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
        else:
            print ("Optimizer is not initialized! Cannot start optimization...")

    def optimize_single_axis (self, axis, x0, range, nr_points, detector_id = 0):

        self.init_detectors([self._detectors[detector_id]])
        self.init_scanners([self._scanner_axes[axis]])

        self._scanner_axes[axis].move_smooth(x0)
        scan_array = np.linspace(x0-0.5*range, x0+0.5*range, nr_points)

        counts, fit_result, fit_plot_x, fit_plot_y = self._optimize_single (axis_id = axis, detector_id = detector_id, scan_array=scan_array)
        x_opt = fit_result.params['x0'].value
        self._scanner_axes[axis].move_smooth(x_opt)
        s = fit_result.params['sigma'].value

        fit_dict = {}
        fit_dict['axis_id'] = axis
        fit_dict['x'] = scan_array
        fit_dict['y'] = counts
        fit_dict['x_fit'] = fit_plot_x
        fit_dict['y_fit'] = fit_plot_y
        fit_dict ['x_opt'] = x_opt
        fit_dict ['sigma'] = s

        return fit_dict




class XYScan (OptimizeableMapper):
    def __init__(self, scanner_axes=None, detectors=None):
        
        self.trigger_active = True
        self.feedback_active = True
        self._back_to_zero = False

        super().__init__ (scanner_axes = scanner_axes, detectors = detectors)

    def set_back_to_zero(self):
        # to go back to 0 V at the end of a scan
        self._back_to_zero = True

    def set_trigger(self, trigger=True, feedback=True):
        self.trigger_active = trigger
        self.feedback_active = feedback

    def set_range(self, xLims, xStep, yLims=None, yStep=None):
        p = self._calculate_range (lims=xLims, step=xStep)
        self.xPositions = p
        self.xNbOfSteps = len(p)
        self.xStep = xStep

        if yLims is not None or yStep is not None:
            p = self._calculate_range (lims=yLims, step=yStep)
            self.yPositions = p
            self.yNbOfSteps = len(p)
            self.yStep = xStep
        else:
            self.yNbOfSteps = 1
            self.yPositions = pl.array([0])
            self.yStep = 0
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps
        
        if self._detectors is None:
            self.counts = None
        else:
            for idx, d in enumerate (self._detectors):
                setattr (self, 'detector_readout_'+str(idx), 
                            pl.zeros([self.xNbOfSteps, self.yNbOfSteps]))             

    def run_scan(self, close_instruments=True, silence_errors=True, do_move_smooth = True):

        try:
            self.init_detectors(self._detectors)
            self.init_scanners(self._scanner_axes)

            print('Total number of steps: {}\n'.format(self.totalNbOfSteps) +
                  'X number of steps:     {}\n'.format(self.xNbOfSteps) +
                  'Y number of steps:     {}'.format(self.yNbOfSteps))

            start_time = 0
            first_point = True
            idx = 0

            if do_move_smooth:
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
                        for i, detector in enumerate (self._detectors):
                            getattr (self, 'detector_readout_'+str(i))[id_x, id_y] = detector.readout()

                    time.sleep(self.max_delay_after_readout)  # some old devices will not react immediately to say they are integrating

                    # wait for detector to say it finished
                    self.wait_for_ready(self._detectors)

                # move back to first point of row smoothly
                if y != self.yPositions[-1]:
                    self._scanner_axes[0].move_smooth(target=self.xPositions[0])

            # go smoothly to start position
            if do_move_smooth:
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
                print ("Closing all instruments.")
                self.close_instruments()


    def save_to_hdf5(self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print("File saved")

    def save_to_npz(self, file_name):
        np.savez(file_name+'.npz', self.counts)

    def plot_counts(self, detector_numbers = None):

        if (detector_numbers == None):
            detector_numbers = range(len(self._detectors))

        for i in detector_numbers:
            pl.figure(figsize=(10, 10))
            [X, Y] = pl.meshgrid (self.xPositions, self.yPositions)
            pl.pcolormesh(X, Y, getattr(self, 'detector_readout_'+str(i) ).transpose(), cmap='Greys')
            pl.title ("detector nr "+str(i), fontsize=18)
            pl.colorbar()
            pl.show()

    def save_to_txt(self, file_name, array=None, flatten=True):
        if array is None:
            array = self.detector_readout_0

        if not(file_name.endswith('.txt')):
            file_name = file_name+'.txt'

        if flatten:
            pl.savetxt(file_name, np.array(array).flatten().transpose())
        else:
            pl.savetxt(file_name, array)
        print("\nPower as volts saved in file.")


class XYScanIterative (OptimizeableMapper):
    def __init__(self, scanner_axes=None, detectors=None):
        
        self.trigger_active = True
        self.feedback_active = True
        self._back_to_zero = False

        super().__init__ (scanner_axes = scanner_axes, detectors = detectors)
        self._iterative = True

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
            for idx, d in enumerate (self._detectors):
                setattr (self, 'detector_readout_'+str(idx), 
                            pl.zeros([self.xNbOfSteps, self.yNbOfSteps]))    

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


    def next_point (self):

        y = self.yPositions[self._id_y]
        x = self.xPositions[self._id_x]
        self._idx += 1
       
        self._scanner_axes[0].move(x)
        try:
            self._scanner_axes[1].move(y)
        except IndexError:
            pass

        # display update
        print('{}/{} \t{:.1f} \t{:.1f}'.format(self._idx, self.totalNbOfSteps, x, y))

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
                getattr (self, 'detector_readout_'+str(i))[self._id_x, self._id_y] = detector.readout()

        time.sleep(self.max_delay_after_readout)

        # wait for detector to say it finished
        self.wait_for_ready(self._detectors)

        self._prepare_next_point()

    def _prepare_next_point (self):

        self._id_x +=1

        if (self._id_x >= self.xNbOfSteps):
            self._id_x = 0
            self._id_y +=1

            if (self._id_y >= self.yNbOfSteps):        
                self.close_scan()
            else:
                # move back to first point of row smoothly
                if self.yPositions[self._id_y] != self.yPositions[-1]:
                    self._scanner_axes[0].move_smooth(target=self.xPositions[0])

    def open_GUI (self):     
        qApp=QtWidgets.QApplication.instance() 
        if not qApp: 
            qApp = QtWidgets.QApplication(sys.argv)

        gui = SG.ScanGUI (scanner=self)
        gui.setWindowTitle('QPL-ScanGUI')
        gui.show()
        sys.exit(qApp.exec_())

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

    def save_to_hdf5(self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print("File saved")

class Mapper2D_XYZ (OptimizeableMapper):

    def __init__(self, scanner_axes=None, detectors=None):

        super().__init__ (scanner_axes = scanner_axes, detectors = detectors)
        
        self.trigger_active = True
        self.feedback_active = True
        self._back_to_zero = False

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
        p = self._calculate_range (lims=xLims, step=xStep)
        self.xPositions = p
        self.xNbOfSteps = len(p)
        self.xStep = xStep

        if yLims is not None or yStep is not None:
            p = self._calculate_range (lims=yLims, step=yStep)
            self.yPositions = p
            self.yNbOfSteps = len(p)
            self.yStep = yStep
        else:
            self.yNbOfSteps = 1
            self.yPositions = pl.array([0])
            self.yStep = 0
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps
        
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

        sys.exit(qApp.exec_())

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

