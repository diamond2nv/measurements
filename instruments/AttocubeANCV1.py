# -*- coding: utf-8 -*-
"""
Created on Tue Jul 05 16:08:51 2016

@author: ted and raphael

This library offers classes and functions to control remotely ANC300 and older ANC150 controllers (possibly others not tested).

!!!!   SUPERSEDES THE OLD AttocubeANC300.py LIBRARY   !!!!
"""
import visa
import re
import time
import warnings
import pylab as pl

class ANCError(Exception):

    """Error regarding anything with the ANC controller
    
    Attributes:
        value (str): error message
    """
    
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ANCaxis():

    """Class to handle one axis of an Attocube controller. 
    Should be provided a valid AttocubeANC() object (the controller where the axis is).
    
    Attributes:
        active (bool): True if axis is active. False otherwise.
        atto (AttocubeANC object): AttocubeANC() object handling the controller where the axis is.
        CAP (str): constant string identifying the capacitance measurement mode
        GROUND (str): constant string identifying the ground mode
        id (int): integer identifying the position of the axis in the controller
        INACTIVE (str): constant string identifying the inactive mode (no communication with the controller will be attempted)
        mode (str): string identifying the current mode of the axis
        OFFSET (str): constant string identifying the offset mode of the axis
        reversedStep (bool): if True, the axis will behave reversed (an up order will go down and reversewise)
        STEP (str): constant string identifying the step mode of the axis
        UNKNOWN (str): constant string identifying any unknown mode of the axis. In this mode, the axis will be inactive.
    """
    
    # mode keys
    INACTIVE = 'inactive'
    UNKNOWN = 'unknown'
    GROUND = 'ground'
    OFFSET = 'scan'
    CAP = 'capacitance'
    STEP = 'step'
    
    def __init__(self, axisId, ANChandle, reversedStep=False):
        """Sets basic properties and reads the mode from the axis if not INACTIVE.
        
        Args:
            axisId (int): integer identifying the position of the axis in the controller
            ANChandle (AttocubeANC object): AttocubeANC() object handling the controller where the axis is.
            reversedStep (bool, optional): if True, the axis will behave reversed (an up order will go down and reversewise)
        """
        self.id = axisId
        self.atto = ANChandle
        self.reversedStep = reversedStep
        if self.id == 0:
            self.active = False
            self.mode = self.INACTIVE
        else:
            self.active = True
            self.mode = self.getMode()
    
    def switchMode(self, newmode):
        """Change the axis mode to newmode
        
        Args:
            newmode (str): string identifying the mode of the axis (check mode keys at the beginning of the class).
        """
        if self.active:
            if newmode == self.GROUND:
                self.atto.groundMode(self.id)
            elif newmode == self.STEP:
                self.atto.stepMode(self.id)
            elif newmode == self.OFFSET:
                self.atto.scanMode(self.id)
            elif newmode == self.CAP:
                self.atto.capacitanceMode(self.id)
                
            self.mode = self.getMode()
                
    def getMode(self):
        """Reads the current mode of the axis
        
        Returns:
            str: string identifying the mode of the axis (check mode keys at the beginning of the class).
        """
        if self.active:
            modeStr = self.atto.getMode(self.id)[0]
            if modeStr == 'gnd':
                mode = self.GROUND
            elif modeStr in {'stp', 'stp+', 'stp-'}:
                mode = self.STEP
            elif modeStr == 'off':
                mode = self.OFFSET
            elif modeStr == 'cap':
                mode = self.CAP
            else:
                mode = self.UNKNOWN
            return mode
        else:
            return self.INACTIVE
        
    def stopMotion(self):
        """Stops all motion of the axis if set active.
        """
        if self.active:
            self.atto.stopMotion(self.id)
        
    def stepUp(self, nbOfSteps=-1):
        """In STEP mode, does nbOfSteps steps up.
        
        Args:
            nbOfSteps (int, optional): number of steps to make. If -1, will step continuously until stopped.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            if self.reversedStep:
                self.atto.stepDown(nbOfSteps, self.id)
            else:
                self.atto.stepUp(nbOfSteps, self.id)
                    
    def stepDown(self, nbOfSteps=-1):
        """In STEP mode, does nbOfSteps steps down.
        
        Args:
            nbOfSteps (int, optional): number of steps to make. If -1, will step continuously until stopped.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            if self.reversedStep:
                self.atto.stepUp(nbOfSteps, self.id)
            else:
                self.atto.stepDown(nbOfSteps, self.id)
            
    def setStepAmplitude(self, amplitude):
        """In STEP mode, sets the amplitude (in volts) of one step.
        
        Args:
            amplitude (float): new amplitude (in volts) to set.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            self.atto.setStepAmplitude(amplitude, self.id)
            
    def setStepFrequency(self, frequency):
        """In STEP mode, sets the frequency (in hertz) of the steps.
        
        Args:
            frequency (float): new frequency (in hertz) to set.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            self.atto.setStepFrequency(frequency, self.id)
            
    def getStepAmplitude(self):
        """In STEP mode, gets the amplitude (in volts) of one step.
        
        Returns:
            float: amplitude of one step (in volts). 0 if axis not in STEP mode.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            return self.atto.getStepAmplitude(self.id)[0]
        else:
            return 0.
            
    def getStepFrequency(self):
        """In STEP mode, gets the frequency (in hertz) of the steps.
        
        Returns:
            float: frequency (in hertz). 0 if axis not in STEP mode.
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            return self.atto.getStepFrequency(self.id)[0]
        else:
            return 0
            
    def setOffset(self, offset):
        """In OFFSET or STEP modes (ambiguous definition for old ANC200 controllers), 
        sets the offset in volts. A warning will be issued if the order is not accepted.
        
        Args:
            offset (float): offset (in volts) to set for this axis.
        """
        try:
            if self.mode in {self.OFFSET, self.STEP}:  # STEP for the old ANC200
                self.atto.setOffset(offset, self.id)
        except:
            warnings.warn('Axis {} may not have an OFFSET mode.'.format(self.id))
            
    def getOffset(self):
        """In OFFSET or STEP modes (ambiguous definition for old ANC200 controllers), 
        gets the offset in volts. A warning will be issued if the order is not accepted.
        
        Returns:
            float: current offset in volts. 0 if axis not in OFFSET or STEP mode or order not accepted.
        """
        try:
            if self.mode in {self.OFFSET, self.STEP}:  # STEP for the old ANC200
                retVal = self.atto.getOffset(self.id)[0]
            else:
                retVal = 0.
        except:
            warnings.warn('Axis {} may not have an OFFSET mode.'.format(self.id))
            return 0.
        else:
            return retVal
            
    def waitStep(self):
        """Wait for the axis to finish whatever it is doing (certainly stepping)
        """
        self.mode = self.getMode()
        if self.mode == self.STEP:
            self.atto.waitStep(self.id)

            

