# -*- coding: utf-8 -*-
"""
Created on June 2016
Last modified on 14/02/2017 by Raphael Proux

@author: ted santana and raphael proux

Library to handle the Keithley 2000 Multimeter (table-top)
"""

import visa

class KeithleyMultimeter():

    def __init__(self, visaAddress, measConfig='voltage'):
        rm = visa.ResourceManager()    # open management indicating the visa path 
        self.keithley = rm.open_resource(visaAddress)
        
        if measConfig == 'voltage':
            self.configureVoltageMeas()
        elif measConfig == 'current':
            self.configureCurrentMeas()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def read(self):
        return self.keithley.query_ascii_values(':fetch?')[0]
        
    def configureVoltageMeas(self):
        self.keithley.write(":configure:voltage:DC")
        self.keithley.write(":initiate:continuous ON")
        
    def configureCurrentMeas(self):
        self.keithley.write(":configure:current:DC")
        self.keithley.write(":initiate:continuous ON")
    
    def close(self):
        self.keithley.write(":system:key 17")  # restore local operation
        self.keithley.close()
  
  
if __name__ == "__main__":
    
    # to time the execution of one measurement    
    
    import time 
    numberOfTries = 500
    
    with KeithleyMultimeter(r'GPIB0::13::INSTR') as dev:
        startTime = time.time()
        value = 0
        for i in xrange(numberOfTries):
            value += dev.read()
        endTime = time.time()
    value /= numberOfTries
    print (endTime - startTime) / numberOfTries, 's'
    print 'mean value: {}'.format(value)