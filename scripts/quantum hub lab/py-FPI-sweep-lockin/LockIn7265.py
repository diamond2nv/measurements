# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 14:00:22 2016

@author: Raphael Proux

Handles Signal Recovery 7265 lockin amplifiers.

Change log:
01/05/2017 - R. Proux - added support to get DAC output voltage using data acquisition

"""

import visa
import time
import pylab as pl

class LockIn7265:
    def __init__(self, eqAddress):
        rm = visa.ResourceManager()
        self.dev = rm.open_resource(eqAddress)
#        eqName = self.dev.query('*IDN?')
#        print eqName
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()    
        
    def sendPulse(self):
        """
        Sends a pulse through the low bit pin of the digital output.
        """
        self.dev.write("BYTE 1")
        self.dev.write("BYTE 0")
        
    def readADCdigital(self, inputId=1):
        """
        Reads the ADC input specified by its number inputId and returns a boolean
        according to TTL convention (True > 2 V)
        """
        
        assert(1 <= inputId <= 3)
        res = int(self.dev.query("ADC {}".format(inputId)))
        #print res
        if res > 2000:
            return True
        else:
            return False

    def setDACvoltage(self, outputId=1, voltage=0.):
        """
        Sets the DAC output specified by its number outputId, voltage is in volts
        """
        
        assert(type(outputId) == int and 1 <= outputId <= 4), 'setDACvoltage was called for DAC{}. Has to be DAC1, 2, 3 or 4.'.format(outputId)
        voltage *= 1000
        self.dev.write("DAC {} {:.0f}".format(outputId, voltage))

    def getDACvoltage(self, outputId=1):
        """ 
        Gets the DAC output voltage in V.
        ATTENTION: only available for DAC1 and 2
        """
        
        assert(type(outputId) == int and 1 <= outputId <= 2), 'getDACvoltage is only available for DAC1 and 2.'
        
        if outputId == 1:  # DAC1
            identifier = '256'
        else:  # DAC2
            identifier = '512'
        self.dev.write("CBD {}".format(identifier))  # set buffer to acquire DAC voltage
        self.dev.write("LEN 1")                      # set length of curve to 1
        self.dev.write("TD")                         # launch measurement (only one sample to acquire)
        voltage = self.dev.query("DCT {}".format(identifier))  # dump data in table format to computer
        
        return float(voltage) / 1000  # return voltage in volts
        

    def lockinGoSmoothlyToVoltage(self, newVoltage, step=50, delay=0.05, outputId=2):
        """ lockin should be a LockIn7265() instance. newVoltage and step is in mV, delay is in seconds. """
        currentVoltage = int(self.getDACvoltage(outputId=outputId) * 1000)
        nb_of_steps = int(abs(newVoltage - currentVoltage) / (step)) + 1
        voltageSteps = pl.linspace(currentVoltage, int(newVoltage), nb_of_steps, dtype=int)
        
    #    print voltageSteps
        for voltage in voltageSteps:
            self.setDACvoltage(outputId=outputId, voltage=float(voltage) / 1000)
            time.sleep(delay)
            
        self.setDACvoltage(outputId=outputId, voltage=float(newVoltage) / 1000)

    def close(self):
        self.dev.close()
        
if __name__ == "__main__":
  
    with LockIn7265('GPIB0::12::INSTR') as test:
        time.sleep(1)
        for voltage in pl.linspace(0,1,10):
                print test.getDACvoltage(outputId=2)
                time.sleep(0.5)

    