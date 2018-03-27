# -*- coding: utf-8 -*-
"""
Created on June 2016

@author: ted santana

modified by raphael proux (added close statements to restore local operation
and Keithley() argument to define GPIB address instantiating the class)
"""

import visa

class Keithley():
    """After initializing the class and calling the function 'read', the value of the voltage reading in the multimeter will be loaded in the variable avgVoltage."""
    def __init__(self, eqAdress):
        rm = visa.ResourceManager()    # open management indicating the visa path
        self.keithley = rm.open_resource(eqAdress)
        self.keithley.write(":configure:voltage:DC")
        self.keithley.write(":initiate:continuous ON")
    
    def read(self):
        return self.keithley.query_ascii_values(':fetch?')[0]
    
    def close(self):
        self.keithley.write(":system:key 17")  # restore local operation
        self.keithley.close()
  
  
if __name__ == "__main__":
    
    # to time the execution of one measurement    
    
    import time 
    numberOfTries = 500
    dev = Keithley(r'ASRL11::INSTR')
    startTime = time.time()
    for i in xrange(numberOfTries):
        dev.read()
    endTime = time.time()
    dev.close()
    
    print (endTime - startTime) / numberOfTries, 's'