class AttocubeANC():
    def __init__(self, visaResourceId):
        rm = visa.ResourceManager()
        try:
            self.ANC = rm.open_resource(visaResourceId, baud_rate=38400) # baud rate important for ANC150
        except visa.VisaIOError as visaError:
            if int(visaError.error_code) == -1073807330:  # baud_rate not supported, try default (can happen with ANC300)
                try:
                    self.ANC = rm.open_resource(visaResourceId)
                    print(self.ANC)
                except:
                    raise
            else:
                raise
        self.isANC300 = self.determineANC300()
        self.lastOrderSent = 'NO ORDER'
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def determineANC300(self):
        lines = self.query('ver')
        for line in lines:
            if 'ANC300' in line:
                return True
        return False
    
    def query(self, msg):
        self.lastOrderSent = msg
        self.ANC.write(msg)
        lines = []
        line = ''
        while 'OK' not in line and 'ERROR' not in line:
            line = self.ANC.read()
            lines.append(line.rstrip())
        if 'ERROR' in line:
            raise ANCError('The ANC unit raised the following error: {}'.format(' '.join(lines)))
        return lines
        
        
    def groundMode(self, *axes):
        for i in axes:
            self.query('setm {} gnd'.format(i))
        
    def stepMode(self, *axes):
        for i in axes:
            self.query('setm {} stp'.format(i))
            
    def scanMode(self, *axes):
        for i in axes:
            if self.isANC300:
                self.query(r'setdci {} off'.format(i))
                self.query(r'setaci {} off'.format(i))
                self.query(r'setm {} off'.format(i))
            else:
                self.query(r'setm {} stp'.format(i))  # FOR ANC200 (old scanner controllers)
            
    def capacitanceMode(self, *axes):
        if self.isANC300:
            for i in axes:
                self.query(r'setm {} cap'.format(i))
        else:
            pass
            
    def getMode(self, *axes):
        mode = []
        for i in axes:
            try:
                retStr = self.query(r'getm {}'.format(i))[1]
                if retStr.startswith(r'mode = '):
                    retStr = retStr[7:]
                else:
                    retStr = 'unknown'
                mode.append(retStr)
            except:
                raise
        return mode
            
    def getCapacitance(self, *axes):
        """ Beware: axes will enter in capacitance measuring mode and stay. """
        cap = []
        for i in axes:
            try:
                self.query(r'setm {} cap'.format(i))
                if self.isANC300:
                    self.query(r'capw {}'.format(i))
                else: # ANC 150 (not tested)
                    time.sleep(2)
                cap.append(self.query(r'getc {}'.format(i))[1])
            except:
                return -1
        return cap
    
    def setStepAmplitude(self, amplitude, *axes):
        for i in axes:
            self.query('setv {} {}'.format(i, int(amplitude)))
            
    def setStepFrequency(self, frequency, *axes):
        for i in axes:
            self.query('setf {} {}'.format(i, int(frequency)))
            
    def setOffset(self, offset, *axes):
        for i in axes:
            if self.isANC300:
                echo = self.query(r'seta {} {:f}'.format(i, offset))
            else:
                offset = pl.uint16(float(offset)/150 * (2**16 - 1))
                self.toto = r'setv {} {}'.format(i, offset)
                echo = self.query(self.toto)    
        return echo
                       
    def getStepFrequency(self, *axes):
        freqs = []
        for i in axes:
            line = self.query(r'getf {}'.format(i))[1]
            value =re.findall(r"\d+", line)
            freqs.append(int(value[0]))
        return freqs
        
    def getStepAmplitude(self, *axes):
        amps = []
        for i in axes:
            line = self.query(r'getv {}'.format(i))[1]
            value =re.findall(r"[-+]?\d*\.\d+|\d+", line)
            amps.append(float(value[0]))
        return amps

    def getOffset(self, *axes):
        offset = []
        for i in axes:
            if self.isANC300:
                line = self.query(r'geta {}'.format(i))[1]
                value =re.findall(r"[-+]?\d*\.\d+|\d+", line)
                offset.append(float(value[0]))
            else:
                line = self.query(r'getv {}'.format(i))[1]
                value = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                offset.append(float(150. / (2**16 - 1) * int(value[0])))
        return offset
        
        
    def stepUp(self, nbOfSteps=-1, *axes):
        """ nbOfSteps is the number of steps. Set nbOfSteps to -1 to move continuously """
        for i in axes:
            if nbOfSteps == -1:
                self.query('stepu {} c'.format(i))
            else:
                self.query('stepu {} {}'.format(i, nbOfSteps))
    
    def stepDown(self, nbOfSteps=-1, *axes):
        """ nbOfSteps is the number of steps. Set nbOfSteps to -1 to move continuously """
        for i in axes:
            if nbOfSteps == -1:
                self.query('stepd {} c'.format(i))
            else:
                self.query('stepd {} {}'.format(i, nbOfSteps))
            
    def stopMotion(self, *axes):
        for i in axes:
            self.query('stop {}'.format(i))
            
    def waitStep(self, *axes):
        if self.isANC300:
            tempTimeout = self.ANC.timeout
            self.ANC.timeout = 100000
            
            for i in axes:
                self.query('stepw {}'.format(i))
            
            self.ANC.timeout = tempTimeout
        else:
            warnings.warn('The ANC controller used does not handle task-end wait. Please be careful when repeating orders.')
             
    def close(self):
        self.ANC.close()
        
