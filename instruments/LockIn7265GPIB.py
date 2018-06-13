# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 14:00:22 2016

@author: Raphael Proux

Minimal library to handle Signal Recovery 7265 lockin amplifiers.

Change log:
01/05/2017 - R. Proux - added support to get DAC output voltage using data acquisition

"""

import visa
import time
import pylab as pl

class LockIn7265:

    """Handles a Signal Recovery 7265 lockin amplifier.
    
    Attributes:
        dev (pyvisa.resources.Resource): pyvisa instrument used for communication
    """
    
    def __init__(self, VISA_address):
        """Constructs a LockIn7265 object for the Signal Recovery 7265 lockin amplifier.
        
        Args:
            VISA_address (str): String containing the visa address (e.g. 'ASRL17::INSTR')
        """
        rm = visa.ResourceManager()
        self.dev = rm.open_resource(VISA_address)
    
    def __enter__(self):
        """ Method used in the 'with...as' structure for initialisation, just returns the current object constructed. """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Method used in the 'with...as' structure for destruction, closes the instrument calling the self.close() function. """
        self.close()    
        
    def send_pulse(self):
        """
        Sends a pulse through the low bit pin of the digital output.
        """
        self.dev.write("BYTE 1")
        self.dev.write("BYTE 0")
        
    def read_ADC_digital(self, input_id=1):
        """
        Reads the specified ADC input (analog) to use it as a virtual digital input.
        
        Args:
            input_id (int, optional): ADC input identifier
        
        Returns:
            bool: input state according to TTL convention (True > 2 V, False otherwise)
        """
        
        assert(1 <= input_id <= 3)
        res = int(self.dev.query("ADC {}".format(input_id)))
        
        if res > 2000:
            return True
        else:
            return False

    def set_DAC_voltage(self, output_id=1, voltage=0.):
        """
        Sets the DAC output voltage in volts.
        
        Args:
            output_id (int, optional): output identifier
            voltage (float, optional): new voltage to set in volts
        """
        
        assert(type(output_id) == int and 1 <= output_id <= 4), f'set_DAC_voltage() was called for DAC{output_id}. Has to be DAC1, 2, 3 or 4.'
        voltage *= 1000
        self.dev.write("DAC {} {:.0f}".format(output_id, voltage))

    def get_DAC_voltage(self, output_id=1):
        """
        Gets the DAC output voltage in volts. ATTENTION: only available for DAC1 and 2
        
        Args:
            output_id (int, optional): output identifier
        
        Returns:
            float: set DAC voltage in volts
        """
        
        assert(type(output_id) == int and 1 <= output_id <= 2), f'get_DAC_voltage() was called for DAC{output_id}. Has to be DAC1 and 2.'
        
        if output_id == 1:  # DAC1
            identifier = '256'
        else:  # DAC2
            identifier = '512'
        self.dev.write("CBD {}".format(identifier))  # set buffer to acquire DAC voltage
        self.dev.write("LEN 1")                      # set length of curve to 1
        self.dev.write("TD")                         # launch measurement (only one sample to acquire)
        voltage = self.dev.query("DCT {}".format(identifier))  # dump data in table format to computer
        
        return float(voltage) / 1000  # return voltage in volts
        

    def move_smooth_to_voltage(self, new_voltage, step=50., delay=0.05, output_id=2):
        """ Move smoothly the voltage of a specified DAC output to new_voltage in millivolts.
        
        Args:
            new_voltage (float): voltage to go to in mV (ATTENTION)
            step (float, optional): step for the smooth movement in mV
            delay (float, optional): delay between each step of the smooth movement in seconds
            output_id (int, optional): DAC output identifier.
        """
        current_voltage = int(self.get_DAC_voltage(output_id=output_id) * 1000)
        nb_of_steps = int(abs(new_voltage - current_voltage) / (step)) + 1
        voltage_steps = pl.linspace(current_voltage, int(new_voltage), nb_of_steps, dtype=int)
        
    #    print voltage_steps
        for voltage in voltage_steps:
            self.set_DAC_voltage(output_id=output_id, voltage=float(voltage) / 1000)
            time.sleep(delay)
            
        self.set_DAC_voltage(output_id=output_id, voltage=float(new_voltage) / 1000)

    def close(self):
        """ Closes the communication with the instrument. """
        self.dev.close()
        
if __name__ == "__main__":
  
    with LockIn7265('GPIB0::12::INSTR') as test:
        time.sleep(1)
        for voltage in pl.linspace(0, 1, 10):
                print(test.get_DAC_voltage(output_id=2))
                time.sleep(0.5)

    