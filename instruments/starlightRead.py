# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 14:00:22 2016

@author: Raphael
"""

import pylab as py
import ctypes, time

class t_sxccd_params(ctypes.Structure):
    _fields_ = [
        ("hfront_porch", ctypes.c_ushort),
        ("hback_porch", ctypes.c_ushort),
        ("width", ctypes.c_ushort),
        ("vfront_porch", ctypes.c_ushort),
        ("vback_porch", ctypes.c_ushort),
        ("height", ctypes.c_ushort),
        ("pix_width", ctypes.c_float),
        ("pix_height", ctypes.c_float),
        ("color_matrix", ctypes.c_ushort),
        ("bits_per_pixel", ctypes.c_byte),
        ("num_serial_ports", ctypes.c_byte),
        ("extra_caps", ctypes.c_byte),
        ("vclk_delay", ctypes.c_byte)]
        

class StarlightCCDs():
    
    MAX_NB_OF_CAMERAS = 20
    
    def __init__(self):
        self.ccdsHandle = (ctypes.wintypes.HANDLE * self.MAX_NB_OF_CAMERAS)()
        
        self.ccdLib = ctypes.cdll.LoadLibrary('SxUSB.dll')
        self.nbOfCcds = self.ccdLib.sxOpen(ctypes.byref(self.ccdsHandle))
        
        self.ccdsParams = (t_sxccd_params * self.MAX_NB_OF_CAMERAS)()
        self.ccdLib.sxGetCameraParams.argtypes = [ctypes.wintypes.HANDLE,
                                                  ctypes.c_ushort,
                                                  ctypes.POINTER(t_sxccd_params)]
                                                  
        self.ccdsFirmwareVersion = (ctypes.c_ulong * self.MAX_NB_OF_CAMERAS)()
        self.ccdsCameraModel = (ctypes.c_ushort * self.MAX_NB_OF_CAMERAS)()
        
        for i, handle in enumerate(self.ccdsHandle):
            if handle is not None:
                self.ccdLib.sxGetCameraParams(handle, 0, ctypes.byref(self.ccdsParams[i]))
                self.ccdsFirmwareVersion[i] = self.ccdLib.sxGetFirmwareVersion(handle)
                self.ccdsCameraModel[i] = self.ccdLib.sxGetCameraModel(handle)
            
        
        
        
class StarlightCCD(StarlightCCDs):
    def __init__(self, ccdId=0):
        StarlightCCDs.__init__(self)
        if ccdId >= self.nbOfCcds:
            raise ValueError('The camera ID number is higher than the number of detected cameras.')
        
        self.ccdHandle = self.ccdsHandle[ccdId]
        self.ccdParams = self.ccdsParams[ccdId]
        self.ccdFirmwareVersion = self.ccdsFirmwareVersion[ccdId]
        self.ccdCameraModel = self.ccdsCameraModel[ccdId]
        
        self.pixels = (ctypes.c_ushort * self.ccdParams.width * self.ccdParams.height)()
        self.ccdLib.sxExposePixels.argtypes = [ctypes.wintypes.HANDLE,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ushort,
                                               ctypes.c_ulong]
           
    def exposure(self, exposureTime):
        assert(exposureTime) > 0
        
        if exposureTime >= 1:
            
            self.ccdLib.sxClearPixels(self.ccdHandle, 0x00, 0)
            timeStart = time.time()
            timeEnd = timeStart + exposureTime
            
            while time.time() < timeEnd:
                pass
            
            self.ccdLib.sxLatchPixels(self.ccdHandle, 0x01 | 0x02, 0, 0, 0, self.ccdParams.width, self.ccdParams.height, 1, 1)
            self.ccdLib.sxReadPixels(self.ccdHandle, ctypes.byref(self.pixels), self.ccdParams.width * self.ccdParams.height)
        
        else:
            self.ccdLib.sxExposePixels(self.ccdHandle, 0x01 | 0x02, 0, 0, 0, self.ccdParams.width, self.ccdParams.height, 1, 1, ctypes.c_ulong(int(exposureTime * 1000)))
            
            timeStart = time.time()
            timeEnd = timeStart + exposureTime
            while time.time() < timeEnd:
                pass
                      
            self.ccdLib.sxReadPixels(self.ccdHandle, ctypes.byref(self.pixels), self.ccdParams.width * self.ccdParams.height)
        
        
if __name__ == "__main__":
    test = StarlightCCD(0)
    #while True:
    test.exposure(.01)
    #print test.ccdParams.width,'*', test.ccdParams.height
    res = py.array(test.pixels).reshape(test.ccdParams.height,test.ccdParams.width)
    print res.max()
    time.sleep(.3)
    py.figure()    
    py.imshow(res)#, aspect=580. / test.ccdParams.height)
    py.colorbar()
    py.show()