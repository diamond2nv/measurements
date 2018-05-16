# -*- coding: utf-8 -*-
"""
Created on June 2016
Last modified on 20/02/2017 by Raphael Proux

@author: ted santana and raphael proux

Library to handle the Agilent 34401A Multimeter (table-top)
"""

import visa

class AgilentMultimeter():

    """ Drives Agilent 34401A benchtop multimeter.
    
    Attributes:
        agilent (pyvisa.resources.Resource): pyvisa instrument used for communication
    """
    
    def __init__(self, VISA_address, meas_mode='voltage'):
        """ Constructs a driving library for the Agilent 34401A benchtop multimeter.
        
        Args:
            VISA_address (str): String containing the visa address (e.g. 'ASRL17::INSTR')
            meas_mode (str, optional): measurement mode, i.e. 'voltage' or 'current'. 
                    Determines what is measured by the multimeter then, when calling read, etc.
        
        Raises:
            IOError: error raised if the device is not detected as an Agilent multimeter. 
                    Used mostly to differentiate it from the Keithley multimeters.
        """
        rm = visa.ResourceManager()    # open management indicating the visa path 
        self.agilent = rm.open_resource(VISA_address)

        if not self.is_agilent():
            self.close()
            raise IOError('This device is not an AgilentMultimeter.')
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

    def is_agilent(self):
        """ Determines whether this device is an Agilent multimeter (in particular, not a Keithley multimeter).
        
        Returns:
            bool: True if this device is an Agilent multimeter, False otherwise.
        """
        self.agilent.write('*IDN?')
        if 'HEWLETT' in self.agilent.read():
            return True
        else:
            return False
        
    def read(self):
        """ Reads the last measurement value from the device. Current if the device was initialised in 'current' mode, 'voltage' otherwise.
        
        Returns:
            float: last value measured (current in amperes or voltage in volts, depending on configured measurement mode)
        """
        return self.agilent.query_ascii_values(':read?')[0]
        
    def configureVoltageMeas(self):
        """ Sets the device to measure voltage in volts. """
        self.agilent.write(":configure:voltage:DC")
        self.agilent.write(r'VOLT:DC:resolution MAX')
        
    def configureCurrentMeas(self):
        """ Sets the device to measure current in amperes. """
        self.agilent.write(":configure:current:DC")
        self.agilent.write(r'CURR:DC:resolution MAX')
    
    def close(self):
        """ Closes the connection to the instrument. """
        try:
            self.agilent.close()
        except visa.InvalidSession:  # resource already closed
            pass


if __name__ == "__main__":
    
    # to time the execution of one measurement    
    
    import time
    numberOfTries = 10
    
    with AgilentMultimeter(r'ASRL17::INSTR') as dev:
        startTime = time.time()
        value = 0
        for i in range(numberOfTries):
            value += dev.read()
        endTime = time.time()
    value /= numberOfTries
    print((endTime - startTime) / numberOfTries, 's')
    print('mean value: {}'.format(value))