if __name__ == '__main__':
    # if you want to use this you should update the functions names and parameters (it has changed)
    with AttocubeANC(r'ASRL11::INSTR') as ANC150:
        pass
#        logVar = ''
#        ANC150.scanMode(1)
#        with open('LOG.txt', 'w') as logFile:
#            for i in range(500000):
#                if i % 1000 == 0:
#                    print i, 'loops'
#                while True:
#                    try:
#                        echo = ANC150.setOffset(25,1)
#                        if echo[0] != u'> setv 1 10922':
#                            curOffset = ANC150.getOffset(1)
#                            tempLog = 'PROBLEM AT LOOP {}\n'.format(i) + \
#                                      'echo {}    offset {}\n'.format(echo[0], curOffset) + \
#                                      'Sent order was {}'.format(ANC150.lastOrderSent)
#                            print tempLog
#                            logFile.write(tempLog + '\n')
#                    except (visa.VisaIOError, ANCError) as error:
#                        tempLog = 'PROBLEM AT LOOP {}\n'.format(i) + \
#                                  str(error) + '\n' + \
#                                  'Sent order was {}\n'.format(ANC150.toto)
#                        print tempLog
#                        logFile.write(tempLog + '\n')
#                    else:
#                        break
        
#        
#        ANC150.scanMode(1)
#        for i in range(10000):
#            if i % 100 == 0:
#                print i, 'loops'
#            try:
#                ANC150.query('abcdefghijklmnopqrstuvwxyz')
#            except ANCError as error:
#                if str(error) != '\'The ANC unit raised the following error: > abcdefghijklmnopqrstuvwxyz ERROR\'':
#                    print error
                    