# -*- coding: utf-8 -*-
"""
@author: Raphael Proux
Last modified on 22/03/2018 by Raphael Proux


"""

from PyQt5.QtWidgets import QApplication, QWidget, QShortcut, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5 import QtCore
from measurements.programs.attoPosDC.UiattoPosDC import Ui_Dialog
from measurements.instruments.pylonWeetabixTrigger import voltOut
import sys
import time
import pylab as pl
import visa

class commandedVar():
    def __init__(self, initValue=False):
        self.x = initValue
        self.y = initValue
        self.z = initValue
        
    def __eq__(self, other):
        return (other == self.__nonzero__())
    
    def __nonzero__(self):
        return self.x or self.y or self.z
        
    def assign(self, value):
        self.x = value
        self.y = value
        self.z = value

class commandedVar2():
    def __init__(self, initValue=False):
        self.xUp   = initValue
        self.xDown = initValue
        self.yUp   = initValue
        self.yDown = initValue
        self.zUp   = initValue
        self.zDown = initValue
        
    def __eq__(self, other):
        return (other == self.__nonzero__())
    
    def __nonzero__(self):
        return self.xUp or self.xDown or self.yUp or self.yDown or self.zUp or self.zDown

    def assign(self, value):
        self.xUp   = value
        self.xDown = value
        self.yUp   = value
        self.yDown = value
        self.zUp   = value
        self.zDown = value
        
        
class keysRef():
    SxDown = QtCore.Qt.Key_Left
    SxUp   = QtCore.Qt.Key_Right
    SyDown = QtCore.Qt.Key_Down
    SyUp   = QtCore.Qt.Key_Up
    SzDown = QtCore.Qt.Key_PageDown
    SzUp   = QtCore.Qt.Key_PageUp

    close = QtCore.Qt.Key_Escape
    
    # ensembles of 
    scanners = {SxDown, SxUp, SyDown, SyUp, SzDown, SzUp}
    Sx = {SxDown, SxUp}
    Sy = {SyDown, SyUp}
    Sz = {SzDown, SzUp}

    
