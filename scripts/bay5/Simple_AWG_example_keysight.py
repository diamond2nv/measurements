# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 10:57:53 2016

@author: AW
First simple routine  
"""

# Import the driver calls and create an instance of SD_DIO
from signadyne import *

AWGobj = SD_AOU()

# Gather Information about AWG S/N, Slot and S/N
AWGPart = AWGobj.getProductNameBySlot(1,11)
AWGNumber = AWGobj.getSerialNumberBySlot(1,11)
NumModules = AWGobj.moduleCount()
print "Part =",AWGPart
print "S/N =",AWGNumber
print "Number of Modules = ",NumModules

# Open the AWG Module
AWGModuleIDbySN = AWGobj.openWithSerialNumber("SD-PXE-AWG-H3344F-2G","0VKHSVMJ")
#ModuleIDbySlot = DIGobj.openWithSlot("SD-PXE-AWG-H3344F-2G",1,11)
print "AWG ModuleID by S/N = ", AWGModuleIDbySN
#print "Module ID by Slot", ModuleIDbySlot

# Configure a waveform and send from the AWG using all-in-one command
#AWGFromFile(nAWG,waveformFile,triggerMode,startDelay,cycles,prescaler,paddingMode=0)
#AWGobj.AWGFromFile(0,"C:/Users/Public/Documents/Signadyne/Examples/Waveforms/Gaussian.csv",0,0,0,0)

# Configure a waveform and send from the AWG using individual commands
wave = SD_Wave()
# newFromFile(self, waveformFile)
wave.newFromFile("C:/Users/Public/Documents/Signadyne/Examples/Waveforms/Gaussian.csv")
# waveformLoad(self, waveformObject, waveformNumber, paddingMode = 0)
AWGobj.waveformLoad(wave, 0);
# channelWaveShape(nChannel, waveShape)
AWGobj.channelWaveShape(0, SD_Waveshapes.AOU_AWG)
# AWG.channelAmplitude(ch, value in Volts)
AWGobj.channelAmplitude(0, 1.0)
# AWGqueueWaveform(self, nAWG, waveformNumber, triggerMode, startDelay, cycles, prescaler)
# triggermode >>> 0=Auto, 1=Software/HVI, 5=S/HVI-perCycle, 2=External Trigger, 6=ExternalTrigger/Cycle
AWGobj.AWGqueueWaveform(0, 0, 0, 0, 0, 0)
#AWGqueueMarkerConfig(self, nAWG, markerMode, trgPXImask, trgIOmask, value, syncMode, length, delay) 
# length must be equal or greater than 2
#AWGobj.AWGqueueMarkerConfig(0, 1, 0x01, 0, 1, 0, 2, 0)
AWGobj.AWGqueueMarkerConfig(0, SD_MarkerModes.START, 0x01, 0, SD_TriggerValue.HIGH, SD_SyncModes.SYNC_CLK10, 10, 0)


AWGobj.AWGstart(0)

# Stop the AWG
AWGobj.AWGstop(0)
# Close the session and clear out variables
AWGobj.close()
