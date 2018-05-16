# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 15:40:00 2017

@author: Raphael Proux

Library which handles the Keithley 2220 dual channel power supply.
This device was tested using USB connection. It does not need drivers (I think)
but may use VISA preinstalled drivers from national instruments (not sure).
It should work also via GPIB.

"""

import visa
import re

class Keithley2220channelModes:

    """Structure style class used to reference the channel mode string identifiers for the Keithley 2220 PSU
    
    Attributes:
        OFF (str): string identifier of no channel combination mode
        PARALLEL (str): string identifier of parallel channel combination mode
        SERIES (str): string identifier of series channel combination mode
    """
    
    OFF = 'off'
    PARALLEL = 'parallel'
    SERIES = 'series'

class Keithley2220:

    """Handles the communication with a Keithley 2220 power supply unit via a VISA interface.
    
    Attributes:
        chMode (str): instance of Keithley2220channelModes for local access
        dev (pyvisa.resources.Resource): pyvisa instrument used for communication
    """
    
    chMode = Keithley2220channelModes
    
    def __init__(self, VISA_address):
        """ Constructs a Keithley2220 object used for communication with the device.
        
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
        
    def read(self):
        """ Read a response from the device, prepared as a string without the new line characters.
        
        Returns:
            str: Response from the device.
        """
        return self.dev.read().rstrip('\n')
        
    def write(self, message):
        """ Writes a message to the device.
        
        Args:
            message (str): Message to the device.
        """
        self.dev.write(message)
        
    def query(self, message):
        """ Writes a message to the device and reads the response.
        
        Args:
            message (str): Message to the device.
        
        Returns:
            str: Response from the device.
        """
        self.write(message)
        response = self.read()
        return response
    
    
    def channel_select(self, channel):
        """Selects current channel to be affected by subsequent queries. 
        
        Args:
            channel (int): channel identifier (1 and 2 on the Keithley 2220 PSU)
        """
        self.write('INST:SEL CH{}'.format(channel))
        assert self.get_selected_channel() == channel, 'Could not select channel.'
        

    def get_selected_channel(self):
        """Returns the integer identifier of the currently selected channel 
        
        Returns:
            int: selected channel identifier
        """
        return int(re.findall(r'\d',self.query('INST:SEL?'))[0])
        

    def channel_enabled(self, channel=0):
        """
        Checks whether specified channel is enabled. 
        
        Args:
            channel (int, optional): channel identifier (0 for both channels)
        
        Returns:
            bool: True for output enabled, False for output disabled. (ATTENTION: True if one channel is enabled and checking both channels)
        """
        if channel == 0:
            ch = [1, 2]
        else:
            ch = [channel]
        
        response = False
        for c in ch:
            self.channel_select(c)
            response = response or bool(int(self.query('OUTPUT:ENABLE?')))
             
        return response
        
    
    def channel_enable(self, channel=0, state=True):
        """
        Enables the specified channel.
        
        Args:
            channel (int, optional): channel identifier, 0 for both channels.
            state (bool, optional): True if you want to enable the channel, False otherwise. Default is True.
        """
        if channel == 0:
            ch = [1, 2]
        else:
            ch = [channel]
        
        for c in ch:
            self.channel_select(c)
            if state:
                self.write('OUTPUT:ENABLE ON')
            else:
                self.write('OUTPUT:ENABLE OFF')
    
    def output_is_on(self):
        """Checks if the output is on (if there is actual voltage applied on the output). 
        
        Returns:
            bool: True for output on, False for output off. 
        """
        return bool(int(self.query('OUTPUT?')))
        
    def output_on(self, state=True):
        """Switches on or off the output voltage.
        
        Args:
            state (bool, optional): True for output on, False for output off. Default is True.
        """
        if state:
            self.write('OUTPUT ON')
        else:
            self.write('OUTPUT OFF')
            

    def set_voltage(self, channel, voltage):
        """Sets voltage in V to specified channel 
        
        Args:
            channel (int): channel identifier
            voltage (float): voltage value to set, in volts.
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            pass
        else:
            self.write('VOLT {}V'.format(voltage))
    
    def read_set_voltage(self, channel):
        """Reads voltage set to specified channel, in V 
        
        Args:
            channel (int): channel identifier
        
        Returns:
            float: set voltage in volts of specified channel (may differ from actual voltage, see read_voltage())
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            return None
        else:
            return float(self.query('VOLT?'))
    
    def read_voltage(self, channel, repeat=1):
        """measures voltage from specified channel, in V.
        
        Args:
            channel (int): channel identifier
            repeat (int, optional): number of measurements (default 1), then mean val returned. 
        
        Returns:
            float: measured voltage in volts of specified channel (may differ from set voltage, see read_set_voltage())
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            return None
        else:
            response = 0.
            for i in range(repeat):
                response += float(self.query('MEAS:VOLT:DC?'))
            response /= repeat
            return response
        
    
    def set_current(self, channel, current):
        """sets current in A to specified channel 
        
        Args:
            channel (int): channel identifier
            current (float): current value to set, in amperes.
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            pass
        else:
            self.write('CURR {}A'.format(current))
    
    def read_set_current(self, channel):
        """reads current set to specified channel, in A 
        
        Args:
            channel (int): channel identifier
        
        Returns:
            float: set current in amperes of specified channel (may differ from actual voltage, see read_current())
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            return None
        else:
            return float(self.query('CURR?'))
    
    def read_current(self, channel, repeat=1):
        """measures current from specified channel, in A.
        
        Args:
            channel (int): channel identifier
            repeat (int, optional): number of measurements (default 1), then mean val returned. 
        
        Returns:
            float: measured current in amperes of specified channel (may differ from set value, see read_set_current())
        """
        try:
            self.channel_select(channel)
        except AssertionError:
            return None
        else:
            response = 0.
            for i in range(repeat):
                response += float(self.query('MEAS:CURR:DC?'))
            response /= repeat
            return response
    
    
    def channel_combine(self, combMode=chMode.OFF):
        """
        To set channel combination mode. Default is no combination.
        Be aware that this also has the effect of switching the output off,
        thus it needs to be followed by an outputOn() call to apply voltage.
        
        Args:
            combMode (str, optional): mode identifier string. Possible values are given by self.chMode:
                self.chMode.OFF: no combination, channels are independent.
                self.chMode.PARALLEL: channels are controlled as one channel, set in parallel, delivering the same voltage.
                self.chMode.SERIES: channels are controlled as one channel delivering the sum of the voltages.
        """
        if combMode == self.chMode.OFF:
            self.write('INST:COM:OFF')
        elif combMode == self.chMode.PARALLEL:
            self.write('INST:COM:PARA')
        elif combMode == self.chMode.SERIES:
            self.write('INST:COM:SER')
            
            
    def close(self):
        """ Closes the communication with the device. """
        self.dev.close()

  
if __name__ == "__main__":
    with Keithley2220(visaAddress=r'GPIB0::10::INSTR') as keithleyPSU:
        response = keithleyPSU.query('*IDN?')
        
        print(repr(response))

        print(repr(keithleyPSU.get_selected_channel()))

        keithleyPSU.channel_select(1)
        print('hello')
        keithleyPSU.channel_select(2)
        print('hello')
        keithleyPSU.channel_select(1)
        keithleyPSU.channel_select(2)
        keithleyPSU.channel_select(1)
        keithleyPSU.channel_select(2)
        keithleyPSU.channel_select(0)

#        response = keithleyPSU.query('*IDN?')
#        
#        print repr(response)
        
        #response = keithleyPSU.query('OUTPUT?')
        
        # keithleyPSU.channel_enable(state=True, channel=0)
        
        # keithleyPSU.channel_combine(keithleyPSU.chMode.OFF)
        
        # keithleyPSU.output_on(True)
        # keithleyPSU.set_voltage(channel=1, voltage=10)
        # print(keithleyPSU.read_voltage(channel=1))
        # keithleyPSU.set_current(channel=1, current=1)
        # print(keithleyPSU.read_set_current(channel=1))
        
        #print repr(lockin.query('CH1 6'))
        #print 'response: {}'.format(response)
        #print response
    