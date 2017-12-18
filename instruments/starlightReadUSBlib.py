# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 14:34:49 2016

@author: Raphael Proux, Quantum Photonics Lab, Heriot-Watt University
"""

import pylab as pl
import usb.core
import usb.util
import struct
import time


def bytesToPx(data):
    return pl.array(struct.unpack(r'<{}H'.format(int(len(data)/2)), data))
   
class StarlightCCDs():
    
    def __init__(self):
        self.devices = []
        self.models = []
        for device in usb.core.find(idVendor=0x1278, find_all=True):
            self.devices.append(device)
            self.models.append(self.getCameraModel(device))
            
        if self.devices == []:
            raise IndexError('No Starlight Xpress device found.')
                
    def getCameraModel(self, dev):
        """
        Returns a string with the name of the camera.
        """
        modelIds = {0x507:'Lodestar', 
                    0x525:'Ultrastar'}
        
        if dev.idProduct in modelIds:
            return modelIds[dev.idProduct]
        else:
            return 'Unknown device'
    
   
class StarlightCamUSB(StarlightCCDs):
    
    # Commands (to be passed in cmd)
    GET_FIRMWARE_VERSION = 255
    ECHO                 = 0
    CLEAR_PIXELS         = 1
    READ_PIXELS_DELAYED  = 2
    READ_PIXELS          = 3
    SET_TIMER            = 4
    GET_TIMER            = 5
    RESET                = 6
    SET_CCD_PARMS        = 7
    GET_CCD_PARMS        = 8
    SET_STAR2K           = 9
    WRITE_SERIAL_PORT    = 10
    READ_SERIAL_PORT     = 11
    SET_SERIAL           = 12
    GET_SERIAL           = 13
    CAMERA_MODEL         = 14
    LOAD_EEPROM          = 15
    
    # Flags (to be passed in cmdValue)
    CCD_FLAGS_FIELD_ODD     = 1
    CCD_FLAGS_FIELD_EVEN    = 2
    CCD_FLAGS_NOBIN_ACCUM   = 4
    CCD_FLAGS_NOWIPE_FRAME  = 8
    CCD_FLAGS_TDI           = 32
    CCD_FLAGS_NOCLEAR_FRAME = 64
        
    def __init__(self, camId=0):
        StarlightCCDs.__init__(self)
        
        self.dev = self.devices[camId]
        self.dev.set_configuration()
        
        # Reset camera before use
        self.write(self.RESET)
        
        # get CCD properties
        self.ccdProperties = self.getCcdProperties()
        self.ccdProperties['downloadDelay'] = self.measureDownloadDelay()
            
        #self.getCameraModel = self.getCameraModel(self.dev)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()    
    
   
    def getInterlaced(self):
        """
        Determines if the camera is interlaced (which will necessitate separate
        download of the even and odd lines).
        """
        if 'Lodestar' in self.getCameraModel(self.dev):
            return True
        else:
            return False
            
    def getCcdProperties(self):
        """
        Returns the ccd dictionary with data like CCD size, isInterlaced, etc.
        """
        self.write(self.GET_CCD_PARMS)
        data = self.read(17)
        
        ccd = {'width': struct.unpack('<h', data[2:4])[0],
               'height': struct.unpack('<h', data[6:8])[0],
               'pxwidth': float(struct.unpack('<h', data[8:10])[0])/256.,
               'pxheight': float(struct.unpack('<h', data[10:12])[0])/256.,
               'bitsperpx': data[14],
               'isInterlaced': self.getInterlaced(),
               'cameraModel': self.getCameraModel(self.dev)
               }
               
        return ccd
        
        
    def measureDownloadDelay(self, **readCcdParams):
        """
        Measures the time to download a frame defined by the readCcdParams 
        which are directly transfered to readCcd().
        (see readCcd() docstring for more information).
        """
        timerStart = time.time()
        
        self.readCcd(**readCcdParams)
        elapsedTime = time.time() - timerStart
        
        return elapsedTime
        
    
    def write(self, cmd=GET_FIRMWARE_VERSION, cmdType=0x40, cmdValue=0x0000, cmdIndex=0x0000, parameters=[]):
        """
        Writes a command to the camera.
        
        cmd and cmdValue should be among the constants defined above.
        cmdIndex should remain at 0
        
        By default, issues a request for GET_FIRMWARE_VERSION.
        
        See camera USB documentation for details on the commands.
        """
        if parameters is None:
            parameters = []
            
        cmdLength = len(parameters)        
        
        arrayToWrite = struct.pack('<BBHHH{}B'.format(len(parameters)), cmdType, cmd, cmdValue, cmdIndex, cmdLength, *parameters)

        return self.dev.write(0x1, arrayToWrite)
        
    def read(self, nbOfBytes=4):
        """
        Reads data from the camera.
        By default reads 4 bytes (corresponds to the GET_FIRMWARE_VERSION test from write()).
        """
        return self.dev.read(0x82, nbOfBytes, timeout=5000)
    
    def detLinesFlag(self, noWipe=False, bothRows=True, oddRows=True):
        """
        Returns the flag to send to the CCD, depending on the parameters:
        - If noWipe == False:
            - if bothRows == False and oddRows == True, only the oddRows are wiped,
            - if bothRows == False and oddRows == False, only the even rows are wiped,
            - if bothRows == True, the command ignores oddRows and wipes the whole CCD.
        - If noWipe == True, it means we just want to clear the registers. In this
                case the other parameters are ignored.

        NoWipe is used only for clearCcd().
        
        These parameters are ignored if the CCD is not interlaced (Ultrastar).
        In this case the returned value is 0 (no flag).
        """
        if noWipe:
            flag = self.CCD_FLAGS_NOWIPE_FRAME
        else:
            if self.ccdProperties['isInterlaced'] == False:
                flag = 0
            else:
                if bothRows:
                    flag = self.CCD_FLAGS_FIELD_ODD|self.CCD_FLAGS_FIELD_EVEN
                else:
                    if oddRows:
                        flag = self.CCD_FLAGS_FIELD_ODD
                    else:
                        flag = self.CCD_FLAGS_FIELD_EVEN
                    
        return flag
    
    def clearCcd(self, **flags):
        """
        Wipes out the CCD according to the line parameter flags (cf. detLinesFlag() method).
        """
        
        return self.write(self.CLEAR_PIXELS,
                          cmdValue=self.detLinesFlag(**flags))
        
    def readCcd(self, xOffset=0, yOffset=0, width=-1, 
                    height=-1, xBin=1, yBin=1, delay=0, **flags):
        """
        Reads the CCD at xOffset, yOffset with specified width and height, and bins.
        
        Positions and size on the CCD are in number of pixels.
        Delay is in seconds.

        If the delay is longer than 0, it will delay the download (up to 1 s),
        if the delay is 0, it will download the pixels immediately.

        For the flags parameters, see detLinesFlag() method.

        Width or height == -1 means full width/height.
        """
        
        if width == -1:
            width = self.ccdProperties['width']
        if height == -1:
            height = self.ccdProperties['height']
            
        if delay == 0:
            parameters = struct.pack('<HHHHBB', xOffset, yOffset, width, height, 
                                                 xBin, yBin)
            parameters = struct.unpack('<{}B'.format(len(parameters)), parameters)
            
            self.write(self.READ_PIXELS, 
                       cmdValue=self.detLinesFlag(**flags), 
                       parameters=parameters)
        else:
            delayInMs = int(1000 * delay)
            parameters = struct.pack('<HHHHBBI', xOffset, yOffset, width, height, 
                                                 xBin, yBin, delayInMs)
            parameters = struct.unpack('<{}B'.format(len(parameters)), parameters)
            
            self.write(self.READ_PIXELS_DELAYED, 
                       cmdValue=self.detLinesFlag(**flags), 
                       parameters=parameters)
        data = self.read(2 * width * height)  # factor 2 because one pixel = one short integer (2 bytes)
        
        return data
        
        
    def close(self):
        self.dev.reset()

if __name__ == "__main__":
    with StarlightCamUSB(0) as test:
        
        print('Camera model:', test.ccdProperties['cameraModel'])
        test.write()
        print('Firmware version:', struct.unpack('<HH', test.read()))
        print('Download time:', test.ccdProperties['downloadDelay'])
        
        print(test.detLinesFlag())
        print(test.detLinesFlag(bothRows=False))
        print(test.detLinesFlag(bothRows=False, oddRows=False))
        print(test.detLinesFlag(noWipe=True))
        
        test.clearCcd()
        data = test.readCcd(delay=0.1)
        print(type(data))
#        pixels = pl.empty(test.ccdProperties['height'] * test.ccdProperties['width'])
#        for i, (lowB, highB) in enumerate(zip(data[::2],data[1::2])):
#            pixels[i] = struct.unpack('<H', bytearray([lowB,highB]))[0]
        print(len(data))
        print(data[0:100])
        pixels = bytesToPx(data).reshape(test.ccdProperties['height'], test.ccdProperties['width'])
        
        res = pixels
        print(res.max())
        #time.sleep(.3)
        pl.figure()    
        pl.imshow(res)
        pl.colorbar()
        pl.show()        
        
        #print test.ccdProperties['downloadDelay']
#        # RESET
#        test.dev.write(0x1, bytearray([64,6,0,0,0,0,0,0]))
#
#        # ECHO test
#        print '\n---- ECHO test ----'
#        test.dev.write(0x1, bytearray([64,0,0,0,0,0,4,0, 1,2,3,4]))
#        data = test.dev.read(0x82, 4)
#        print data
#        
#        # GET_CCD_PARMS
#        print '\n---- GET_CCD_PARMS ---'
#        test.dev.write(0x1, bytearray([64,8,0,0,0,0,0,0]))
#        data = test.dev.read(0x82, 17)
#        print data
#        ccd = {'width': struct.unpack('<h', data[2:4])[0],
#               'height': struct.unpack('<h', data[6:8])[0],
#               'pxwidth': float(struct.unpack('<h', data[8:10])[0])/256.,
#               'pxheight': float(struct.unpack('<h', data[10:12])[0])/256.,
#               'bitsperpx': data[14]}
#        resStr = 'Width: {} pixels\n'.format(ccd['width'])\
#                +'Height: {} pixels\n'.format(ccd['height'])\
#                +'Pixel width: {} microns\n'.format(ccd['pxwidth'])\
#                +'Pixel height: {} microns\n'.format(ccd['pxheight'])\
#                +'Bits per pixel: {}\n'.format(ccd['bitsperpx'])
#        
#        print resStr
#        
#        # CLEAR_PIXELS and READ_PIXELS_DELAYED
#        print '\n---- CLEAR_PIXELS and READ_PIXELS_DELAYED ---'
#        # clear pixels
#        test.dev.write(0x1, bytearray([64,1,3,0,0,0,0,0]))
#        # read pixels delayed
#        ccdWidthBytes = bytearray(struct.pack('<h', ccd['width']))
#        ccdHeightBytes = bytearray(struct.pack('<h', ccd['height']))
#        delayBytes = bytearray(struct.pack('<i', 100))
#        test.dev.write(0x1, bytearray([64,2,1,0,0,0,14,0, 0,0,0,0,ccdWidthBytes[0],ccdWidthBytes[1],ccdHeightBytes[0],ccdHeightBytes[1],1,1,delayBytes[0],delayBytes[1],delayBytes[2],delayBytes[3]]))
#        # get times
##        while True:
##            time.sleep(0.2)
##            print 'read timer'
##            test.dev.write(0x1, bytearray([64,5,1,0,0,0,0,0]))
##            data = test.dev.read(0x82, 4)
##            timerVal = struct.unpack('<i', data)[0]
##            print timerVal
##            if timerVal <= 300:
##                break
##        # read serial
##        time.sleep(.4)
#        
#        data = test.dev.read(0x82, ccd['width'] * ccd['height'] * 2)
#        
#        timerStart = time.time()
#        test.dev.write(0x1, bytearray([64,1,3,0,0,0,0,0]))
#        test.dev.write(0x1, bytearray([64,2,2,0,0,0,14,0, 0,0,0,0,ccdWidthBytes[0],ccdWidthBytes[1],ccdHeightBytes[0],ccdHeightBytes[1],1,1,delayBytes[0],delayBytes[1],delayBytes[2],delayBytes[3]]))
#        data2 = test.dev.read(0x82, ccd['width'] * ccd['height'] * 2)
#        elapsedTime = time.time() - timerStart
#        print 'Elapsed time:', elapsedTime,'s'
#        print len(data)
##        test.dev.write(0x1, bytearray([64,3,2,0,0,0,14,0, 0,0,0,0,ccdWidthBytes[0],ccdWidthBytes[1],ccdHeightBytes[0],ccdHeightBytes[1],1,1]))
##        data2 = test.dev.read(0x82, ccd['width'] * ccd['height'] * 2)
#        
#        pixels1 = []
#        for lowB, highB in zip(data[::2],data[1::2]):
#            pixels1.append(struct.unpack('<H', bytearray([lowB,highB]))[0])
#        
#        pixels1 = pl.array(pixels1).reshape(ccd['height'], ccd['width'])
#        
#        pixels2 = []
#        for lowB, highB in zip(data2[::2],data2[1::2]):
#            pixels2.append(struct.unpack('<H', bytearray([lowB,highB]))[0])
#        
#        pixels2 = pl.array(pixels2).reshape(ccd['height'], ccd['width'])
#        
#        pixels = pl.empty((pixels1.shape[0] + pixels2.shape[0], pixels1.shape[1]), dtype=pixels1.dtype)
#        
#        pixels[0::2] = pixels1
#        pixels[1::2] = pixels2
#        
#        #pixels = pixels1        
#        
#        print 'Max value:',pixels.max()
#        print 'Mean value:',pl.mean(pixels)
#        #time.sleep(.3)
#             
#        
#        pl.figure()    
#        pl.imshow(pixels,cmap='gray')  #, aspect=580. / test.ccdParams.height)
#        pl.clim((None,1500))
#        pl.colorbar()
#        pl.show()
#            
##        while True:
##            time.sleep(0.1)
##            test.dev.write(0x1, bytearray([64,13,1,0,0,0,0,0]))
##            data = test.dev.read(0x82, 2)
##            amountOfData = struct.unpack('<h', data)[0]
##            print 'Amount of data:', amountOfData
#            
#        
#        
        