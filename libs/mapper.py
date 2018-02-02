# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 09:23:52 2017

@author: cristian bonato
"""

import pylab as pl
import time
from tools import data_object as DO
import numpy as np


class XYScan ():
    def __init__(self, scanner=None, detectors=None):
        self._scanner = scanner
        self._detectors = detectors

        self.delayBetweenPoints = 1
        self.delayBetweenRows = 0.5
        self.trigger_active = True
        self.feedback_active = True

        self._back_to_zero = False

        # Check what kind of detector is used (spectrometer or apd)
        # if (isinstance (detector, PylonNICtrl) or isinstance (detector, ActonLockinCtrl) or isinstance (detector, ActonNICtrl)):
        #     self.detector_type = 'spectro'
        # elif (isinstance (detector, APDCounterCtrl)):
        #     self.detector_type = 'apd'
        # else:
        #     self.detector_type = 'unknown'

        # determine the longest test delay in the detectors
        self.max_delay_state_check = max([detector.delay_state_check for detector in self._detectors])
        self.max_delay_after_readout = max([detector.delay_after_readout for detector in self._detectors])

    def set_delays (self, between_points, between_rows):
        self.delayBetweenPoints = between_points
        self.delayBetweenRows = between_rows

    def set_back_to_zero(self):
        # to go back to 0 V at the end of a scan
        self._back_to_zero = True

    def set_range (self, xLims, xStep, yLims, yStep):

        self.xNbOfSteps = int(abs(pl.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
        self.xPositions = pl.linspace(xLims[0], xLims[1], self.xNbOfSteps)
        self.yNbOfSteps = int(abs(pl.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
        self.yPositions = pl.linspace(yLims[0], yLims[1], self.yNbOfSteps)
        self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps
        self.xStep = xStep
        self.yStep = yStep

        if self._detectors is None:
            self.counts = None
        else:
            self.counts = [pl.zeros ([self.xNbOfSteps, self.yNbOfSteps]) for detector in self._detectors]

    def set_trigger(self, trigger=True, feedback=True):
        self.trigger_active = trigger
        self.feedback_active = feedback

    def secondsInHMS(self, nbOfSeconds):
        hours = pl.floor(nbOfSeconds / 3600)
        minutes = pl.floor(nbOfSeconds % 3600 / 60)
        seconds = nbOfSeconds - minutes*60 - hours*3600
        return hours, minutes, seconds

    def print_elapsed_time (self, startTime, currentIndex, totalNbOfSteps):
        elapsedTime = float(time.time() - startTime)
        remainingTime = elapsedTime / currentIndex * (totalNbOfSteps - (currentIndex-1))
        
        hoursE, minutesE, secondsE = self.secondsInHMS(elapsedTime)
        hoursR, minutesR, secondsR = self.secondsInHMS(remainingTime)

        print('Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR))

    def wait_first_point(self, detectors):
        if detectors is None:
            pass
        else:
            while not all([detector.first_point() for detector in detectors]):
                time.sleep(self.max_delay_state_check)

    def wait_for_ready(self, detectors):
        if detectors is None:
            pass
        else:
            while not all([detector.is_ready() for detector in detectors]):
                time.sleep(self.max_delay_state_check)

    def init_detectors(self, detectors):
        if detectors is None:
            pass
        else:
            for detector in detectors:
                detector.initialize()

    def run_scan (self):
        try:
            self.init_detectors(self._detectors)
            self._scanner.initialize()

            print('Total number of steps: {}\n'.format(self.totalNbOfSteps) +
                  'X number of steps:     {}\n'.format(self.xNbOfSteps) +
                  'Y number of steps:     {}'.format(self.yNbOfSteps))

            start_time = 0
            first_point = True
            idx = 0

            self._scanner.goSmoothlyToPos(xPos=self.xPositions[0], yPos=self.yPositions[0])

            print('\nScanners are at start position. Waiting for spectrometer acquisition.\n')

            print('step \tx (V)\ty (V)')

            for id_y, y in enumerate(self.yPositions):
                firstInRow = True
                
                for id_x, x in enumerate(self.xPositions):
                    idx += 1
                    
                    self._scanner.moveX(x)
                    self._scanner.moveY(y)

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
                            self.print_elapsed_time(startTime=start_time, currentIndex=idx, totalNbOfSteps=self.totalNbOfSteps)

                        # delay between rows
                        if firstInRow:
                            time.sleep(self.delayBetweenRows)
                            firstInRow = False

                        # delay between points
                        time.sleep(self.delayBetweenPoints)

                        # trigger exposure
                        if self._detectors is not None:
                            for counts, detector in zip(self.counts, self._detectors):
                                counts[id_x, id_y] = detector.readout()   # POSSIBLE BLOCKING BEHAVIOUR HERE! put non blocking (spectros...) before blocking (apds...) in the detectors list

                    time.sleep(self.max_delay_after_readout)  # some old devices will not react immediately to say they are integrating

                    # wait for detector to say it finished
                    self.wait_for_ready(self._detectors)

                # move back to first point of row smoothly
                if y != self.yPositions[-1]:
                    self._scanner.goSmoothlyToPos(xPos=self.xPositions[0], yPos=y)       

            # go smoothly to start position
            if self._back_to_zero:
                print('\nGoing back to 0 V on scanners...')
                self._scanner.goSmoothlyToPos(xPos=0, yPos=0)

            print('\nSCAN COMPLETED\n' +
                  'X from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.xPositions[0], self.xPositions[-1], self.xStep, self.xNbOfSteps) +
                  'Y from {:.2f} V to {:.2f} V with step size {:.2f} V (nb of steps: {})\n'.format(self.yPositions[0], self.yPositions[-1], self.yStep, self.yNbOfSteps) +
                  'Total number of steps: {}'.format(self.totalNbOfSteps))

        except KeyboardInterrupt:
            print('\n####  Program interrupted by user.  ####')
        finally:
            self.counts = counts
            self._scanner.close()
            for detector in self._detectors:
                detector.close()

    def save_to_hdf5(self, file_name=None):

        d_obj = DO.DataObjectHDF5()
        d_obj.save_object_to_file (self, file_name)
        print("File saved")

    def save_to_npz(self, file_name):
        np.savez (file_name+'.npz', xPos = self.xPositions, yPos = self.yPositions, counts = self.counts)

    def plot_counts(self):

        if (self.detector_type == 'apd'):
            pl.figure(figsize=(10, 10))
            pl.pcolor (self.counts)
            pl.show()
        else:
            print("No counts available.. use APD")


    def save_volts(self, counts_array, filename, flatten=True):
        if flatten:
            pl.savetxt(filename, counts_array.flatten().transpose())
        else:
            pl.savetxt(filename, counts_array)
        print("\nPower as volts saved in file.")
