# -*- coding: utf-8 -*-
"""
Created on June 2016
Last modified on 14/02/2017 by Raphael Proux

@author: ted santana and raphael proux

Library to handle the Keithley 2000 Multimeter (table-top)
"""

import visa

class KeithleyMultimeter():

    """ Drives Keithley 2000 benchtop multimeter.
    
    Attributes:
        keithley (pyvisa.resources.Resource): pyvisa instrument used for communication
    """

    def __init__(self, VISA_address, meas_mode='voltage'):
        """ Constructs a driving library for the Keithley 2000 benchtop multimeter.
        
        Args:
            VISA_address (str): String containing the visa address (e.g. 'ASRL17::INSTR')
            meas_mode (str, optional): measurement mode, i.e. 'voltage' or 'current'. 
                    Determines what is measured by the multimeter then, when calling read, etc.
        
        Raises:
            IOError: error raised if the device is not detected as a Keithley multimeter. 
                    Used mostly to differentiate it from the Agilent multimeters.
        """
        rm = visa.ResourceManager()    # open management indicating the visa path 
        self.keithley = rm.open_resource(VISA_address)
        
        if not self.is_keithley():
            self.close()
            raise IOError('This device is not an KeithleyMultimeter.')
        if meas_mode == 'voltage':
            self.configureVoltageMeas()
        elif meas_mode == 'current':
            self.configureCurrentMeas()
    
    def __enter__(self):
        """ Method used in the 'with...as' structure for initialisation, just returns the current object constructed. """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Method used in the 'with...as' structure for destruction, closes the instrument calling the self.close() function. """
        self.close()

    def is_keithley(self):
        """ Determines whether this device is a Keithley multimeter (in particular, not an Agilent multimeter).
        
        Returns:
            bool: True if this device is a Keithley multimeter, False otherwise.
        """
        self.keithley.write('*IDN?')
        if 'KEITHLEY' in self.keithley.read():
            return True
        else:
            return False
        
    def read(self):
        """ Reads the last measurement value from the device. Current if the device was initialised in 'current' mode, 'voltage' otherwise.
        
        Returns:
            float: last value measured (current in amperes or voltage in volts, depending on configured measurement mode)
        """
        return self.keithley.query_ascii_values(':fetch?')[0]
        
    def configureVoltageMeas(self):
        """ Sets the device to measure voltage in volts. """
        self.keithley.write(":configure:voltage:DC")
        self.keithley.write(":initiate:continuous ON")
        
    def configureCurrentMeas(self):
        """ Sets the device to measure current in amperes. """
        self.keithley.write(":configure:current:DC")
        self.keithley.write(":initiate:continuous ON")
    
    def close(self):
        """ Closes the connection to the instrument. """
        try:
            self.keithley.write(":system:key 17")  # restore local operation
            self.keithley.close()
        except visa.InvalidSession:  # resource already closed
            pass

 
if __name__ == "__main__":
    
    # to time the execution of one measurement    
    
    import time
    numberOfTries = 10
    
    with KeithleyMultimeter(r'ASRL17::INSTR', meas_mode='current') as dev:
        print(dev.is_keithley())
        startTime = time.time()
        value = 0
        for i in range(numberOfTries):
            value += dev.read()
        endTime = time.time()
        dev.close()
    value /= numberOfTries
    print((endTime - startTime) / numberOfTries, 's')
    print('mean value: {}'.format(value))
    