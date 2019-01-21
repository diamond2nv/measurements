# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 14:24:17 2017

@author: QPL
"""

import ctypes
import time


class PicoHarpError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def listDev():
    """
    Prints a list of all devices.
    ATTENTION: do not use while a device is open (it will close it prematurely)
    """
    
    phLib = PicoHarp.loadLib()
    
    print("\nSearching for PicoHarp devices...");
    print("\nDevID      Status");
    
    MAXDEVNUM = 8
    ERROR_DEVICE_OPEN_FAIL = -1
    dev = []
    HW_Serial = (ctypes.c_char * 8)()
    Errorstring = (ctypes.c_char * 40)()
    
    for i in range(MAXDEVNUM):
        
        retcode = phLib.PH_OpenDevice(i, HW_Serial)
        if retcode == 0: # Grab any PicoHarp we can open
            print("  {}        S/N {}".format(i, HW_Serial.value))
            dev.append(i)  # keep index to devices we want to use
        else:
            if retcode == ERROR_DEVICE_OPEN_FAIL:
                print("  {}        no device".format(i))
            else:
                phLib.PH_GetErrorString(Errorstring, retcode)
                print("  {}        {}".format(i, Errorstring.value))
        phLib.PH_CloseDevice(i)
        
        
class PicoHarp():
    
    def __init__(self, dev_id=0):
        self.phLib = self.loadLib()
        self.dev_id = dev_id
        
        ERROR_DEVICE_OPEN_FAIL = -1
        HW_Serial = (ctypes.c_char * 8)()
        Errorstring = (ctypes.c_char * 40)()
        
        retcode = self.phLib.PH_OpenDevice(dev_id, HW_Serial)
        if retcode != 0:
            if retcode == ERROR_DEVICE_OPEN_FAIL:
                raise PicoHarpError("No device with ID {}".format(dev_id))
            else:
                self.phLib.PH_GetErrorString(Errorstring, retcode)
                raise PicoHarpError("{}".format(Errorstring.value))
        
        self.phLib.PH_Initialize(self.dev_id, 0);  # 0 = histogramming mode
        
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @staticmethod
    def loadLib():
        
        phLib = ctypes.windll.LoadLibrary('phlib64')  # has to be installed first with PicoQuant installer
        phLib.PH_OpenDevice.argtypes = [ctypes.c_int, ctypes.c_char_p]
        phLib.PH_CloseDevice.argtypes = [ctypes.c_int]
        phLib.PH_GetErrorString.argtypes = [ctypes.c_char_p, ctypes.c_int]
        phLib.PH_GetCountRate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        phLib.PH_Initialize.argtypes = [ctypes.c_int, ctypes.c_int]
        
        return phLib
    
        
    def getCountRates(self):
        rates = [ctypes.c_int(), ctypes.c_int()]
        self.phLib.PH_GetCountRate(self.dev_id, 0, ctypes.byref(rates[0]))
        self.phLib.PH_GetCountRate(self.dev_id, 1, ctypes.byref(rates[1]))  
        return rates[0].value, rates[1].value
    
    def close(self):
        self.phLib.PH_CloseDevice(self.dev_id)


        
if __name__ == '__main__':
    listDev()
    with PicoHarp() as ph:
        try:
            print('\nCounter 1   Counter 2')
            while True:
                time.sleep(0.1)
                rates = ph.getCountRates()
                print ' ', rates[0], '     ', rates[1]
        except KeyboardInterrupt:
            pass

#    if len(dev) > 0:
#        print('\nCounter 1   Counter 2')
#        phLib.PH_Initialize (dev[0], 0);
#        
#        
#        try:
#            while True:
#                time.sleep(0.1)
#                phLib.PH_GetCountRate(dev[0], 0, ctypes.byref(rates[0]))
#                phLib.PH_GetCountRate(dev[0], 1, ctypes.byref(rates[1]))
#                print ' ', rates[0].value, '     ', rates[1].value
#        except KeyboardInterrupt:
#            pass
#        finally:
#            phLib.PH_CloseDevice(dev[0])