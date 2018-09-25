# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 14:00:22 2016

@author: Raphael Proux, Quantum Photonics Lab, Heriot-Watt University

Library to get images from a Starlight camera given an exposure time.

"""

import pylab as py
import time
from measurements.instruments.starlightReadUSBlib import *

        
class StarlightCCD(StarlightCamUSB):
    """
    Higher level class to call a specific Starlight Xpress identified by its
    number ccdId (see starlightReadUSBlib).
    To be used in other programs, overloads the lower level StarlightCamUSB and
    StarlightCCDs providing user-friendly exposure handling (integration time,
    interlacing) and thread integration.
    Once instantiated, the only function to call is self.exposure()
    """
    def __init__(self, ccdId=0):
        StarlightCamUSB.__init__(self, ccdId)
        
        self.ccdHandle = self.dev
        self.ccdParams = self.ccdProperties
        
        if self.ccdParams['isInterlaced']:
            self.pixels1 = py.empty(self.ccdParams['height'] * self.ccdParams['width'])
            self.pixels2 = py.empty(self.ccdParams['height'] * self.ccdParams['width'])
            self.pixels = py.empty((2 * self.ccdParams['height'], self.ccdParams['width']))
        else:
            self.pixels = py.empty(self.ccdParams['height'] * self.ccdParams['width'])
        self.mustStartAcq = True
        self.exposureFinished = False
        self.firstExposureFinished = False
        self.noMoreWipes = False
        self.timeStart = 0.
        self.timeEnd = 0.
        self.curTime = 0.
        
        self.completionPercentage = 0
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
        
    def _longExposure(self, exposureTime=2, **readFlags):
        """
        To handle long exposures (> 1 second) which need to be timed by the 
        computer.
        Is meant to be non-blocking: will execute and clear CCD, wait or
        recover integrated CCD depending on the integration stage. It needs
        to be called repeatedly until self.exposureFinished is True. The data
        is then available in self.dataBuffer.
        PLEASE NOTE: this function should not be called externally, it is 
        called internally by self.exposure().
        """
        
        if self.mustStartAcq:
            self.mustStartAcq = False
            self.clearCcd()
            
            timeStart = time.time()
            self.timeEnd = timeStart + exposureTime            
            timeCur = time.time()
            self.timeNextWipeReg = min((timeStart + 30, self.timeEnd - 4))
            
        else:
            timeCur = time.time()
            if timeCur < self.timeEnd:
                timeCur = time.time()
                if self.timeNextWipeReg < timeCur and not self.noMoreWipes:
                    self.clearCcd(noWipe=True)
                    self.timeNextWipeReg = min((timeCur + 30, self.timeEnd - 4))
                    if timeCur > self.timeEnd - 4:
                        self.noMoreWipes = True
                self.completionPercentage = 100 * (1 - (self.timeEnd - timeCur) / exposureTime)
                
            else:
                self.mustStartAcq = True
                self.exposureFinished = True
                self.noMoreWipes = False
                self.dataBuffer = self.readCcd(**readFlags)
        
           
    def exposure(self, exposureTime, ilAcq=False, ilCorrDoubleExpo=False):
        """
        Main CCD exposure function. It is meant to be used in a thread and
        called repeatedly, changing state when:
            - acquisition must start (first call only),
            - is undergoing, 
            - has finished (last call only).
        exposureTime is the exposure time (integration time for one image) in 
            seconds.
        ilAcq is a flag for basic interlaced acquisition.
            If True, the camera will read the odd rows first and then the even 
            rows. On short integration times, this will result in huge 
            distortion of the image since the read time becomes non 
            negligeable.
        ilCorrDoubleExpo is a flag for double integration interlaced 
            acquisition.
            If True, the camera will first perform a full integration reading 
            the odd rows, then clear the CCD and perform another full 
            integration and read the even rows. This cancels the distortion
            due to different reading times for odd and even rows, but is much
            slower.
        PLEASE NOTE: ilAcq must be True in order to activate ilCorrDoubleExpo
        """
        assert(exposureTime >= 0)
        
        # exposure finished before the last call of this function.
        self.exposureFinished = False
        
        if not self.ccdParams['isInterlaced']:
            ilAcq = False
        
        if not ilAcq:  # ilAcq must be True to allow double exposure
            ilCorrDoubleExpo = False
        
        # if exposureTime is smaller than 1 second, the function will block
        # execution for the time of the integration (up to 2 s in double expo
        # mode).
        if exposureTime < 1:  
            if self.mustStartAcq:
                if ilCorrDoubleExpo:  # double exposure, one reading for each
                    self.clearCcd()
                    self.data1 = self.readCcd(delay=exposureTime, bothRows=False, oddRows=True)   # read odd rows
                    self.clearCcd()
                    self.data2 = self.readCcd(delay=exposureTime, bothRows=False, oddRows=False)  # read even rows
                elif ilAcq:  # single exposure, two readings
                    self.clearCcd()
                    self.data1 = self.readCcd(delay=exposureTime, bothRows=False, oddRows=True)   # read odd rows
                    self.data2 = self.readCcd(bothRows=False, oddRows=False)                     # read even rows
                else:  # single exposure, single read (not interlaced mode)
                    self.clearCcd()
                    self.data = self.readCcd(delay=exposureTime)
    
                self.exposureFinished = True
                self.mustStartAcq = True
                self.completionPercentage = 100
        # integration times longer than 1 second need software timing.
        # The function will not block execution and will update the
        # self.exposureFinished flag when finished
        else:  
            if ilCorrDoubleExpo:  # double exposure, one reading for each
                if not self.exposureFinished and not self.firstExposureFinished:
                    self._longExposure(exposureTime, bothRows=False, oddRows=False)
                    if self.exposureFinished:
                        self.firstExposureFinished = True
                        self.exposureFinished = False
                        self.data1 = self.dataBuffer
                elif not self.exposureFinished:
                    self._longExposure(exposureTime, bothRows=False, oddRows=True)
                    if self.exposureFinished:
                        self.data2 = self.dataBuffer
                        
            elif ilAcq:  # single exposure, two readings
                if not self.exposureFinished:
                    self._longExposure(exposureTime, bothRows=False, oddRows=True)
                    if self.exposureFinished:
                        self.data1 = self.dataBuffer   # read odd rows
                        self.data2 = self.readCcd(bothRows=False, oddRows=False)  # read even rows
                
            else:  # single exposure, single read (not interlaced mode)
                if not self.exposureFinished:
                    self._longExposure(exposureTime)
                    if self.exposureFinished:
                        self.data = self.dataBuffer

        if self.exposureFinished:
            if not ilAcq:
                self.pixels = bytesToPx(self.data).reshape(self.ccdParams['height'], self.ccdParams['width'])
            else:
                
                self.pixels1 = bytesToPx(self.data1).reshape(self.ccdParams['height'], self.ccdParams['width'])
                self.pixels2 = bytesToPx(self.data2).reshape(self.ccdParams['height'], self.ccdParams['width'])
                self.pixels = py.empty((2 * self.ccdParams['height'], self.ccdParams['width']), dtype=py.ushort)
                  
                self.pixels[0::2] = self.pixels1  # physical odd rows (image even rows)
                self.pixels[1::2] = self.pixels2  # physical even rows (image odd rows)
                
                self.firstExposureFinished = False
            
            # This function does not return anything but the result is 
            # accessible as self.pixels, once the self.exposureFinished has
            # toggled to True
#            return self.pixels
         
        
if __name__ == "__main__":
    with StarlightCCD(0) as test:
        ilAcq = False
        ilCorrDoubleExpo = True
        exposureTime = 10
        
        while not test.exposureFinished:
            test.exposure(exposureTime, ilAcq=ilAcq, ilCorrDoubleExpo=ilCorrDoubleExpo)
             
        if not ilAcq and test.ccdParams['isInterlaced']:
            aspect = 2
        else:
            aspect = 1
        #print test.ccdParams.width,'*', test.ccdParams.height
        res = test.pixels
        print(res.max())
        #time.sleep(.3)
        py.figure()    
        py.imshow(res, aspect=aspect)
        py.colorbar()
        py.show()