class AttoPosDC(QWidget):
    
    #==============================================================================
    #                    MAIN PARAMETERS FOR THE EXPERIMENT                       #
    #==============================================================================
        
    # these parameters are not meant to be changed on daily operation
    SMOOTH_DELAY = 0.005  # in s, delay between steps for smooth piezo movements
    SMOOTH_STEP = 1  # in V
    CONVERSION_FACTOR = 1./15
        
    #==============================================================================

    def __init__(self, app, config):
        self.dialog = super().__init__(self)
        self.app = app
        
        # Set up the user interface from Designer.
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        try:
            self.x_axis = voltOut(config['x_axis_channel'])
        except KeyError:
            self.x_axis = None
            self.ui.X.setEnabled(False)
        try:
            self.y_axis = voltOut(config['y_axis_channel'])
        except KeyError:
            self.y_axis = None
            self.ui.X.setEnabled(False)
        try:
            self.z_axis = voltOut(config['z_axis_channel'])
        except KeyError:
            self.z_axis = None
            self.ui.X.setEnabled(False)

        self.x_axis_to_init = True
        self.y_axis_to_init = True
        self.z_axis_to_init = True
        
        # state variables
        self.keyControl = True
        
        # shortcut
        self.keys = keysRef()
        
        # Connect up the buttons.
        self.ui.X.setKeyboardTracking(False)  # detects changes only after leaving the field or pressing enter
        self.ui.Y.setKeyboardTracking(False)
        self.ui.Z.setKeyboardTracking(False)
        self.ui.X.valueChanged.connect(self.SxPosChange)
        self.ui.Y.valueChanged.connect(self.SyPosChange)
        self.ui.Z.valueChanged.connect(self.SzPosChange)
        
        self.app.focusChanged.connect(self.focusOnWindow)
    
    def closeInstruments(self):
        """ close communication with instruments. """
        try:
            self.x_axis.StopTask()
        except:
            pass
        try:
            self.y_axis.StopTask()
        except:
            pass
        try:
            self.z_axis.StopTask()
        except:
            pass
    
    
    ######################
    # SCANNERS FUNCTIONS #
    ######################
        
    def _SxyzPosChange(self, event, axis, ui_element):
        """
        Function called when the user changes the value of the axis position.
        (called exclusively by the functions immediately below)
        Will give the orders and ensure a smooth movement to position.
        """
        currentVoltage = ui_element.value()
        smoothNbOfSteps = int(max((abs(pl.floor((event - currentVoltage) / float(self.SMOOTH_STEP))), 1)) + 1)
        smoothPositions = pl.linspace(currentVoltage, event, smoothNbOfSteps)
        for volts in smoothPositions:
            axis.write(volts * self.CONVERSION_FACTOR)
            time.sleep(self.SMOOTH_DELAY)

    # above function is called by the following 'callbacks'
    def SxPosChange(self, event):
        if self.x_axis_to_init:  # the first change is to set the initial position value.
            self.x_axis_to_init = False
        else:
            self._SxyzPosChange(event, self.x_axis, self.ui.X)
    def SyPosChange(self, event):
        if self.y_axis_to_init:  # the first change is to set the initial position value.
            self.y_axis_to_init = False
        else:
            self._SxyzPosChange(event, self.y_axis, self.ui.Y)
    def SzPosChange(self, event):
        if self.z_axis_to_init:  # the first change is to set the initial position value.
            self.z_axis_to_init = False
        else:
            self._SxyzPosChange(event, self.z_axis, self.ui.Z)
        
        
    def keyPressEvent(self, event):
        """ For keyboard navigation, called by Qt when a key press event happens. """
        
        if self.keyControl:  # check if keyboard control is on
            if event.key() == self.keys.close:          # close program
                self.close()
            elif event.key() == self.keys.SxDown:       # scanner X down
                singleStep = self.ui.X.singleStep()
                value = self.ui.X.value()
                self.ui.X.setValue(value - singleStep)
            elif event.key() == self.keys.SxUp:         # scanner X up
                singleStep = self.ui.X.singleStep()
                value = self.ui.X.value()
                self.ui.X.setValue(value + singleStep)
            elif event.key() == self.keys.SyDown:       # scanner Y down
                singleStep = self.ui.Y.singleStep()
                value = self.ui.Y.value()
                self.ui.Y.setValue(value - singleStep)
            elif event.key() == self.keys.SyUp:         # scanner Y up
                singleStep = self.ui.Y.singleStep()
                value = self.ui.Y.value()
                self.ui.Y.setValue(value + singleStep)
            elif event.key() == self.keys.SzDown:       # scanner Z down
                singleStep = self.ui.Z.singleStep()
                value = self.ui.Z.value()
                self.ui.Z.setValue(value - singleStep)
            elif event.key() == self.keys.SzUp:         # scanner Z up
                singleStep = self.ui.Z.singleStep()
                value = self.ui.Z.value()
                self.ui.Z.setValue(value + singleStep)
            
    def focusOnWindow(self, oldWidget, newWidget):
        """ Called when the focus changes from or to the app, and toggled the keyboard control accordingly. """
        if newWidget == self:  # switch on keyboard control
            self.keyControl = True
        elif oldWidget == self:  # switch off keyboard control
            self.keyControl = False

def attopos_dc_run(config):
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = AttoPosDC(app, config)
    
    try:
        window.setFocus(True)
        window.show()
        app.exec_()
    except:
        raise
    finally:
        window.closeInstruments()
        
if __name__ == "__main__":
    
    config = {"x_axis_channel": '/Weetabix/ao0', "y_axis_channel": '/Weetabix/ao1'}
    attopos_dc_run(config)
    