# -*- coding: utf-8 -*-
"""
Created on June 2016
Last modified on 20/02/2017 by Raphael Proux

@author: ted santana and raphael proux

Library to handle the Agilent 34401A Multimeter (table-top)
"""

import visa

class AgilentMultimeter():

    def __init__(self, visaAddress, measConfig='voltage'):
        rm = visa.ResourceManager()    # open management indicating the visa path 
        self.agilent = rm.open_resource(visaAddress)
        
        if measConfig == 'voltage':
            self.configureVoltageMeas()
        elif measConfig == 'current':
            self.configureCurrentMeas()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def read(self):
        return self.agilent.query_ascii_values(':read?')[0]
        
    def configureVoltageMeas(self):
        self.agilent.write(":configure:voltage:DC")
        self.agilent.write(r'VOLT:DC:resolution MAX')
        
    def configureCurrentMeas(self):
        self.agilent.write(":configure:current:DC")
        self.agilent.write(r'CURR:DC:resolution MAX')
    
    def close(self):
        #self.agilent.write(":system:key 17")  # restore local operation
        self.agilent.close()
  
  
if __name__ == "__main__":
    
    # to time the execution of one measurement    
    
    import time 
    numberOfTries = 10
    
    with AgilentMultimeter(r'GPIB0::23::INSTR') as dev:
        startTime = time.time()
        value = 0
        for i in xrange(numberOfTries):
            value += dev.read()
        endTime = time.time()
    value /= numberOfTries
    print (endTime - startTime) / numberOfTries, 's'
    print 'mean value: {}'.format(value)