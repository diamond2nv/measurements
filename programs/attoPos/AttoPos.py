# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 17:38:08 2016

@author: Raphael Proux
Last modified on 20/02/2017 by Raphael Proux

This program provides an easy to use interface for computer controlled operation
of the ANC300 axes (meant with 3 positioners and 3 scanners or less). It can also 
handle ANC150 controllers (with 3 positioners or less) and ANC200 (with 3 scanners
or less). Can be configured to use two different controllers for scanners and
positioners.

It provides control via USB and any serial interface. 
For scanners, the voltage can go from 0 to 150 V with adjustable steps. 
It ensures smooth movement of the scanner to position for any order in voltage.
For positioners, the frequency and voltage amplitude of the steps can be adjusted.
They can do single steps or a given number of steps for each click (up to 99),
and move continuously.

Complete keyboard control is possible (see in GUI)
"""

from PyQt5.QtWidgets import QApplication, QWidget, QShortcut, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5 import QtCore
from UiAttoPos import Ui_AttoPos
from measurements.instruments.AttocubeANCV1 import AttocubeANC, ANCaxis, ANCError
import sys
import time
import pylab as pl
import json
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
    
    PxDown = QtCore.Qt.Key_4
    PxUp   = QtCore.Qt.Key_6
    PyDown = QtCore.Qt.Key_5
    PyUp   = QtCore.Qt.Key_8
    PzDown = QtCore.Qt.Key_Plus
    PzUp   = QtCore.Qt.Key_Minus

    fullStop = QtCore.Qt.Key_0
    
    cont = QtCore.Qt.Key_Control
    contLock = QtCore.Qt.Key_Alt

    close = QtCore.Qt.Key_Escape
    
    # ensembles of 
    scanners = {SxDown, SxUp, SyDown, SyUp, SzDown, SzUp}
    Sx = {SxDown, SxUp}
    Sy = {SyDown, SyUp}
    Sz = {SzDown, SzUp}
    positioners = {PxDown, PxUp, PyDown, PyUp, PzDown, PzUp}
    Px = {PxDown, PxUp}
    Py = {PyDown, PyUp}
    Pz = {PzDown, PzUp}

    
class AttoPos(QWidget):
    
    #==============================================================================
    #                    MAIN PARAMETERS FOR THE EXPERIMENT                       #
    #==============================================================================
        
    # these parameters are not meant to be changed on daily operation
    SMOOTH_DELAY = 0.005  # in s, delay between steps for smooth piezo movements
    SMOOTH_STEP = 1  # in V
        
    #==============================================================================

    def __init__(self, app, config):
        self.dialog = QWidget.__init__(self)
        self.app = app
        
        # Set up the user interface from Designer.
        self.ui = Ui_AttoPos()
        self.ui.setupUi(self)
        
        # open configuration file
        try: 
            # initialize instruments
            self.initInstruments(visaPositionersId=config['attoVisaPositionersId'], 
                                 visaScannersId=config['attoVisaScannersId'],
                                 SxAxisId=config['attoAxes']['Sx'],
                                 SyAxisId=config['attoAxes']['Sy'],
                                 SzAxisId=config['attoAxes']['Sz'],
                                 PxAxisId=config['attoAxes']['Px'],
                                 PyAxisId=config['attoAxes']['Py'],
                                 PzAxisId=config['attoAxes']['Pz'],
                                 PxStepRev=config['reversedMotion']['Px'],
                                 PyStepRev=config['reversedMotion']['Py'],
                                 PzStepRev=config['reversedMotion']['Pz'])
            # not the reversed move of the scanners has to be handled by this 
            #   program and not the library
            self.SxStepRev = config['reversedMotion']['Sx']
            self.SyStepRev = config['reversedMotion']['Sy']
            self.SzStepRev = config['reversedMotion']['Sz']
        except (ValueError, KeyError):
            errorMessageWindow(self, 'Invalid config dictionary', 'The config dictionary in your script is invalid.\nPlease check documentation for a reference dictionary.')
            raise
        
        
        
        # deactivate GUI of inactive axes
        self.guiDeactivateAxes()
        
        # state variables
        self.SxPos = 0.
        self.SyPos = 0.
        self.SzPos = 0.
        self.SxGrounded = True
        self.SyGrounded = True
        self.SzGrounded = True
        self.SxDeactivated = False
        self.SxDeactivated = False
        self.SxDeactivated = False
        self.PxAmp = 0.
        self.PyAmp = 0.
        self.PzAmp = 0.
        self.PxFreq = 0
        self.PyFreq = 0
        self.PzFreq = 0
        self.PxOffset = 0.
        self.PyOffset = 0.
        self.PzOffset = 0.
        self.keyControl = self.ui.arrowKeyControl.isChecked()
        self.keyControlAutoSwitched = False
        self.keyControlSetByUser = False
        self.contStepMode = False
        self.contLockKeyPressed = False
        self.nbOfStepsToDo = 1
        self.contLockedStepMode = commandedVar()
        self.contActive = commandedVar2()
        self.stepActive = commandedVar2()
        
        SstepSize = self.ui.SstepSize.value()
        self.SstepSizeChange(SstepSize)
        
        # shortcut
        QShortcut(QKeySequence("Ctrl+Space"), self, self.toggleArrowKeyControlShortcut)
        self.keys = keysRef()
        
        # Connect up the buttons.
        self.ui.SxPos.setKeyboardTracking(False)  # detects changes only after leaving the field or pressing enter
        self.ui.SyPos.setKeyboardTracking(False)
        self.ui.SzPos.setKeyboardTracking(False)
        self.ui.SxPos.valueChanged.connect(self.SxPosChange)
        self.ui.SyPos.valueChanged.connect(self.SyPosChange)
        self.ui.SzPos.valueChanged.connect(self.SzPosChange)
        self.ui.SxDeactivate.toggled.connect(self.SxDeactivate)
        self.ui.SyDeactivate.toggled.connect(self.SyDeactivate)
        self.ui.SzDeactivate.toggled.connect(self.SzDeactivate)
        self.ui.SxGnd.toggled.connect(self.SxGndToggled)
        self.ui.SyGnd.toggled.connect(self.SyGndToggled)
        self.ui.SzGnd.toggled.connect(self.SzGndToggled)

        self.ui.SstepSize.valueChanged.connect(self.SstepSizeChange)
        self.ui.PxAmp.valueChanged.connect(self.PxAmpChange)
        self.ui.PyAmp.valueChanged.connect(self.PyAmpChange)
        self.ui.PzAmp.valueChanged.connect(self.PzAmpChange)
        self.ui.PxFreq.valueChanged.connect(self.PxFreqChange)
        self.ui.PyFreq.valueChanged.connect(self.PyFreqChange)
        self.ui.PzFreq.valueChanged.connect(self.PzFreqChange)
        self.ui.PxOffset.valueChanged.connect(self.PxOffsetChange)
        self.ui.PyOffset.valueChanged.connect(self.PyOffsetChange)
        self.ui.PzOffset.valueChanged.connect(self.PzOffsetChange)
        self.ui.PxGnd.toggled.connect(self.PxGndToggled)
        self.ui.PyGnd.toggled.connect(self.PyGndToggled)
        self.ui.PzGnd.toggled.connect(self.PzGndToggled)
        
        
        self.ui.arrowKeyControl.toggled.connect(self.arrowKeyControlToggled)
        self.app.focusChanged.connect(self.focusOnWindow)
        self.toggleContIndicator(self.contActive)
        
        # connect the positioners commands
        self.ui.PstepMultiplier.valueChanged.connect(self.PnbOfStepsUpdate)
        self.ui.PxStepUp.clicked.connect(self.PxStepUp)
        self.ui.PxStepDown.clicked.connect(self.PxStepDown)
        self.ui.PyStepUp.clicked.connect(self.PyStepUp)
        self.ui.PyStepDown.clicked.connect(self.PyStepDown)
        self.ui.PzStepUp.clicked.connect(self.PzStepUp)
        self.ui.PzStepDown.clicked.connect(self.PzStepDown)
        
        self.ui.PxContUp.pressed.connect(self.PxContUp)
        self.ui.PxContDown.pressed.connect(self.PxContDown)
        self.ui.PxContUp.released.connect(self.PxStop)
        self.ui.PxContDown.released.connect(self.PxStop)
        self.ui.PyContUp.pressed.connect(self.PyContUp)
        self.ui.PyContDown.pressed.connect(self.PyContDown)
        self.ui.PyContUp.released.connect(self.PyStop)
        self.ui.PyContDown.released.connect(self.PyStop)
        self.ui.PzContUp.pressed.connect(self.PzContUp)
        self.ui.PzContDown.pressed.connect(self.PzContDown)
        self.ui.PzContUp.released.connect(self.PzStop)
        self.ui.PzContDown.released.connect(self.PzStop)
        
    def initInstruments(self, visaPositionersId, visaScannersId, SxAxisId, SyAxisId, SzAxisId, PxAxisId, PyAxisId, PzAxisId, PxStepRev, PyStepRev, PzStepRev):
        """ 
        Creates the ANC and individual axes handles by connecting to the device 
        and updates the GUI with the real values.
        """
        # handle cases when the same controller handles both scanners and positioners,
        #    or when only one controller is used (for only positioners/only scanners)
        if visaPositionersId == visaScannersId:
            self.scannersAndPositionersOnSameDevice = True
        else:
            self.scannersAndPositionersOnSameDevice = False
            
        if SxAxisId == SyAxisId == SzAxisId == 0:  # scanners deactivated
            self.scannersAndPositionersOnSameDevice = True
            visaScannersId = visaPositionersId
        if PxAxisId == PyAxisId == PzAxisId == 0:  # positioners deactivated
            self.scannersAndPositionersOnSameDevice = True
            visaPositionersId = visaScannersId
            
        # Initialize intruments
        try:
            self.attoPositioners = AttocubeANC(visaResourceId=visaPositionersId)
            if visaPositionersId == visaScannersId:
                self.attoScanners = self.attoPositioners
                self.scannersAndPositionersOnSameDevice = True
            else:
                self.attoScanners = AttocubeANC(visaResourceId=visaScannersId)
                self.scannersAndPositionersOnSameDevice = False
                
        except visa.VisaIOError:
            errorMessageWindow(self, 'Problem connecting with the controller', 'The program could not connect with the Attocube controller.\nPlease check the address of the device in the CONFIG.txt file.')
            raise
        
        try:
            self.SxAxis = ANCaxis(SxAxisId, self.attoScanners)
            self.SyAxis = ANCaxis(SyAxisId, self.attoScanners)
            self.SzAxis = ANCaxis(SzAxisId, self.attoScanners)
            self.PxAxis = ANCaxis(PxAxisId, self.attoPositioners, PxStepRev)
            self.PyAxis = ANCaxis(PyAxisId, self.attoPositioners, PyStepRev)
            self.PzAxis = ANCaxis(PzAxisId, self.attoPositioners, PzStepRev)
            
            self.SxModeUpdate()
            self.SyModeUpdate()
            self.SzModeUpdate()
            self.SxPosUpdate()
            self.SyPosUpdate()
            self.SzPosUpdate()
            self.PxModeUpdate()
            self.PyModeUpdate()
            self.PzModeUpdate()
            self.PxAmpUpdate()
            self.PyAmpUpdate()
            self.PzAmpUpdate()
            self.PxFreqUpdate()
            self.PyFreqUpdate()
            self.PzFreqUpdate()
            self.PxOffsetUpdate()
            self.PyOffsetUpdate()
            self.PzOffsetUpdate()
            
        except ANCError as errormessage:
            errorMessageWindow(self, 'Error while initializing axes', str(errormessage))
            raise
    
    def closeInstruments(self):
        """ Stops all motion and releases the ANC. """
        self.PxAxis.stopMotion()
        self.PyAxis.stopMotion()
        self.PzAxis.stopMotion()
        if self.scannersAndPositionersOnSameDevice:
            self.attoScanners.close()
        else:
            try:
                self.attoScanners.close()
            except:
                raise
            finally:
                self.attoPositioners.close()
    
    
    ######################
    # SCANNERS FUNCTIONS #
    ######################
    
    def SstepSizeChange(self, event):
        """ Function called when the user changes the value of the step size. """        
        self.ui.SxPos.setSingleStep(event)
        self.ui.SyPos.setSingleStep(event)
        self.ui.SzPos.setSingleStep(event)
        
    def _SxyzPosChange(self, event, axis, updateFunc):
        """
        Function called when the user changes the value of the axis position.
        (called exclusively by the functions immediately below)
        Will give the orders and ensure a smooth movement to position.
        """
        currentVoltage = axis.getOffset()
        smoothNbOfSteps = int(max((abs(pl.floor((event - currentVoltage) / float(self.SMOOTH_STEP))), 1)) + 1)
        smoothPositions = pl.linspace(currentVoltage, event, smoothNbOfSteps)
        for volts in smoothPositions:
            axis.setOffset(volts)
            time.sleep(self.SMOOTH_DELAY)
        updateFunc()
    # above function is called by the following 'callbacks'
    def SxPosChange(self, event):
        self._SxyzPosChange(event, self.SxAxis, self.SxPosUpdate)
    def SyPosChange(self, event):
        self._SxyzPosChange(event, self.SyAxis, self.SyPosUpdate)
    def SzPosChange(self, event):
        self._SxyzPosChange(event, self.SzAxis, self.SzPosUpdate)
        
    def SxPosUpdate(self):
        """ Updates the field in GUI with the current real voltage of the axis. """
        self.SxPos = self.SxAxis.getOffset()
        self.ui.SxPos.setValue(self.SxPos)
        
    def SyPosUpdate(self):
        """ Updates the field in GUI with the current real voltage of the axis. """
        self.SyPos = self.SyAxis.getOffset()
        self.ui.SyPos.setValue(self.SyPos)
        
    def SzPosUpdate(self):
        """ Updates the field in GUI with the current real voltage of the axis. """
        self.SzPos = self.SzAxis.getOffset()
        self.ui.SzPos.setValue(self.SzPos)
        
    def SxModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.SxAxis.getMode()
        if currentMode in {self.SxAxis.STEP, self.SxAxis.OFFSET}:
            self.SxGrounded = False
        else:
            self.SxGrounded = True
        self.ui.SxGnd.setChecked(self.SxGrounded)
        self.updateUIWhenGnd(self.SxAxis, self.SxGrounded)
    
    def SyModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.SyAxis.getMode()
        if currentMode in {self.SyAxis.STEP, self.SyAxis.OFFSET}:
            self.SyGrounded = False
        else:
            self.SyGrounded = True
        self.ui.SyGnd.setChecked(self.SyGrounded)
        self.updateUIWhenGnd(self.SyAxis, self.SyGrounded)
        
    def SzModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.SzAxis.getMode()
        if currentMode in {self.SzAxis.STEP, self.SzAxis.OFFSET}:
            self.SzGrounded = False
        else:
            self.SzGrounded = True
        self.ui.SzGnd.setChecked(self.SzGrounded)
        self.updateUIWhenGnd(self.SzAxis, self.SzGrounded)
        
    def SxDeactivate(self, event):
        """ Disables the relevant fields to prevent user modification of the position of the axis.
        This means it will gray out the GND and position fields. """
        
        if self.SxAxis.getMode() != self.SxAxis.INACTIVE:
            if event:  # axis should be deactivated
                self.ui.SxPos.setDisabled(True)
                self.ui.SxGnd.setDisabled(True)
                self.SxDeactivated = True
            else:
                self.ui.SxPos.setDisabled(False)
                self.ui.SxGnd.setDisabled(False)
                self.SxDeactivated = False
    def SyDeactivate(self, event):
        """ Disables the relevant fields to prevent user modification of the position of the axis.
        This means it will gray out the GND and position fields. """
        
        if self.SyAxis.getMode() != self.SyAxis.INACTIVE:
            if event:  # axis should be deactivated
                self.ui.SyPos.setDisabled(True)
                self.ui.SyGnd.setDisabled(True)
                self.SyDeactivated = True
            else:
                self.ui.SyPos.setDisabled(False)
                self.ui.SyGnd.setDisabled(False)
                self.SyDeactivated = False
    def SzDeactivate(self, event):
        """ Disables the relevant fields to prevent user modification of the position of the axis.
        This means it will gray out the GND and position fields. """
        
        if self.SzAxis.getMode() != self.SzAxis.INACTIVE:
            if event:  # axis should be deactivated
                self.ui.SzPos.setDisabled(True)
                self.ui.SzGnd.setDisabled(True)
                self.SzDeactivated = True
            else:
                self.ui.SzPos.setDisabled(False)
                self.ui.SzGnd.setDisabled(False)
                self.SzDeactivated = False
        
    def SxGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.SxAxis.getMode() != self.SxAxis.INACTIVE:
            if event:  # axis should grounded
                self.SxAxis.switchMode(self.SxAxis.GROUND)
                self.SxGrounded = True
            else:
                self.SxPosChange(0.)
                self.SxAxis.switchMode(self.SxAxis.OFFSET)
                # print(self.SxAxis.getMode())
                self.SxGrounded = False
            self.updateUIWhenGnd(self.SxAxis, self.SxGrounded)
    def SyGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.SyAxis.getMode() != self.SyAxis.INACTIVE:
            if event:  # axis should grounded
                self.SyAxis.switchMode(self.SyAxis.GROUND)
                self.SyGrounded = True
            else:
                self.SyPosChange(0.)
                self.SyAxis.switchMode(self.SyAxis.OFFSET)
                self.SyGrounded = False
            self.updateUIWhenGnd(self.SyAxis, self.SyGrounded)
    def SzGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.SzAxis.getMode() != self.SzAxis.INACTIVE:
            if event:  # axis should grounded
                self.SzAxis.switchMode(self.SzAxis.GROUND)
                self.SzGrounded = True
            else:
                self.SzPosChange(0.)
                self.SzAxis.switchMode(self.SzAxis.OFFSET)
                self.SzGrounded = False
            self.updateUIWhenGnd(self.SzAxis, self.SzGrounded)
                
        
    #########################
    # POSITIONERS FUNCTIONS #
    ######################### 
        
    def PnbOfStepsUpdate(self, event=0):
        """ Updates the internal variable of nb of steps to do for a single user click for a positioner axis. """
        self.nbOfStepsToDo = event

    # Orders of single step (or nbOfStepsToDo steps)
    def PxStepUp(self, event=0):
        self.PxAxis.stepUp(self.nbOfStepsToDo)
    def PxStepDown(self, event=0):
        self.PxAxis.stepDown(self.nbOfStepsToDo)
                
    def PyStepUp(self, event=0):
        self.PyAxis.stepUp(self.nbOfStepsToDo)
    def PyStepDown(self, event=0):#
        self.PyAxis.stepDown(self.nbOfStepsToDo)
                
    def PzStepUp(self, event=0):
        self.PzAxis.stepUp(self.nbOfStepsToDo)
    def PzStepDown(self, event=0):
        self.PzAxis.stepDown(self.nbOfStepsToDo)
        
    # Orders of continuous motion and stop
    def PxContUp(self, event=0):
        self.PxAxis.stepUp()
        self.contActive.xUp = True
        self.contActive.xDown = False
        self.toggleContIndicator(self.contActive)
    def PxContDown(self, event=0):
        self.PxAxis.stepDown()
        self.contActive.xUp = False
        self.contActive.xDown = True
        self.toggleContIndicator(self.contActive)
    def PxStop(self, event=0):
        self.PxAxis.stopMotion()
        self.contActive.xUp = False
        self.contActive.xDown = False
        self.toggleContIndicator(self.contActive)
                
    def PyContUp(self, event=0):
        self.PyAxis.stepUp()
        self.contActive.yUp = True
        self.contActive.yDown = False
        self.toggleContIndicator(self.contActive)
    def PyContDown(self, event=0):
        self.PyAxis.stepDown()
        self.contActive.yUp = False
        self.contActive.yDown = True
        self.toggleContIndicator(self.contActive)
    def PyStop(self, event=0):
        self.PyAxis.stopMotion()
        self.contActive.yUp = False
        self.contActive.yDown = False
        self.toggleContIndicator(self.contActive)
                
    def PzContUp(self, event=0):
        self.PzAxis.stepUp()
        self.contActive.zUp = True
        self.contActive.zDown = False
        self.toggleContIndicator(self.contActive)
    def PzContDown(self, event=0):
        self.PzAxis.stepDown()
        self.contActive.zUp = False
        self.contActive.zDown = True
        self.toggleContIndicator(self.contActive)
    def PzStop(self, event=0):
        self.PzAxis.stopMotion()
        self.contActive.zUp = False
        self.contActive.zDown = False
        self.toggleContIndicator(self.contActive)
    
    # functions to deal with GUI user inputs and updates from device-origin values.
    def PxAmpChange(self, event):
        """ Sets the Px axis amplitude on the ANC when a user-change happens. """
        self.PxAxis.setStepAmplitude(event)
        self.PxAmpUpdate()
    def PyAmpChange(self, event):
        """ Sets the Py axis amplitude on the ANC when a user-change happens. """
        self.PyAxis.setStepAmplitude(event)
        self.PyAmpUpdate()
    def PzAmpChange(self, event):
        """ Sets the Pz axis amplitude on the ANC when a user-change happens. """
        self.PzAxis.setStepAmplitude(event)
        self.PzAmpUpdate()
    
    def PxAmpUpdate(self):
        """ Updates the Px amplitude field in GUI with the current real value of the axis. """
        self.PxAmp = self.PxAxis.getStepAmplitude()
        self.ui.PxAmp.setValue(self.PxAmp)
    def PyAmpUpdate(self):
        """ Updates the Py amplitude field in GUI with the current real value of the axis. """
        self.PyAmp = self.PyAxis.getStepAmplitude()
        self.ui.PyAmp.setValue(self.PyAmp)
    def PzAmpUpdate(self):
        """ Updates the Pz amplitude field in GUI with the current real value of the axis. """
        self.PzAmp = self.PzAxis.getStepAmplitude()
        self.ui.PzAmp.setValue(self.PzAmp)
        
        
    def PxFreqChange(self, event):
        """ Sets the Px axis frequency on the ANC when a user-change happens. """
        self.PxAxis.setStepFrequency(event)
        self.PxFreqUpdate()
    def PyFreqChange(self, event):
        """ Sets the Py axis frequency on the ANC when a user-change happens. """
        self.PyAxis.setStepFrequency(event)
        self.PyFreqUpdate()
    def PzFreqChange(self, event):
        """ Sets the Pz axis frequency on the ANC when a user-change happens. """
        self.PzAxis.setStepFrequency(event)
        self.PzFreqUpdate()
    
    def PxFreqUpdate(self):
        """ Updates the Px frequency field in GUI with the current real value of the axis. """
        self.PxFreq = self.PxAxis.getStepFrequency()
        self.ui.PxFreq.setValue(self.PxFreq)
    def PyFreqUpdate(self):
        """ Updates the Py frequency field in GUI with the current real value of the axis. """
        self.PyFreq = self.PyAxis.getStepFrequency()
        self.ui.PyFreq.setValue(self.PyFreq)
    def PzFreqUpdate(self):
        """ Updates the Pz frequency field in GUI with the current real value of the axis. """
        self.PzFreq = self.PzAxis.getStepFrequency()
        self.ui.PzFreq.setValue(self.PzFreq)
        
    def PxOffsetChange(self, event):
        """ Sets the Px axis offset on the ANC when a user-change happens. """
        self.PxAxis.setStepOffset(event)
        self.PxOffsetUpdate()
    def PyOffsetChange(self, event):
        """ Sets the Py axis offset on the ANC when a user-change happens. """
        self.PyAxis.setStepOffset(event)
        self.PyOffsetUpdate()
    def PzOffsetChange(self, event):
        """ Sets the Pz axis offset on the ANC when a user-change happens. """
        self.PzAxis.setStepOffset(event)
        self.PzOffsetUpdate()
    
    def PxOffsetUpdate(self):
        """ Updates the Px offset field in GUI with the current real value of the axis. """
        self.PxOffset = self.PxAxis.getOffset()
        self.ui.PxOffset.setValue(self.PxOffset)
    def PyOffsetUpdate(self):
        """ Updates the Py offset field in GUI with the current real value of the axis. """
        self.PyOffset = self.PyAxis.getOffset()
        self.ui.PyOffset.setValue(self.PyOffset)
    def PzOffsetUpdate(self):
        """ Updates the Pz offset field in GUI with the current real value of the axis. """
        self.PzOffset = self.PzAxis.getOffset()
        self.ui.PzOffset.setValue(self.PzOffset)
        
    def PxModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.PxAxis.getMode()
        if currentMode in {self.PxAxis.STEP, self.PxAxis.OFFSET}:
            self.PxGrounded = False
        else:
            self.PxGrounded = True
        self.ui.PxGnd.setChecked(self.PxGrounded)
        self.updateUIWhenGnd(self.PxAxis, self.PxGrounded)
    def PyModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.PyAxis.getMode()
        if currentMode in {self.PyAxis.STEP, self.PyAxis.OFFSET}:
            self.PyGrounded = False
        else:
            self.PyGrounded = True
        self.ui.PyGnd.setChecked(self.PyGrounded)
        self.updateUIWhenGnd(self.PyAxis, self.PyGrounded)
    def PzModeUpdate(self):
        """ Updates the tickbox "GND" in the GUI with the current mode (grounded or not) of the axis. """
        currentMode = self.PzAxis.getMode()
        if currentMode in {self.PzAxis.STEP, self.PzAxis.OFFSET}:
            self.PzGrounded = False
        else:
            self.PzGrounded = True
        self.ui.PzGnd.setChecked(self.PzGrounded)
        self.updateUIWhenGnd(self.PzAxis, self.PzGrounded)
    
    def PxGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.PxAxis.getMode() != self.PxAxis.INACTIVE:
            if event:  # axis should grounded
                self.PxAxis.switchMode(self.PxAxis.GROUND)
                self.PxGrounded = True
            else:
                self.PxAxis.switchMode(self.PxAxis.STEP)
                self.PxGrounded = False
                self.PxAmpUpdate()
                self.PxFreqUpdate()
                self.PxOffsetUpdate()
            self.updateUIWhenGnd(self.PxAxis, self.PxGrounded)
    def PyGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.PyAxis.getMode() != self.PyAxis.INACTIVE:
            if event:  # axis should grounded
                self.PyAxis.switchMode(self.PyAxis.GROUND)
                self.PyGrounded = True
            else:
                self.PyAxis.switchMode(self.PyAxis.STEP)
                self.PyGrounded = False
                self.PyAmpUpdate()
                self.PyFreqUpdate()
                self.PyOffsetUpdate()
            self.updateUIWhenGnd(self.PyAxis, self.PyGrounded)
    def PzGndToggled(self, event):
        """ Called when checkbox "GND" is toggled. """
        if self.PzAxis.getMode() != self.PzAxis.INACTIVE:
            if event:  # axis should grounded
                self.PzAxis.switchMode(self.PzAxis.GROUND)
                self.PzGrounded = True
            else:
                self.PzAxis.switchMode(self.PzAxis.STEP)
                self.PzGrounded = False
                self.PzAmpUpdate()
                self.PzFreqUpdate()
                self.PzOffsetUpdate()
            self.updateUIWhenGnd(self.PzAxis, self.PzGrounded)
                
    def updateUIWhenGnd(self, axis, grounded):
        if axis is self.PxAxis:
            self.ui.PxAmp.setDisabled(grounded)  # if grounded, disable
            self.ui.PxFreq.setDisabled(grounded)
            self.ui.PxStepUp.setDisabled(grounded)
            self.ui.PxStepDown.setDisabled(grounded)
            self.ui.PxContUp.setDisabled(grounded)
            self.ui.PxContDown.setDisabled(grounded)
        elif axis is self.PyAxis:
            self.ui.PyAmp.setDisabled(grounded)  # if grounded, disable
            self.ui.PyFreq.setDisabled(grounded)
            self.ui.PyStepUp.setDisabled(grounded)
            self.ui.PyStepDown.setDisabled(grounded)
            self.ui.PyContUp.setDisabled(grounded)
            self.ui.PyContDown.setDisabled(grounded)
        elif axis is self.PzAxis:
            self.ui.PzAmp.setDisabled(grounded)  # if grounded, disable
            self.ui.PzFreq.setDisabled(grounded)
            self.ui.PzStepUp.setDisabled(grounded)
            self.ui.PzStepDown.setDisabled(grounded)
            self.ui.PzContUp.setDisabled(grounded)
            self.ui.PzContDown.setDisabled(grounded)
        elif axis is self.SxAxis:
            self.ui.SxPos.setDisabled(grounded)  # if grounded, disable
            self.ui.SxDeactivate.setDisabled(grounded)
        elif axis is self.SyAxis:
            self.ui.SyPos.setDisabled(grounded)  # if grounded, disable
            self.ui.SyDeactivate.setDisabled(grounded)
        elif axis is self.SzAxis:
            self.ui.SzPos.setDisabled(grounded)  # if grounded, disable
            self.ui.SzDeactivate.setDisabled(grounded)
            
    
    #################################
    # KEYBOARD NAVIGATION FUNCTIONS #
    #################################
        
    def keyPressEvent(self, event):
        """ For keyboard navigation, called by Qt when a key press event happens. """
        # deals with the keyboard navigation
        #if not event.isAutoRepeat():
#        print('Press',event.key())
        
        if self.keyControl:  # check if keyboard control is on (big button)
            if event.key() == self.keys.close:          # close program
                self.close()
            elif event.key() == self.keys.SxDown:       # scanner X down
                singleStep = self.ui.SxPos.singleStep()
                value = self.ui.SxPos.value()
                if self.SxStepRev:
                    self.ui.SxPos.setValue(value + singleStep)
                else:
                    self.ui.SxPos.setValue(value - singleStep)
            elif event.key() == self.keys.SxUp:         # scanner X up
                singleStep = self.ui.SxPos.singleStep()
                value = self.ui.SxPos.value()
                if self.SxStepRev:
                    self.ui.SxPos.setValue(value - singleStep)
                else:
                    self.ui.SxPos.setValue(value + singleStep)
            elif event.key() == self.keys.SyDown:       # scanner Y down
                singleStep = self.ui.SyPos.singleStep()
                value = self.ui.SyPos.value()
                if self.SyStepRev:
                    self.ui.SyPos.setValue(value + singleStep)
                else:
                    self.ui.SyPos.setValue(value - singleStep)
            elif event.key() == self.keys.SyUp:         # scanner Y up
                singleStep = self.ui.SyPos.singleStep()
                value = self.ui.SyPos.value()
                if self.SyStepRev:
                    self.ui.SyPos.setValue(value - singleStep)
                else:
                    self.ui.SyPos.setValue(value + singleStep)
            elif event.key() == self.keys.SzDown:       # scanner Z down
                singleStep = self.ui.SzPos.singleStep()
                value = self.ui.SzPos.value()
                if self.SzStepRev:
                    self.ui.SzPos.setValue(value + singleStep)
                else:
                    self.ui.SzPos.setValue(value - singleStep)
            elif event.key() == self.keys.SzUp:         # scanner Z up
                singleStep = self.ui.SzPos.singleStep()
                value = self.ui.SzPos.value()
                if self.SzStepRev:
                    self.ui.SzPos.setValue(value - singleStep)
                else:
                    self.ui.SzPos.setValue(value + singleStep)
            elif event.key() in self.keys.positioners:  # positioners in general (dealt with in _keyPressPxyzDetail)
                if not event.isAutoRepeat():
                    if not self.contStepMode:
                        self._keyPressPxyzDetail(event.key())
                    else:
                        self._keyPressPxyzDetail(event.key())
            elif event.key() == self.keys.cont:         # on press of continuous motion key, activate continuous motion mode
                self.contStepMode = True
            elif event.key() == self.keys.contLock:     # locked continuous motion of positioners
                self.contLockKeyPressed = True
            elif event.key() == self.keys.fullStop:     # full stop of all positioners motion
                self.PxStop()
                self.PyStop()
                self.PzStop()
                self.contLockKeyPressed = False
                self.contLockedStepMode.x = False
                self.contLockedStepMode.y = False
                self.contLockedStepMode.z = False
    
    def keyReleaseEvent(self, event):
        """ For keyboard navigation, called by Qt when a key release event happens. """
        #if not event.isAutoRepeat():
#        print('Release',event.key())
        if self.keyControl:  # check if keyboard control is on (big button)
            if event.key() in self.keys.positioners:    # for positioners in general (dealt with in _keyReleasePxyzDetail)
                if not event.isAutoRepeat():
                    # if continuous motion without locking, will stop the motion on release
                    if self.contStepMode and not self.contLockedStepMode: 
                        self._keyReleasePxyzDetail(event.key())
            elif event.key() == self.keys.cont:         # on release of continuous motion key, deactivate continuous motion mode
                self.contStepMode = False
                if not self.contLockedStepMode:
                    self.PxStop()
                    self.PyStop()
                    self.PzStop()
            elif event.key() == self.keys.contLock:     # locked continuous motion key released
                self.contLockKeyPressed = False
                
    def _keyPressPxyzDetail(self, key):
        """ Detail of keypress function for handling positioners exclusively """
        if key in self.keys.Px:  # X AXIS
            if self.contLockedStepMode.x and not self.contLockKeyPressed:  # if button pushed while stepping in locked mode, stop motors
                self.PxStop()
                self.contLockedStepMode.x = False
            elif self.contStepMode:  # if continuous mode is expected, begin stepping
                if self.contLockKeyPressed:
                    self.contLockedStepMode.x = True
                    
                if key == self.keys.PxDown:
                    self.PxContDown()
                elif key == self.keys.PxUp:
                    self.PxContUp()
            else:  # if single step
                if key == self.keys.PxDown:
                    self.PxStepDown()
                elif key == self.keys.PxUp:
                    self.PxStepUp()
                    
        elif key in self.keys.Py:  # Y AXIS
            if self.contLockedStepMode.y and not self.contLockKeyPressed:  # if button pushed while stepping in locked mode, stop motors
                self.PyStop()
                self.contLockedStepMode.y = False
            elif self.contStepMode:  # if continuous mode is expected, begin stepping
                if self.contLockKeyPressed:
                    self.contLockedStepMode.y = True
                    
                if key == self.keys.PyDown:
                    self.PyContDown()
                elif key == self.keys.PyUp:
                    self.PyContUp()
            else:  # if single step
                if key == self.keys.PyDown:
                    self.PyStepDown()
                elif key == self.keys.PyUp:
                    self.PyStepUp()
                    
        elif key in self.keys.Pz:  # Z AXIS
            if self.contLockedStepMode.z and not self.contLockKeyPressed:  # if button pushed while stepping in locked mode, stop motors
                self.PzStop()
                self.contLockedStepMode.z = False
            elif self.contStepMode:  # if continuous mode is expected, begin stepping
                if self.contLockKeyPressed:
                    self.contLockedStepMode.z = True
                    
                if key == self.keys.PzDown:
                    self.PzContDown()
                elif key == self.keys.PzUp:
                    self.PzContUp()
            else:  # if single step
                if key == self.keys.PzDown:
                    self.PzStepDown()
                elif key == self.keys.PzUp:
                    self.PzStepUp()
        
            
    def _keyReleasePxyzDetail(self, key):
        """ Detail of keyrelease function for handling positioners exclusively. 
        Will be called by keyReleaseEvent() only if not locked mode to stop the motion. """
        if key in self.keys.Px:  # X AXIS
            self.PxStop()
        elif key in self.keys.Py:  # Y AXIS
            self.PyStop()
        elif key in self.keys.Pz:  # Z AXIS
            self.PzStop()
    
    
    ######################
    # PURE GUI FUNCTIONS #
    ######################
    
    def toggleContIndicator(self, contActive):
        """ Switch on the CONT indicators for the corresponding axes which are moving. """
        if contActive.xUp or contActive.xDown:
            self.ui.contXled.setStyleSheet("background-color: rgb(0, 115, 255);\ncolor: rgb(255, 255, 255);");
        else:
            self.ui.contXled.setStyleSheet("background-color: rgb(231, 248, 255);\ncolor: rgb(255, 255, 255);");
        if contActive.yUp or contActive.yDown:
            self.ui.contYled.setStyleSheet("background-color: rgb(0, 115, 255);\ncolor: rgb(255, 255, 255);");
        else:
            self.ui.contYled.setStyleSheet("background-color: rgb(231, 248, 255);\ncolor: rgb(255, 255, 255);");
        if contActive.zUp or contActive.zDown:
            self.ui.contZled.setStyleSheet("background-color: rgb(0, 115, 255);\ncolor: rgb(255, 255, 255);");
        else:
            self.ui.contZled.setStyleSheet("background-color: rgb(231, 248, 255);\ncolor: rgb(255, 255, 255);");
            
    def arrowKeyControlToggled(self, event):
        """ Big keyboard control button toggled by user or by focusOnWindow(). 
        Updates the keyControl state variable and changes the appearance of the button. """
        
        self.keyControl = event
        if self.keyControlAutoSwitched:
            self.keyControlAutoSwitched = False
        elif self.keyControl == False:  # if user deactivates keyboard control on purpose
            self.keyControlSetByUser = True
        else:
            self.keyControlSetByUser = False
            
        if self.keyControl:
            self.ui.arrowKeyControl.setStyleSheet("background-color: rgb(38, 234, 68);");
        else:
            self.ui.arrowKeyControl.setStyleSheet("background-color: red;");
    
    def toggleArrowKeyControlShortcut(self):
        """ Programmatically toggle big keyboard control button. Associated to the Ctrl+Space shortcut. """
        self.ui.arrowKeyControl.toggle()
            
    def focusOnWindow(self, oldWidget, newWidget):
        """ Called when the focus changes from or to the app, and toggled the keyboard control accordingly. """
        if not self.keyControlSetByUser:
            self.keyControlAutoSwitched = True
            if newWidget == self:  # press easy control button
                self.ui.arrowKeyControl.setChecked(True)
            elif oldWidget == self:  # unpress easy control button
                self.ui.arrowKeyControl.setChecked(False)

    def guiDeactivateAxes(self):
        """ Called at the start of the program to disable the controls associated to inactive axes. """
        if self.SxAxis.mode == self.SxAxis.INACTIVE:
            self.ui.SxPos.setEnabled(False)
            self.ui.SxDeactivate.setEnabled(False)
            self.ui.SxGnd.setEnabled(False)
        if self.SyAxis.mode == self.SyAxis.INACTIVE:
            self.ui.SyPos.setEnabled(False)
            self.ui.SyDeactivate.setEnabled(False)
            self.ui.SyGnd.setEnabled(False)
        if self.SzAxis.mode == self.SzAxis.INACTIVE:
            self.ui.SzPos.setEnabled(False)
            self.ui.SzDeactivate.setEnabled(False)
            self.ui.SzGnd.setEnabled(False)
        if self.PxAxis.mode == self.PxAxis.INACTIVE:
            self.ui.PxAmp.setEnabled(False)
            self.ui.PxFreq.setEnabled(False)
            self.ui.PxOffset.setEnabled(False)
            self.ui.PxStepUp.setEnabled(False)
            self.ui.PxStepDown.setEnabled(False)
            self.ui.PxContUp.setEnabled(False)
            self.ui.PxContDown.setEnabled(False)
        if self.PyAxis.mode == self.PyAxis.INACTIVE:
            self.ui.PyAmp.setEnabled(False)
            self.ui.PyFreq.setEnabled(False)
            self.ui.PyOffset.setEnabled(False)
            self.ui.PyStepUp.setEnabled(False)
            self.ui.PyStepDown.setEnabled(False)
            self.ui.PyContUp.setEnabled(False)
            self.ui.PyContDown.setEnabled(False)
        if self.PzAxis.mode == self.PzAxis.INACTIVE:
            self.ui.PzAmp.setEnabled(False)
            self.ui.PzFreq.setEnabled(False)
            self.ui.PzOffset.setEnabled(False)
            self.ui.PzStepUp.setEnabled(False)
            self.ui.PzStepDown.setEnabled(False)
            self.ui.PzContUp.setEnabled(False)
            self.ui.PzContDown.setEnabled(False)

    
def errorMessageWindow(parentWindow, winTitle, winText):
    """ Displays a QT error message box, with title, text and OK button. """
    msg = QMessageBox(parentWindow)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(winTitle)
    msg.setText(winText)
    msg.exec_()

def attopos_run(config):
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = AttoPos(app, config)
    
    try:
        #window.ui.setFocus(True)
        window.setFocus(True)
        window.show()
        app.exec_()
    except:
        raise
    finally:
        window.closeInstruments()
        
if __name__ == "__main__":
    

    config = {"attoAxes": {"Px": 1, "Py": 2, "Pz": 3, "Sx": 4, "Sy": 5, "Sz": 6}, 
              "attoVisaScannersId": "ASRL1::INSTR", 
              "attoVisaPositionersId": "ASRL1::INSTR", 
              "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}


    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    
    window = AttoPos(app, config)
    
    try:
        #window.ui.setFocus(True)
        window.setFocus(True)
        window.show()
        app.exec_()
    except:
        raise
    finally:
        window.closeInstruments()
            
    #window.selectFile()
    

