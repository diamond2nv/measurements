# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 14:13:53 2016

@author: Raphael Proux, Quantum Photonics Lab, Heriot-Watt University

Live + capture images from starlight camera QT

Uses direct USB handling

Last changes:
    2017-07-04, R. Proux: added support for horizontal and vertical flipping,
                          changed "import pylab as py" to "import pylab as pl",
                          corrected scale issue when changing display options
                              (by centralizing the scale in an object property)
                          added cross lines for marker
    2017-07-12, R. Proux: added amplitude, fwhm and saturating status display 
                          for easier focus
    2017-07-17, R. Proux: added centre of mass cross lines
"""

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QShortcut, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtMultimedia import QSound
from measurements.instruments.starlightRead import StarlightCCD
from UiStarlightCapture import Ui_starlightCapture

import datetime
import sys
import os.path, os, copy
import pylab as pl
from scipy.ndimage.measurements import center_of_mass
import threading
import time
from astropy.io import fits
import pyqtgraph as pg
#import logging
#logging.basicConfig(filename='example.log',level=logging.DEBUG)

# For working with python, pythonw and ipython
#import os
if sys.executable.endswith("pythonw.exe"):  # this allows pythonw not to quit immediately
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")

def histeq(im,nbr_bins=256):
    """
    This function equalises the histogram of im (numpy array), distributing
    the pixels accross nbr_bins bins.
    Returns the equalised image as a numpy array (same shape as input).
    Largely copied from https://stackoverflow.com/a/28520445  
        (author: Trilarion, 17/07/2017)
    """
    #get image histogram
    imhist, bins = pl.histogram(im.flatten(), nbr_bins, normed=True)
    cdf = imhist.cumsum() #cumulative distribution function
    cdf = 65535 * cdf / cdf[-1] #normalize
    
    #use linear interpolation of cdf to find new pixel values
    im2 = pl.interp(im.flatten(), bins[:-1], cdf)
    
    return im2.reshape(im.shape)

    
def findFWHM(vector, maxPos=None, amplitude=None):
    """ 
    Find FWHM of vector peak (width at value at maxPos - amplitude /2).
    If maxPos is None, will find maximum in vector.
    If amplitude is None, will calculate amplitude from maximum to minimum of vector.
    """
    if maxPos == None:
        maxPos = vector.argmax()
    if amplitude == None:
        maxVal = pl.amax(vector)
        minVal = pl.amin(vector)
        amplitude = float(maxVal - minVal)
        
    maxSign = pl.sign(vector[maxPos])
    for pos, val in enumerate(vector[maxPos:]):
        if pl.sign(val) != maxSign: 
            # we passed 0
            break
    halfAbove = pos - abs(vector[maxPos+pos]) / abs(vector[maxPos+pos] - vector[maxPos+pos-1])
    
    for pos, val in enumerate(vector[maxPos:0:-1]):
        if pl.sign(val) != maxSign: 
            # we passed 0
            break
    halfBelow = pos - abs(vector[maxPos-pos]) / abs(vector[maxPos-pos] - vector[maxPos-pos+1])
    
    FWHM = halfBelow + halfAbove
    
    return FWHM, maxPos, amplitude


def errorMessageWindow(parentWindow, winTitle, winText):
    """
    Displays a QT error message box, with title, text and OK button
    """
    msg = QMessageBox(parentWindow)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(winTitle)
    msg.setText(winText)
    msg.exec_()

    
class ExposureThread (threading.Thread):
    """
    Separate thread for CCD exposure handling.
    ccd should be the StarlightCCD object (see starlightRead.py).
    integrationTime is the integration time in seconds for this session.
    flags is a dictionnary of flags that will be passed to ccd.exposure().
        Typically, acquisition info like interlaced acquisition mode.
        See starlightRead.py
    """
    def __init__(self, ccd, integrationTime=1, **flags):
        threading.Thread.__init__(self)
        self._stopper = threading.Event()
        self.ccd = ccd
        self.integrationTime = integrationTime
        self.flags = flags
        
    def run(self):
        exposureFinished = False
        while not exposureFinished:
            if self.stopped():
                self.ccd.timeEnd = time.time()
            
            self.ccd.exposure(self.integrationTime, **self.flags)
            exposureFinished = self.ccd.exposureFinished
            
    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()

    
class StarlightCapture(QWidget):
    """
    Qt class for GUI handling.
    """
    def __init__(self, app):
        self.dialog = QWidget.__init__(self)
        self.app = app
        self.acquire = False
        self.plotMeas = False
        self.ilAcq = False
        self.ilDoubleExpo = False
        self.acquiring = False
        self.scale = (1,1)
        self.ccd = None
        self.meas = None
        
        # Set up the user interface from Designer.
        self.ui = Ui_starlightCapture()
        self.ui.setupUi(self)
        
        self.ui.stopBut.setEnabled(False)        
        
        # initialize gui variables
        self.exposureTime = self.ui.exposureTime.value()
        self.capture = self.ui.captureBox.isChecked()
        self.autolevels = self.ui.autolevelsBox.isChecked()
        self.equalizeHist = self.ui.eqHistBox.isChecked()
        self.horizFlip = self.ui.horizFlipCheckBox.isChecked()
        self.vertFlip = self.ui.vertFlipCheckBox.isChecked()
        self.crossLinesActive = self.ui.crossLinesCheckBox.isChecked()
        self.crossLinesMaxActive = self.ui.crossLinesMaxCheckBox.isChecked()
        self.fitsDir = self.ui.selectFileLineEdit.text()

        # Connect up the buttons.
        self.ui.startBut.clicked.connect(self.startAcq)
        self.ui.stopBut.clicked.connect(self.stopBut)
        #self.ui.exposureTime.setKeyboardTracking(False)
        self.ui.exposureTime.valueChanged.connect(self.exposureTimeChanged)
        self.ui.ilAcq.toggled.connect(self.ilAcqToggled)
        self.ui.ilDoubleExpo.toggled.connect(self.ilDoubleExpoToggled)
        self.ui.captureBox.toggled.connect(self.captureBoxChanged)
        self.ui.autolevelsBox.stateChanged.connect(self.autolevelsBoxChanged)
        self.ui.eqHistBox.stateChanged.connect(self.eqHistBoxChanged)
        self.ui.horizFlipCheckBox.stateChanged.connect(self.horizFlipCheckBoxChanged)
        self.ui.vertFlipCheckBox.stateChanged.connect(self.vertFlipCheckBoxChanged)
        self.ui.crossLinesCheckBox.stateChanged.connect(self.crossLinesCheckBoxChanged)
        self.ui.crossLinesMaxCheckBox.stateChanged.connect(self.crossLinesMaxCheckBoxChanged)
        self.ui.setCrossLinesToMaxButton.clicked.connect(self.setCrossLinesToMaxButtonPushed)
        self.ui.selectFileLineEdit.textChanged.connect(self.getSaveDir)
        self.ui.selectFileBut.clicked.connect(self.selectFile)
        
        self.ui.cameraID.valueChanged.connect(self.cameraIdChanged)
        
        # shortcut
        QShortcut(QKeySequence("Ctrl+Space"), self, self.acqShortcut)
        
        # sounds
        self.captureStopSound = QSound("captureStopSound.wav")
        self.captureStartSound = QSound("captureStartSound.wav")
        self.cameraIdChanged(0)
        
        
        maxPosPen = pg.mkPen({'width': 1, 'color': 'g'})
        
        self.verticalLine = pg.InfiniteLine(pos=50, movable=True)
        self.horizontalLine = pg.InfiniteLine(pos=50, angle=0, movable=True)
        self.verticalLineMax = pg.InfiniteLine(pos=(50,50), angle=45, pen=maxPosPen, movable=False)
        self.horizontalLineMax = pg.InfiniteLine(pos=(50,50), angle=135, pen=maxPosPen, movable=False)
        
        self.toggleSatIndicator(False)
        
    def startAcq(self):
        """
        Function called when pressing the Start button. Will launch the
        integration loop and stay going as long as no stopping action has 
        happened (pressing Stop button, closing the window, changed integration
        time).
        """
        self.ui.stopBut.setEnabled(True)
        self.ui.startBut.setEnabled(False)
        camId = self.ui.cameraID.value()
        
        try:
            with StarlightCCD(camId) as self.ccd:
                self.meas = pl.zeros((self.ccd.ccdParams['height'], self.ccd.ccdParams['width']))
                i = 0
                
                # flags for the event loop
                startThread = True     # needs to start a new acquisition
                self.plotMeas = False  # needs to plot the acquisition (acq finished)
                self.acquire = True    # CCD should be acquiring

                # wait for a loop to finish                
                while self.acquiring:
                    pass
                
                self.acquiring = True  # the event loop below is active
                
                # acquisition event loop
                while self.acquire:
                    if startThread:
                        ccdThread = ExposureThread(self.ccd, self.exposureTime, ilAcq=self.ilAcq, ilCorrDoubleExpo=self.ilDoubleExpo)
                        ccdThread.start()
                        startThread = False
                        if self.capture and self.exposureTime > 1:
                            self.captureStartSound.play()
                            #print 'start sound'
                    
                    if not ccdThread.is_alive():  # acquisition finished
                        self.plotMeas = True
                        startThread = True
                    
                    if self.plotMeas:
                        self.meas = ccdThread.ccd.pixels.transpose()
                        
                        if self.ccd.ccdParams['isInterlaced'] and not self.ilAcq: ##not self.ilAcq and 
                            self.scale = (1,2)
                        else:
                            self.scale = (1,1)
                        
                        # flip image according to user specification
                        #    note that due to pyqtgraph behaviour, the array 
                        #    columns are the rows in the displayed image
                        if self.horizFlip:
                            self.meas = pl.flipud(self.meas)
                        if self.vertFlip:
                            self.meas = pl.fliplr(self.meas)
                            
                        # plot image preview
                        self.plotImage(self.meas, autoLevels=self.autolevels, eqHist=self.equalizeHist, scale=self.scale)
                        
                        if self.capture:  
                            self.captureStopSound.play()
                            #print 'stop sound'
                            break  # will stop and record file in self.stop()
                        else:
                            self.plotMeas = False  # go for another acquisition
                            
                    if ccdThread.ccd.completionPercentage == 100 or i % 100 == 0:
                        self.ui.progressBar.setValue(ccdThread.ccd.completionPercentage)
                    self.displayStats()
                    # process events to catch a stop push and refresh image preview
                    self.app.processEvents()
                    
                    i = i + 1
                
                #self.ui.progressBar.setValue(0)
                ccdThread.stop()
                while ccdThread.is_alive():  # wait before closing device
                    pass
                self.acquiring = False
                
        except IndexError:
            self.ui.modelName.setText('No device')
            self.ccd = None
        finally:        
            self.stop(userStop=False)
        
    def plotImage(self, dispMeas, autoLevels=True, eqHist=False, scale=(1,1)):
        if self.equalizeHist:
            dispMeas = histeq(self.meas)
        else:
            dispMeas = self.meas
        
        self.ui.image.setImage(dispMeas, autoRange=False, autoLevels=autoLevels, levels=None, axes=None, xvals=None, pos=None, scale=scale, transform=None, autoHistogramRange=autoLevels)
        
        
    def stop(self, userStop=True):
        """
        This function will stop integration. Called when pressing the Stop
        button, closing the window or changing integration time.
        """
        self.acquire = False
        if not userStop and self.capture and self.plotMeas:
            if os.path.isdir(self.fitsDir):
                hdu = fits.PrimaryHDU(self.meas.transpose().astype(pl.uint16))
                #tbhdu = fits.BinTableHDU.from_columns([fits.Column(name='ccdCounts', format='I', array=meas)])
                d = datetime.datetime.now()
                fname = 'starlight_{}s_{:%Y-%m-%d_%H-%M-%S}'.format(self.exposureTime, d)
                if os.path.exists(fname):
                    i = 0
                    while os.path.exists(fname + '-{}'.format(i)):
                        i += 1
                    fname = fname + '-{}'.format(i)
                
                hdu.writeto(os.path.join(self.fitsDir, fname + '.fits'))
        
        self.ui.stopBut.setEnabled(False)
        self.ui.startBut.setEnabled(True)
        
    def stopBut(self, event):
        self.stop()        
        
    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def cameraIdChanged(self, event):
        try:
            with StarlightCCD(event) as ccd:
                self.ui.modelName.setText(ccd.ccdParams['cameraModel'])
                if ccd.ccdParams['isInterlaced']:
                    self.ui.ilAcq.setEnabled(True)
                    self.ui.ilDoubleExpo.setEnabled(True)
                else:
                    self.ui.ilAcq.setEnabled(False)
                    self.ui.ilDoubleExpo.setEnabled(False)
                if self.acquire:
                    self.stop()
                    
        except IndexError:
            self.ui.modelName.setText('No device')

        
    def exposureTimeChanged(self, event):
        if self.acquire:
            self.stop()
        self.exposureTime = event
        
         
    def captureBoxChanged(self, event):
        self.capture = self.ui.captureBox.isChecked()
        if self.capture and not os.path.isdir(self.fitsDir):
            errorMessageWindow(self, 'Directory does not exist', 'Please select a directory for capturing images.')
            self.ui.captureBox.setChecked(False)
            self.capture = False
    
    def ilAcqToggled(self, event):
        if event:
            self.ilAcq = True
            self.scale = (1, 1)
        else:
            self.ilAcq = False
            if self.ccd is not None and self.ccd.ccdParams['isInterlaced']:
                self.scale = (1,2)
            else:
                self.scale = (1,1)
            if self.ui.ilDoubleExpo.isChecked():
                self.ui.ilDoubleExpo.setChecked(False)
        
    def ilDoubleExpoToggled(self, event):
        if event:
            self.ilDoubleExpo = True
            if not self.ui.ilAcq.isChecked():
                self.ui.ilAcq.setChecked(True)
                
        else:
            self.ilDoubleExpo = False
        
    def autolevelsBoxChanged(self, event):
        self.autolevels = self.ui.autolevelsBox.isChecked()
        if hasattr(self, 'meas'):
            self.plotImage(self.meas, autoLevels=self.autolevels, eqHist=self.equalizeHist, scale=self.scale)
        
    def eqHistBoxChanged(self, event):
        self.equalizeHist = self.ui.eqHistBox.isChecked()
        if hasattr(self, 'meas'):
            self.plotImage(self.meas, autoLevels=self.autolevels, eqHist=self.equalizeHist, scale=self.scale)
        
    def horizFlipCheckBoxChanged(self, event):
        self.horizFlip = self.ui.horizFlipCheckBox.isChecked()
        if hasattr(self, 'meas'):
            self.plotImage(pl.flipud(self.meas), autoLevels=self.autolevels, eqHist=self.equalizeHist, scale=self.scale)
            
    def vertFlipCheckBoxChanged(self, event):
        self.vertFlip = self.ui.vertFlipCheckBox.isChecked()
        if hasattr(self, 'meas'):
            self.plotImage(pl.fliplr(self.meas), autoLevels=self.autolevels, eqHist=self.equalizeHist, scale=self.scale)
            
    def crossLinesCheckBoxChanged(self, event):
        self.crossLinesActive = self.ui.crossLinesCheckBox.isChecked()
        if self.crossLinesActive:
            self.ui.image.addItem(self.verticalLine)
            self.ui.image.addItem(self.horizontalLine)
        else:
            self.ui.image.removeItem(self.verticalLine)
            self.ui.image.removeItem(self.horizontalLine)
            
    def crossLinesMaxCheckBoxChanged(self, event):
        self.crossLinesMaxActive = self.ui.crossLinesMaxCheckBox.isChecked()
        if self.crossLinesMaxActive:
            self.ui.image.addItem(self.verticalLineMax)
            self.ui.image.addItem(self.horizontalLineMax)
        else:
            self.ui.image.removeItem(self.verticalLineMax)
            self.ui.image.removeItem(self.horizontalLineMax)
    
    def setCrossLinesToMaxButtonPushed(self):
        # logging.info('So should this {}'.format(self.verticalLine.value()))
        CoMpos = self.verticalLineMax.value()
        
        self.verticalLine.setValue(CoMpos)
        self.horizontalLine.setValue(CoMpos)
        
    def selectFile(self, event):
        self.ui.selectFileLineEdit.setText(QFileDialog.getExistingDirectory())
        
    def getSaveDir(self, event):
        self.fitsDir = str(self.ui.selectFileLineEdit.text())
        
    def acqShortcut(self):
        if not self.acquire:
            self.startAcq()
        else:
            self.stop()
    
    def displayStats(self):
        if self.meas is not None:
            maxPos = pl.unravel_index(self.meas.argmax(), self.meas.shape)
            maxVal = self.meas[maxPos]
            minVal = pl.amin(self.meas)
            amplitude = float(maxVal - minVal)
            self.ui.lcdAmplitude.display('{:.0f}'.format(amplitude))

            xVector = self.meas[maxPos[0],:].astype(float) - amplitude/2
            yVector = self.meas[:,maxPos[1]].astype(float) - amplitude/2
                               
            # with interlaced camera in binning mode, pixels are size 2 in height
            if self.ccd.ccdParams['isInterlaced'] and not self.ilAcq:
                yVector = pl.array([yVector, yVector]).flatten('F')
                maxPos = (2*maxPos[0], maxPos[1])

            xFWHM,_,_ = findFWHM(xVector, maxPos=maxPos[1], amplitude=amplitude)
            yFWHM,_,_ = findFWHM(yVector, maxPos=maxPos[0], amplitude=amplitude)
            FWHM = pl.mean([xFWHM, yFWHM])
            
            self.ui.lcdFwhm.display('{:.2f}'.format(FWHM))
            
            if maxVal == 2**16-1:
                self.toggleSatIndicator(True)
            else:
                self.toggleSatIndicator(False)
                
            thresholdArray = copy.deepcopy(self.meas)
            low_values_indices = thresholdArray < 2*minVal
            thresholdArray[low_values_indices] = 0
            comPos = center_of_mass(thresholdArray)#[::-1]
            if self.ccd.ccdParams['isInterlaced'] and not self.ilAcq:
                comPos = (comPos[0], 2*comPos[1])
            self.verticalLineMax.setValue(comPos)
            self.horizontalLineMax.setValue(comPos)
            
            
    def toggleSatIndicator(self, satActive):
        """ Switch on the SATURATING indicator. """
        if satActive:
            self.ui.satIndicator.setStyleSheet("background-color: rgb(255, 51, 0);\ncolor: rgb(255, 255, 255);")
        else:
            self.ui.satIndicator.setStyleSheet("background-color: rgb(255, 235, 230);\ncolor: rgb(255, 255, 255);")
    
if __name__ == "__main__":
        
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = StarlightCapture(app)
    
    window.show()
    app.exec_()