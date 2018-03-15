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
    OFF = 'off'
    PARALLEL = 'parallel'
    SERIES = 'series'

class Keithley2220:
    chMode = Keithley2220channelModes
    
    def __init__(self, visaAddress):
        rm = visa.ResourceManager()
        self.dev = rm.open_resource(visaAddress)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def read(self):
        return self.dev.read().rstrip('\n')
        
    def write(self, message):
        self.dev.write(message)
        
    def query(self, message):
        self.write(message)
        response = self.read()
        return response
    
    
    def channelSelect(self, channel):
        """ Selects current channel to be affected by subsequent queries. """
        self.write('INST:SEL CH{}'.format(channel))
        assert self.get_selected_channel() == channel, 'Could not select channel.'
        

    def get_selected_channel(self):
        """ Returns the integer identifier of the currently selected channel """
        return int(re.findall(r'\d',self.query('INST:SEL?'))[0])
        

    def channelEnabled(self, channel=0):
        """ True for output enabled, False for output disabled.
        channel=0 for both channels (true if one channel is enabled). """
        if channel == 0:
            ch = [1, 2]
        else:
            ch = [channel]
        
        response = False
        for c in ch:
            self.channelSelect(c)
            response = response or bool(int(self.query('OUTPUT:ENABLE?')))
             
        return response
        
    
    def channelEnable(self, state, channel=0):
        """ True for output enabled, False for output disabled.
        channel=0 for both channels (true if one channel is enabled). """
        if channel == 0:
            ch = [1, 2]
        else:
            ch = [channel]
        
        response = False
        for c in ch:
            self.channelSelect(c)
            if state:
                self.write('OUTPUT:ENABLE ON')
            else:
                self.write('OUTPUT:ENABLE OFF')
             
        return response
    
    
    def outputIsOn(self):
        """ Checks if the output is on (if there is actual voltage applied on the output). 
        True for output on, False for output off. """
        return bool(int(self.query('OUTPUT?')))
        
    def outputOn(self, state):
        """ Switches on or off the output voltage.
        True for output on, False for output off."""
        if state:
            self.write('OUTPUT ON')
        else:
            self.write('OUTPUT OFF')
            

    def setVoltage(self, channel, voltage):
        """ sets voltage in V to specified channel """
        try:
            self.channelSelect(channel)
        except AssertionError:
            pass
        else:
            print('sent voltage')
            self.write('VOLT {}V'.format(voltage))
    
    def readSetVoltage(self, channel):
        """ reads voltage set to specified channel, in V """
        try:
            self.channelSelect(channel)
        except AssertionError:
            return None
        else:
            return float(self.query('VOLT?'))
    
    def readVoltage(self, channel, repeat=1):
        """ measures voltage from specified channel, in V.
        repeat is the number of measurements (default 1), then meaning val taken. """
        try:
            self.channelSelect(channel)
        except AssertionError:
            return None
        else:
            response = 0.
            for i in range(repeat):
                response += float(self.query('MEAS:VOLT:DC?'))
            response /= repeat
            return response
        
    
    def setCurrent(self, channel, current):
        """ sets current in A to specified channel """
        try:
            self.channelSelect(channel)
        except AssertionError:
            pass
        else:
            self.write('CURR {}A'.format(current))
    
    def readSetCurrent(self, channel):
        """ reads current set to specified channel, in A """
        try:
            self.channelSelect(channel)
        except AssertionError:
            return None
        else:
            return float(self.query('CURR?'))
    
    def readCurrent(self, channel, repeat=1):
        """ measures current from specified channel, in A.
        repeat is the number of measurements (default 1), then meaning val taken. """
        try:
            self.channelSelect(channel)
        except AssertionError:
            return None
        else:
            response = 0.
            for i in range(repeat):
                response += float(self.query('MEAS:CURR:DC?'))
            response /= repeat
            return response
    
    
    def channelCombine(self, combMode=chMode.OFF):
        """
        To set channel combination mode. Default is no combination.
        Be aware that this also has the effect of switching the output off,
        thus it needs to be followed by an outputOn() call to apply voltage.
        """
        if combMode == self.chMode.OFF:
            self.write('INST:COM:OFF')
        elif combMode == self.chMode.PARALLEL:
            self.write('INST:COM:PARA')
        elif combMode == self.chMode.SERIES:
            self.write('INST:COM:SER')
            
            
    def close(self):
        self.dev.close()

  
if __name__ == "__main__":
    with Keithley2220(visaAddress=r'GPIB0::10::INSTR') as keithleyPSU:
        response = keithleyPSU.query('*IDN?')
        
        print(repr(response))

        print(repr(keithleyPSU.get_selected_channel()))

        keithleyPSU.channelSelect(1)
        print('hello')
        keithleyPSU.channelSelect(2)
        print('hello')
        keithleyPSU.channelSelect(1)
        keithleyPSU.channelSelect(2)
        keithleyPSU.channelSelect(1)
        keithleyPSU.channelSelect(2)
        keithleyPSU.channelSelect(0)

#        response = keithleyPSU.query('*IDN?')
#        
#        print repr(response)
        
        #response = keithleyPSU.query('OUTPUT?')
        
        # keithleyPSU.channelEnable(state=True, channel=0)
        
        # keithleyPSU.channelCombine(keithleyPSU.chMode.OFF)
        
        # keithleyPSU.outputOn(True)
        # keithleyPSU.setVoltage(channel=1, voltage=10)
        # print(keithleyPSU.readVoltage(channel=1))
        # keithleyPSU.setCurrent(channel=1, current=1)
        # print(keithleyPSU.readSetCurrent(channel=1))
        
#        print repr(keithleyPSU.readDCvoltage(1))
        
        #print repr(lockin.query('CH1 6'))
        #print 'response: {}'.format(response)
        #print response
    