# -*- coding: utf-8 -*-
"""
Created on Fri May 27 15:40:28 2016.

@author: raphaelproux

Reads spatial 2D maps done using Lightfield and SPE3 files
Version 2 - 27/07/2016

NOTE: needs to have SPE3read.py 
"""


from PyQt4.QtGui import QApplication, QWidget, QFileDialog
from PyQt4.QtCore import QTimer
from UiRanges import Ui_ranges
import pylab as py
import matplotlib.colors

import json

from SPE3read import SPE3map, range_to_edge
from SPE2read import SPE2map
from smallFuncs2Dmap import *

# For working with python, pythonw and ipython
import sys, os
if sys.executable.endswith("pythonw.exe"):  # this allows pythonw not to quit immediately
    sys.stdout = open(os.devnull, "w");
    sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")
else:
    try:  # if under ipython, needs to choose external window for live updating figure
        from IPython import get_ipython
        ipython = get_ipython()
        ipython.magic("matplotlib qt")
    except:
        pass


class SpaceMapWindow(QWidget):
    """
    Main QDialog class with the measurement and plot properties form.
    Also generates the matplotlib windows for displaying data
    """
    
    def __init__(self, app):
        self.dialog = QWidget.__init__(self)
        self.app = app
        
        # Set up the user interface from Designer.
        self.ui = Ui_ranges()
        self.ui.setupUi(self)
        
        self.cmapList = [colormap for colormap in py.colormaps() if not colormap.endswith("_r")]
        self.ui.colorMap.addItems(self.cmapList)
        self.ui.colorMap.setCurrentIndex(60)
        
        # flags
        self.f_mapOpen  = False
        self.f_spOpen   = False
        self.f_fileOpen = False
        self.f_firstOpening = False
        self.f_cacheRecovered = False
        
        self.measParams = {}
        self.plotParams = {}
        self.plotSpPos = None
        self.spMapPos = None
        self.spVerticalBarCounter = 0
        self.spWaveLimits = []
        
        
        # Connect up the buttons.
        self.ui.squareMeas.toggled.connect(self.squareMeasClicked)
        self.ui.xMeasMin.valueChanged.connect(self.measRangeUpdate)
        self.ui.xMeasMax.valueChanged.connect(self.measRangeUpdate)
        self.ui.xMeasStep.valueChanged.connect(self.measRangeUpdate)
        self.ui.colorPlotFullscale.clicked.connect(self.colorPlotFullscale)
        self.ui.xPlotFullscale.clicked.connect(self.xPlotFullscale)
        self.ui.yPlotFullscale.clicked.connect(self.yPlotFullscale)
        self.ui.wavePlotFullscale.clicked.connect(self.wavePlotFullscale)
        self.ui.plotUpdate.clicked.connect(self.update)
        self.ui.selectFileButton.clicked.connect(self.selectFile)
        
        QTimer.singleShot(100, self.selectFile)  # select file at start
        
        
    def selectFile(self, event=0):
        """ 
        Generates the selection dialog window until cancelled or valid selected file.
        This function calls self.openFile() to open the file and validate it.
        """
        # ask for SPE file until valid file or user cancel
        while True:
            self.filename = str(QFileDialog.getOpenFileName(self, 'Open 2D map SPE file'))
            
            if self.filename == '':  # user cancelled
                break
            elif self.openFile(self.filename):  # open selected file
                self.ui.filePath.setText(self.filename)
                self.f_fileOpen = True
                if self.f_cacheRecovered:
                    self.update()
                break
            else: # not valid file, display an error box
                errorMessageWindow(self, "File is not valid", 
                                         "Failed to read the file.\nPlease specify an SPE3 file recorded with Lightfield.")
                
        
    def openFile(self, filename):
        """ 
        Opens data SPE3 file provided the filename from self.selectFile().
        Also opens if existing cache file
        """
        # read cache file if it is there
        try: 
            with open(cacheName(filename)) as infile:
                cacheData = json.load(infile)
        except IOError:
            self.f_cacheRecovered = False
            pass
        else:
            self.measParams = cacheData['measParams']
            self.plotParams = cacheData['plotParams']
            self.f_cacheRecovered = True
            
        # read the SPE3 file if possible
        try:
            try:
                self.data = SPE3map(self.filename)
            except:
                try:
                    self.data = SPE2map(self.filename)
                except:
                    raise
            self.f_firstOpening = True
            self.wavelength = self.data.wavelength
            self.wavelengthRangeMeas = (self.wavelength[0], self.wavelength[-1])
            self.nbOfFrames = self.data.nbOfFrames
            self.counts = py.array([dataRow[0] for dataRow in self.data.data])
            self.exposureTime = self.data.exposureTime  # exposure time in ms
        except:
            return False
        else:
            return True
        
    def update(self, event=0):
        
        # recover data and validate form
        if self.f_cacheRecovered and self.f_firstOpening:
            self.updateForm()
            validForm = self.recoverForm()
        else:
            validForm = self.recoverForm()
            
        self.updateForm()  # will sort the min/max if necessary
        if not(validForm):
            errorMessageWindow(self, "Form is not valid", 
                                     "Please check no min/max values are equal.")
                                     
            self.f_cacheRecovered = False
            return
        
        # save cache file with new information
        try: 
            cacheData = {'measParams': self.measParams, 'plotParams': self.plotParams}
            with open(cacheName(self.filename), 'wb') as outfile:
                json.dump(cacheData, outfile)
        except IOError:
            pass
        
        xNbOfSteps = int(py.floor(abs(self.measParams['xRange'][1] - self.measParams['xRange'][0]) / 
                        abs(self.measParams['xStep'])) + 1)
        yNbOfSteps = int(py.floor(abs(self.measParams['yRange'][1] - self.measParams['yRange'][0]) / 
                        abs(self.measParams['yStep'])) + 1)
        
        if xNbOfSteps * yNbOfSteps != self.nbOfFrames:
            errorMessageWindow(self, "Step issue", 
                                     "The calculated number of steps does not match the number of frames in the file.")
                                     
            self.f_cacheRecovered = False
            return
            
        
        self.xVoltage = py.linspace(min(self.measParams['xRange']), max(self.measParams['xRange']), xNbOfSteps)
        self.yVoltage = py.linspace(min(self.measParams['yRange']), max(self.measParams['yRange']), yNbOfSteps)
        
        self.processedCounts = self.calculateCountArray(xNbOfSteps, yNbOfSteps)
        
        if not self.f_cacheRecovered and self.f_firstOpening:
            self.colorPlotFullscale(onlySet=True)
            self.xPlotFullscale(onlySet=True)
            self.yPlotFullscale(onlySet=True)
            self.wavePlotFullscale(onlySet=True)
            self.recoverForm()
        
        self.f_firstOpening = False
        
        self.plotFigure(self.processedCounts, self.xVoltage, self.yVoltage)
        
        self.ui.plotUpdate.setText('Update')
        
        
    def recoverForm(self):
        try:
            self.measParams['xRange'] = sorted((self.ui.xMeasMin.value(), self.ui.xMeasMax.value()))
            self.measParams['xStep']  = self.ui.xMeasStep.value()
            self.measParams['yRange'] = sorted((self.ui.yMeasMin.value(), self.ui.yMeasMax.value()))
            self.measParams['yStep']  = self.ui.yMeasStep.value()
            
            self.plotParams['xRange'] = sorted((self.ui.xPlotMin.value(), self.ui.xPlotMax.value()))
            self.plotParams['yRange'] = sorted((self.ui.yPlotMin.value(), self.ui.yPlotMax.value()))
            self.plotParams['colorRange'] = sorted((self.ui.colorPlotMin.value(), self.ui.colorPlotMax.value()))
            self.plotParams['waveRange']  = sorted((self.ui.wavePlotMin.value(), self.ui.wavePlotMax.value()))
            self.plotParams['mode'] = self.ui.plotMode.currentIndex()
            self.plotParams['colorMap'] = self.ui.colorMap.currentIndex()
            self.plotParams['colorMapReversed'] = self.ui.colorMapReversed.isChecked()
            self.plotParams['keepAspRatio'] = self.ui.keepAspRatio.isChecked()
            self.plotParams['scale'] = self.ui.scaleMode.currentIndex()
                
            if not(increasingTuples([self.measParams['xRange'],
                                     self.measParams['yRange'],
                                     self.plotParams['xRange'],
                                     self.plotParams['yRange'],
                                     self.plotParams['colorRange'],
                                     self.plotParams['waveRange']])):
                raise ValueError

        except ValueError:
            raise
            return False
        else:
            return True
            
    def updateForm(self):
        self.ui.xMeasMin.setValue(self.measParams['xRange'][0])
        self.ui.xMeasMax.setValue(self.measParams['xRange'][1])
        self.ui.xMeasStep.setValue(self.measParams['xStep'])
        self.ui.yMeasMin.setValue(self.measParams['yRange'][0])
        self.ui.yMeasMax.setValue(self.measParams['yRange'][1])
        self.ui.yMeasStep.setValue(self.measParams['yStep'])
        
        self.ui.xPlotMin.setValue(self.plotParams['xRange'][0])
        self.ui.xPlotMax.setValue(self.plotParams['xRange'][1])
        self.ui.yPlotMin.setValue(self.plotParams['yRange'][0])
        self.ui.yPlotMax.setValue(self.plotParams['yRange'][1])
        self.ui.colorPlotMin.setValue(self.plotParams['colorRange'][0])
        self.ui.colorPlotMax.setValue(self.plotParams['colorRange'][1])
        self.ui.wavePlotMin.setValue(self.plotParams['waveRange'][0])
        self.ui.wavePlotMax.setValue(self.plotParams['waveRange'][1])
        
        self.ui.plotMode.setCurrentIndex(self.plotParams['mode'])
        self.ui.colorMap.setCurrentIndex(self.plotParams['colorMap'])
        self.ui.colorMapReversed.setChecked(self.plotParams['colorMapReversed'])
        self.ui.keepAspRatio.setChecked(self.plotParams['keepAspRatio'])
        self.ui.scaleMode.setCurrentIndex(self.plotParams['scale'])
            
            
    def squareMeasClicked(self, event):
        squareMeasurement = self.ui.squareMeas.isChecked()
        if squareMeasurement:  # box was checked
            self.measParams['xRange'] = (self.ui.xMeasMin.value(), self.ui.xMeasMax.value())
            self.measParams['xStep']  = float(self.ui.xMeasStep.text())

            self.ui.yMeasMin.setValue(self.measParams['xRange'][0])
            self.ui.yMeasMax.setValue(self.measParams['xRange'][1])
            self.ui.yMeasStep.setValue(self.measParams['xStep'])
            self.ui.yMeasMin.setEnabled(False)
            self.ui.yMeasMax.setEnabled(False)
            self.ui.yMeasStep.setEnabled(False)
                
        else:  # box was unchecked
            self.ui.yMeasMin.setEnabled(True)
            self.ui.yMeasMax.setEnabled(True)
            self.ui.yMeasStep.setEnabled(True)
            
    def measRangeUpdate(self, event=0):
        if self.ui.squareMeas.isChecked():
            self.ui.yMeasMin.setValue(self.ui.xMeasMin.text())
            self.ui.yMeasMax.setText(self.ui.xMeasMax.text())
            self.ui.yMeasStep.setText(self.ui.xMeasStep.text())
            
            
    def calculateCountArray(self, xNbOfSteps, yNbOfSteps):
        """
        Main function that calculates the data to display given the parameters
        """
        indexWaveRange = self.findWaveIndex(self.plotParams['waveRange'])
        
        if self.plotParams['mode'] == 0:
            countVector = py.sum(self.counts[:, int(indexWaveRange[0]):int(indexWaveRange[1]+1)], axis=1)
            resultCounts = countVector.reshape(yNbOfSteps, xNbOfSteps)
        else:
            countVector = self.counts[:, int(indexWaveRange[0]):int(indexWaveRange[1]+1)].max(axis=1)
            resultCounts = countVector.reshape(yNbOfSteps, xNbOfSteps)
        
        return resultCounts
        
    def findWaveIndex(self,waveRange):
        """
        Find the indices of each element of 2-tuple waveRange
        Returns the tuple of indices
        """
        foundMinIndex = False
        foundMaxIndex = False
        minIndex = 0
        for i, wave in enumerate(self.wavelength):
            if waveRange[0] is not None and wave >= waveRange[0] and not(foundMinIndex):
                foundMinIndex = True
                minIndex = i
            if waveRange[1] is not None and wave >= waveRange[1]:
                foundMaxIndex = True
                indexWaveRange = (minIndex, i)
                break
        if not(foundMaxIndex):
            indexWaveRange = (minIndex,len(self.wavelength))
            
        return indexWaveRange
        
        
        
    def plotFigure(self, counts, xVoltage, yVoltage):
        
        # if figure did not exist, let's create it
        if not self.f_mapOpen:
            self.fig = py.figure(figsize=(8.*4./3.*0.8,8.*0.8), dpi=100)
            self.mainAxes = self.fig.add_axes([0.1,0.1,0.7,0.8])
            self.colorBarAxes= self.fig.add_axes([0.82,0.1,0.03,0.8])
            self.f_mapOpen = True
        else:
            self.mainAxes.clear()  # fresh start for replotting
            self.colorBarAxes.clear()
            
        if self.plotParams['scale'] == 0:
            normFunc = matplotlib.colors.LogNorm
        else:
            normFunc = matplotlib.colors.Normalize
        
        
        cmapName = colorMapName(self.plotParams['colorMap'], self.plotParams['colorMapReversed'], self.cmapList)
        
        # draw the map
        self.pcf=self.mainAxes.pcolorfast(range_to_edge(xVoltage),
                                range_to_edge(yVoltage),
                                counts,
                                norm=normFunc(),
                                cmap=cmapName,
                                vmin=self.plotParams['colorRange'][0],
                                vmax=self.plotParams['colorRange'][1],
                                zorder=1)
                                
        # plot position of spectrum if displayed
        if self.f_spOpen:
            self.plotSpPos, = self.mainAxes.plot([self.spMapPos[0]], [self.spMapPos[1]], 'xb', markersize=20)
            
        self.mainAxes.set_title(os.path.basename(self.filename))
        self.mainAxes.get_xaxis().set_label_text('Voltage (V)')
        self.mainAxes.get_yaxis().set_label_text('Voltage (V)')
        self.mainAxes.get_xaxis().get_major_formatter().set_useOffset(False)
        self.mainAxes.get_yaxis().get_major_formatter().set_useOffset(False)
                                
        self.mainAxes.set_xlim(self.plotParams['xRange'])
        self.mainAxes.set_ylim(self.plotParams['yRange'])
        if self.plotParams['keepAspRatio']:
            self.mainAxes.set_aspect('equal')
        else:
            self.mainAxes.set_aspect('auto')
        
        self.fig.canvas.mpl_connect('draw_event', self.updateFormDraw)
        self.fig.canvas.mpl_connect('button_release_event', self.displaySpectrum)
        
        self.fig.canvas.mpl_connect('close_event', self.mapClose)
        
        self.fig.subplots_adjust(left=0.10, right=0.92) # before colorbar
              
        
        cb = self.fig.colorbar(mappable=self.pcf, cax=self.colorBarAxes)
        cb.set_label("Counts in {:.0f} ms".format(self.exposureTime))
        cb.ax.minorticks_on()
        
        self.fig.canvas.draw()
        self.fig.canvas.show()
        
           
        
    def displaySpectrum(self, event=0, moveX=0, moveY=0):
        
        if event == 0:
            xIndex = argNearest(self.xVoltage, self.spMapPos[0])
            if 0 <= xIndex + moveX < len(self.xVoltage):
                xIndex = xIndex + moveX
            yIndex = argNearest(self.yVoltage, self.spMapPos[1])
            if 0 <= yIndex + moveY < len(self.yVoltage):
                yIndex = yIndex + moveY
        else:
            xIndex = argNearest(self.xVoltage, event.xdata)
            yIndex = argNearest(self.yVoltage, event.ydata)
            
        countsIndex = yIndex * len(self.xVoltage) + xIndex
        self.spMapPos = (self.xVoltage[xIndex], self.yVoltage[yIndex])
        
        # if figure did not exist, let's create it
        if not self.f_spOpen:
            # update blue dot
            self.f_spOpen = True
            self.update()
            
            # create new figure for spectrum
            self.spFig = py.figure(figsize=(8.*4./3.*0.8,8.*0.4))
            self.spFigNumber = self.spFig.number
            self.spAxes = self.spFig.add_axes([0.1,0.16,0.85,0.74])
            
            # plot spectrum
            self.spPlot, = self.spAxes.plot(self.wavelength, self.counts[countsIndex])
            self.spAxes.set_title('Spectrum at X = {:.3f} V, Y = {:.3f} V'.format(self.spMapPos[0], self.spMapPos[1]))
            self.spAxes.get_xaxis().set_label_text('Wavelength (nm)')
            self.spAxes.get_yaxis().set_label_text("Counts in {:.0f} ms".format(self.exposureTime))
    
            # connect events for choosing wavelength range
            self.spFig.canvas.mpl_connect('button_release_event', self.mousSpectrumClick)
            self.spFig.canvas.mpl_connect('close_event', self.spectrumClose)
            self.fig.canvas.mpl_connect('key_press_event', self.keyboardChangeSpectrum)
            self.spFig.canvas.mpl_connect('key_press_event', self.keyboardChangeSpectrum)
            self.spFig.canvas.show() 
        else:
            # update blue dot
            self.update()
            
            # update spectrum
            self.spPlot.set_data(self.wavelength, self.counts[countsIndex])
            self.spAxes.set_title('Spectrum at X = {:.3f} V, Y = {:.3f} V'.format(self.spMapPos[0], self.spMapPos[1]))
            self.spAxes.relim()
            self.spAxes.autoscale_view(True,True,True)
            self.spFig.canvas.draw()
            self.spFig.canvas.show() 
           
        
    def keyboardChangeSpectrum(self, event):
        if event.key == 'right':
            self.displaySpectrum(moveX=1, moveY=0)
        elif event.key == 'left':
            self.displaySpectrum(moveX=-1, moveY=0)
        elif event.key == 'up':
            self.displaySpectrum(moveX=0, moveY=1)
        elif event.key == 'down':
            self.displaySpectrum(moveX=0, moveY=-1)
        
    def mousSpectrumClick(self, event):
        if event.button == 3: # right click
            if self.spVerticalBarCounter == 0 and len(self.spAxes.lines) > 2:
                self.spAxes.lines[-1].remove()
                self.spAxes.lines[-1].remove()
            elif self.spVerticalBarCounter == 1:
                self.spAxes.lines[-1].remove()
            
            self.spFig.canvas.draw()
            self.wavePlotFullscale()
            self.colorPlotFullscale()
            
        elif event.button == 1: # left click
            
            if self.spVerticalBarCounter == 0 and len(self.spAxes.lines) > 2:
                self.spAxes.lines[-1].remove()
                self.spAxes.lines[-1].remove()
                self.spWaveLimits = []
                
            plotVerticalBar(self.spAxes, event.xdata, 'r')
            self.spFig.canvas.draw()
            self.spWaveLimits.append(float(event.xdata))
            self.spVerticalBarCounter = (self.spVerticalBarCounter + 1) % 2
            
            if self.spVerticalBarCounter == 0:
                self.plotParams['waveRange'] = sorted(self.spWaveLimits)
                self.ui.wavePlotMin.setValue(self.plotParams['waveRange'][0])
                self.ui.wavePlotMax.setValue(self.plotParams['waveRange'][1])
                self.update()
                self.colorPlotFullscale()
        
    def mapClose(self, event):
        self.f_mapOpen = False
            
    def spectrumClose(self, event):
        self.f_spOpen = False
        if self.f_mapOpen:
            self.update()
         
        
    def updateFormDraw(self, event=0):
        """Updates Entry boxes after redrawing PL map"""
        self.plotParams['xRange'] = self.mainAxes.get_xlim()
        self.plotParams['yRange'] = self.mainAxes.get_ylim()
        self.ui.xPlotMin.setValue(self.plotParams['xRange'][0])
        self.ui.xPlotMax.setValue(self.plotParams['xRange'][1])
        self.ui.yPlotMin.setValue(self.plotParams['yRange'][0])
        self.ui.yPlotMax.setValue(self.plotParams['yRange'][1])
        
    
    def colorPlotFullscale(self, onlySet=False):
        try:
            self.ui.colorPlotMin.setValue(self.processedCounts.min())
            self.ui.colorPlotMax.setValue(self.processedCounts.max())
        
        finally:
            if not onlySet:
                self.update()
    
    def xPlotFullscale(self, onlySet=False):
        try:
            self.ui.xPlotMin.setValue(self.measParams['xRange'][0])
            self.ui.xPlotMax.setValue(self.measParams['xRange'][1])
        
        finally:
            if not onlySet:
                self.update()
    
    def yPlotFullscale(self, onlySet=False):
        try:
            self.ui.yPlotMin.setValue(self.measParams['yRange'][0])
            self.ui.yPlotMax.setValue(self.measParams['yRange'][1])
        
        finally:
            if not onlySet:
                self.update()
    
    def wavePlotFullscale(self, onlySet=False):
        try:
            self.ui.wavePlotMin.setValue(self.wavelengthRangeMeas[0])
            self.ui.wavePlotMax.setValue(self.wavelengthRangeMeas[1])
        
        finally:
            if not onlySet:
                self.update()
        
            

if __name__ == "__main__":
        
    # interactive mode for matplotlib
    py.ion()
        
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = SpaceMapWindow(app)
    
    window.show()
    app.exec_()


    
