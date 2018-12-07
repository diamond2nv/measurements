
#python commands for LJ, you should download this from labjack.com
from measurement.hardware.Labjack.src import u3, LabJackPython 
import struct
import types
import logging
import numpy
import time
import os
import qt

class LabJackU3(Instrument):

    #####configuration of the LabJack
    DAC_reg = 5000 #for the communication to the "intrinsic" dac
    #sclPins = [0,2,4,5,6] # number of LJTDAC modules that are connected to the labjack are
                    # given by the number of elements and the address by the values
                    # connected to FIO0, FIO2, FIO4, FIO6
    EEPROM_ADDRESS = 0x50
    DAC_ADDRESS = 0x12

    def __init__(self, name=None, sclPins = [4,5]):

        self.id = name
        self._LJ = u3.U3()
        self.sclPins = sclPins
        #self._LJ.configIO(FIOAnalog=int('00000000',2)) #all FIO0-8 set to digital
        self.EEPROM_ADDRESS = 0x50
        self.DAC_ADDRESS = 0x12
        self.getCalConstants()

    def toDouble(self, buffer):
        """ 
        Name: toDouble(buffer)
        Args: buffer, an array with 8 bytes
        Desc: Converts the 8 byte array into a floating point number.
        """
        if type(buffer) == type(''):
            bufferStr = buffer[:8]
        else:
            bufferStr = ''.join(chr(x) for x in buffer[:8])
        dec, wh = struct.unpack('<Ii', bufferStr)
        return float(wh) + float(dec)/2**32

    def getCalConstants(self, verbose = False):
        """ 
        Name: getCalConstants()
        Desc: Loads or reloads the calibration constants for the LJTic-DAC
              modules and writes it in the module dictionary
        """
        for i,v in enumerate(self.sclPins):
            module = {}
            module['sclPin'] = v
            module['sdaPin'] = v+1
            ## getting calibration data from the LJTDAC
            data = self._LJ.i2c(self.EEPROM_ADDRESS, [64], 
                    NumI2CBytesToReceive=36, SDAPinNum = module['sdaPin'],
                    SCLPinNum = module['sclPin'])

            response = data['I2CBytes']
            module['aSlope'] = self.toDouble(response[0:8])
            module['aOffset'] = self.toDouble(response[8:16])
            module['bSlope'] = self.toDouble(response[16:24])
            module['bOffset'] = self.toDouble(response[24:32])

            if verbose:
                print ('SCL pin: ', v)
                print ('aSlope: ', module['aSlope'], 'aOffset: ', module['aOffset'])
                print ('bSlope: ', module['bSlope'], 'bOffset: ', module['bOffset'])

            self.dac_modules['LJTDAC'+str(i)] = module 

    def set_bipolar_dac(self, voltage, channel):
        module =  self.dac_modules['LJTDAC'+str(int(channel/2.0))]
        try:
            #print [48+channel%2, int(((voltage*module['aSlope'])+module['aOffset'])/256), 
                         #int(((voltage*module['aSlope'])+module['aOffset'])%256)]
            self._LJ.i2c(self.DAC_ADDRESS, 
                     [48+channel%2, int(((voltage*module['aSlope'])+module['aOffset'])/256), 
                         int(((voltage*module['aSlope'])+module['aOffset'])%256)], 
                     SDAPinNum = module['sdaPin'], 
                     SCLPinNum = module['sclPin'])
            self.bipolar_dac_values[channel]=voltage
            
        except:
            print "I2C Error! Something went wrong when setting the LJTickDAC. Is the device detached?"

    def get_bipolar_dac(self, channel):
        return self.bipolar_dac_values[channel]

    def set_dac(self, voltage, channel):
        self._LJ.writeRegister(self.DAC_reg+channel*2,voltage)
         
    def get_dac(self, channel):
        self._LJ.readRegister(self.DAC_reg+channel*2) 

