# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 14:00:22 2016

@author: Raphael Proux
"""

import visa
import time

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

    def writeDAC(self, value, inputId=2):
        """
        Writes a voltage in volts to DAC specified by its inputID
        """
        self.dev.write("DAC. {} {}".format(inputId, float(value)))       
    
    def close(self):
        pass
        
if __name__ == "__main__":
  
    with LockIn7265() as test:
        time.sleep(1)
        for i in xrange(10):
            while True:
                res = test.readADCdigital()
                print(res)
                if not res:
                    break
                time.sleep(0.1)
            test.sendPulse()
            time.sleep(0.5)  # important! due to lag in the controller response
            

    