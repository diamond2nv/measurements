# -*- coding: utf-8 -*-
"""
Created on Mon Nov 26 18:56:04 2018

@author: Ted Santana, C Bonato, M Brotons
"""

import pyvisa
import time

class mag4g:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.dev = rm.open_resource(address, write_termination='\r', read_termination='\r\n')

        self._verbose = False

        for a in range(5):
            self.dev.write('REMOTE')
            a = self.dev.read()
            if (a[:6]=='REMOTE'):
                print ("Device initialization succeeded.")
                break
            print ("Device not initialized to REMOTE. Trying again.")
        self.dev.query('UNITS?')
        if self.dev.read() != 'T':
            self.dev.write('UNITS T')
            self.dev.read()

    
    def set_verbose (self, a):
        self._verbose = a    

    def close(self, sweep_to_zero = True):
        print ("Closing magnet instrument...")
        if sweep_to_zero:
            self.move_to(0)
        self.dev.write('LOCAL')
        self.dev.read()
        self.dev.close()

    def get_lowLim(self):
        self.dev.query('LLIM?')
        x = self.dev.read()
        lowlim = float(x[:-2])
        unit = x[-2:]
        if unit == "kG":
            lowlim /= 10
            unit = "T"
        return lowlim, unit

    def get_highLim(self):
        self.dev.query('ULIM?')
        x = self.dev.read()
        highlim = float(x[:-2])
        unit = x[-2:]
        if unit == "kG":
            highlim /= 10
            unit = "T"
        return highlim, unit

    def set_lowLim(self, low):
        """ in Tesla"""
        low *= 10
        self.dev.write('LLIM {:.3f}'.format(low))
        a = self.dev.read()
        print ("Low limit set to: ", a)

    def set_highLim(self, high):
        """ in Tesla"""
        high *= 10
        self.dev.write('ULIM {:.3f}'.format(high))
        a = self.dev.read()
        print ("High limit set to: ", a)
        
    def get_heater(self):
        self.dev.query('PSHTR?')
        return self.dev.read()
    
    def set_heater(self, on):
        """in Tesla"""
        if on:
            self.dev.write('PSHTR ON')
            self.dev.read()
        else:
            self.dev.write('PSHTR OFF')
            self.dev.read()

    def sweep_pause(self):
        self.dev.write('SWEEP PAUSE')
        self.dev.read()
        
    def sweep_up(self):
        self.dev.write('SWEEP UP FAST')
        self.dev.read()
    
    def sweep_down(self):
        self.dev.write('SWEEP DOWN FAST')
        self.dev.read()
    
    def sweep_to_zero(self):
        self.dev.write('SWEEP ZERO FAST')
        self.dev.read()
    
    def get_field(self):
        self.dev.query('IOUT?')
        x = self.dev.read()
        unit = x[-2:]
        self.field = round(float(x[:-2]),4)
        if unit == "kG":
            self.field /= 10
            unit = "T"
        return self.field, unit
    
    def _check_if_ready (self, B, tolerance):
        actualB, unit = self.get_field()
        if actualB == B:
#                    time.sleep(10)
            self.sweep_pause()
            if self._verbose:
                print ("Sweeep paused: B = {:.3f} T".format(actualB))
            ok = True
        else:
            if self._verbose:
                print ("Sweeping to target: B = {:.3f} T".format(actualB))
            ok = False
            time.sleep(10)
        actualB, unit = self.get_field()
        within_tol = (abs(actualB-B)<tolerance)            
        return ok, within_tol
            
    def move_to(self, B, tolerance = 0.001, nr_tolerance_reps = 5):
        self.set_heater(True)
        is_heater = self.get_heater()
        if not is_heater:
            raise "Heater is off"
        low_lim, _ = self.get_lowLim()
        high_lim, _ = self.get_highLim()
        nr_repeats = 0
        if B == 0:
            self.sweep_to_zero()
            ok = False
            while not ok:
                ok, within_tol = self._check_if_ready (B=0, tolerance = 0)                    
        elif abs(B-high_lim) <= abs(B-low_lim):
            self.set_highLim(B)
            self.sweep_up()
            ok = False
            while not ok:
                ok, within_tol = self._check_if_ready (B=B, tolerance=tolerance)
                if within_tol:
                    nr_repeats += 1
                if nr_repeats >= nr_tolerance_reps:
                    ok = True
        else: # abs(B-high_lim) > abs(B-low_lim)
            self.set_lowLim(B)
            self.sweep_down()
            ok = False
            while not ok:
                ok, within_tol = self._check_if_ready (B=B, tolerance=tolerance)
                if within_tol:
                    nr_repeats += 1
                if nr_repeats >= nr_tolerance_reps:
                    ok = True

        self.set_heater(False)

if __name__=='__main__':
    mag = mag4g()
    mag.move_to(0.05)
    mag.close()