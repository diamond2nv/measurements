# -*- coding: utf-8 -*-
"""
Created on Mon May 15 12:39:47 2017

@author: QPL
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 14:24:17 2017

@author: QPL
"""

import ctypes
import time


class HydraHarpError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def listDev():
    """
    Prints a list of all devices.
    ATTENTION: do not use while a device is open (it will close it prematurely)
    """
    
    hhLib = HydraHarp.loadLib()
    
    print("\nSearching for HydraHarp devices...");
    print("\nDevID      Status");
    
    MAXDEVNUM = 8
    ERROR_DEVICE_OPEN_FAIL = -1
    dev = []
    HW_Serial = (ctypes.c_char * 8)()
    Errorstring = (ctypes.c_char * 40)()
    
    for i in range(MAXDEVNUM):
        
        retcode = hhLib.HH_OpenDevice(i, HW_Serial)
        if retcode == 0: # Grab any HydraHarp we can open
            print("  {}        S/N {}".format(i, HW_Serial.value))
            dev.append(i)  # keep index to devices we want to use
        else:
            if retcode == ERROR_DEVICE_OPEN_FAIL:
                print("  {}        no device".format(i))
            else:
                hhLib.HH_GetErrorString(Errorstring, retcode)
                print("  {}        {}".format(i, Errorstring.value))
        hhLib.HH_CloseDevice(i)
        
        
class HydraHarp():
    
    def __init__(self, dev_id=0):
        self.hhLib = self.loadLib()
        self.dev_id = dev_id
        
        ERROR_DEVICE_OPEN_FAIL = -1
        HW_Serial = (ctypes.c_char * 8)()
        Errorstring = (ctypes.c_char * 40)()
        
        retcode = self.hhLib.HH_OpenDevice(dev_id, HW_Serial)
        if retcode != 0:
            if retcode == ERROR_DEVICE_OPEN_FAIL:
                raise HydraHarpError("No device with ID {}".format(dev_id))
            else:
                self.hhLib.HH_GetErrorString(Errorstring, retcode)
                raise HydraHarpError("{}".format(Errorstring.value))
        
        self.hhLib.HH_Initialize(self.dev_id, 0, 0);  # 0,0 = histogramming mode, internal timing
        
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @staticmethod
    def loadLib():
        
        hhLib = ctypes.windll.LoadLibrary('hhLib')  # has to be installed first with PicoQuant installer
        hhLib.HH_OpenDevice.argtypes = [ctypes.c_int, ctypes.c_char_p]
        hhLib.HH_CloseDevice.argtypes = [ctypes.c_int]
        hhLib.HH_GetErrorString.argtypes = [ctypes.c_char_p, ctypes.c_int]
        hhLib.HH_GetSyncRate.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        hhLib.HH_GetCountRate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        hhLib.HH_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        
        return hhLib
    
        
    def getCountRates(self):
        rates = [ctypes.c_int(), ctypes.c_int()]
        self.hhLib.HH_GetSyncRate(self.dev_id, ctypes.byref(rates[0]))
        self.hhLib.HH_GetCountRate(self.dev_id, 0, ctypes.byref(rates[1]))
          
        return rates[0].value, rates[1].value
    
    def close(self):
        self.hhLib.HH_CloseDevice(self.dev_id)


        
if __name__ == '__main__':
    listDev()
    with HydraHarp() as ph:
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
#        hhLib.HH_Initialize (dev[0], 0);
#        
#        
#        try:
#            while True:
#                time.sleep(0.1)
#                hhLib.HH_GetCountRate(dev[0], 0, ctypes.byref(rates[0]))
#                hhLib.HH_GetCountRate(dev[0], 1, ctypes.byref(rates[1]))
#                print ' ', rates[0].value, '     ', rates[1].value
#        except KeyboardInterrupt:
#            pass
#        finally:
#            hhLib.HH_CloseDevice(dev[0])