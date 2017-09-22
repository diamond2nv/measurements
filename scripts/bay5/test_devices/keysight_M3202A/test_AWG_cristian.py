
import sys
sys.path.append ('C:\Research\measurements\libs')
import keysightSD1 as ks

import matplotlib.pyplot as plt
import numpy as np
import time

# MODULE CONSTANTS
product = ""
chassis = 1

# change slot numbers to your values
slot_awg = 2

#NUM_CHANNELS = 3
#CHANNEL_TRIG_CONTROL = 3

# CREATE AND OPEN MODULE IN
AWGobj = ks.SD_AOU()

AWGid = AWGobj.openWithSlot(product, chassis, slot_awg)

print 'AWG id: ', AWGid

if AWGid < 0:
	print("Error opening module IN - error code:", AWGid)
else:
	print("===== MODULE IN =====")
	print("ID:\t\t", AWGid)
	print("Product name:\t", AWGobj.getProductName())
	print("Serial number:\t", AWGobj.getSerialNumber())
	print("Chassis:\t", AWGobj.getChassis())
	print("Slot:\t\t", AWGobj.getSlot())


def gaussian_waveform ():
	# Configure a waveform and send from the AWG using individual commands
	waveform = ks.SD_Wave()
	# newFromFile(self, waveformFile)
	waveform.newFromFile("C:/Users/Public/Documents/Keysight/SD1/Examples/Waveforms/Gaussian.csv")
	# waveformLoad(self, waveformObject, waveformNumber, paddingMode = 0)
	AWGobj.waveformFlush() #empties AWG memory
	AWGobj.waveformLoad(waveform, 0);
	# channelWaveShape(nChannel, waveShape) -- sets the waveform type for the output channel
	AWGobj.channelWaveShape(0, ks.SD_Waveshapes.AOU_AWG)
	# AWG.channelAmplitude(ch, value in Volts)
	AWGobj.channelAmplitude(0, 1.0)
	# AWGqueueWaveform(self, nAWG, waveformNumber, triggerMode, startDelay, cycles, prescaler)
	# triggermode >>> 0=Auto, 1=Software/HVI, 5=S/HVI-perCycle, 2=External Trigger, 6=ExternalTrigger/Cycle
	AWGobj.AWGqueueWaveform(0, 0, 0, 0, 0, 0)
	#AWGqueueMarkerConfig(self, nAWG, markerMode, trgPXImask, trgIOmask, value, syncMode, length, delay) 
	# length must be equal or greater than 2
	#AWGobj.AWGqueueMarkerConfig(0, 1, 0x01, 0, 1, 0, 2, 0)
	AWGobj.AWGqueueMarkerConfig(0, ks.SD_MarkerModes.START, 0x01, 0, ks.SD_TriggerValue.HIGH, ks.SD_SyncModes.SYNC_CLK10, 10, 0)


	AWGobj.AWGstart(0)

	# Stop the AWG
	AWGobj.AWGstop(0)
	# Close the session and clear out variables
	AWGobj.close()

def amplitude_modulation (channel=0, fc = 50e6, wf = None):

	#out[t] = (A + G*AWG[t]) * cos(2pi fc t + phi)

	#set carrier cos(2pi fc t + phi)
	A = 0.
	AWGobj.channelAmplitude(channel, A)
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_SINUSOIDAL)
	AWGobj.channelFrequency(channel, fc)

	G = 1 #modulation gain
	#load modulating waveform AWG[t]
	waveform = ks.SD_Wave()
	if (wf != None):
		print 'Waveform passed as parameter!'
		waveform.newFromArrayDouble (waveformType = 0, waveformDataA = wf)
	else:
		# newFromFile(self, waveformFile)
		waveform.newFromFile("C:/Users/Public/Documents/Keysight/SD1/Examples/Waveforms/Gaussian.csv")
	# waveformLoad(self, waveformObject, waveformNumber, paddingMode = 0)
	AWGobj.waveformFlush() #empties AWG memory
	AWGobj.waveformLoad(waveform, 0); #loads waveform in module onboard RAM

	#modulationAmplitudeConfig (nChannel, modulationType, modulationGain), modulationType=1 for amplitude modulation
	AWGobj.modulationAmplitudeConfig (channel, 1, G)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueMarkerConfig(0, ks.SD_MarkerModes.START, 0x01, 0, ks.SD_TriggerValue.HIGH, ks.SD_SyncModes.SYNC_CLK10, 10, 0)

	AWGobj.AWGstart(0)
	AWGobj.AWGstop(0)
	AWGobj.close()


def amplitude_modulation_ramsey2 (channel=0, fc = 50e6, wait_time=10):

	#out[t] = (A + G*AWG[t]) * cos(2pi fc t + phi)
	tr_ch = 2

	#set carrier cos(2pi fc t + phi)
	A = 0.
	AWGobj.channelAmplitude(channel, A)
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_SINUSOIDAL)
	AWGobj.channelWaveShape(tr_ch, ks.SD_Waveshapes.AOU_AWG)
	#AWGobj.channelAmplitude(tr_ch, .5)
	AWGobj.channelFrequency(channel, fc)

	G = 0.5 #modulation gain
	#load modulating waveform AWG[t]
	wf_pi = ks.SD_Wave()
	wf_pi.newFromArrayDouble (waveformType = 0, waveformDataA = gaussian_pulse(50))
	wf_wait = ks.SD_Wave()
	wf_wait.newFromArrayDouble (waveformType = 0, waveformDataA = np.zeros(wait_time))
	wf_pi2 = ks.SD_Wave()
	wf_pi2.newFromArrayDouble (waveformType = 0, waveformDataA = pi_pulse(50))


	AWGobj.waveformFlush() 
	AWGobj.waveformLoad(wf_pi, 0); 
	AWGobj.waveformLoad(wf_wait, 1); 
	AWGobj.waveformLoad(wf_pi2, 2); 

	#modulationAmplitudeConfig (nChannel, modulationType, modulationGain), modulationType=1 for amplitude modulation
	
	AWGobj.modulationAmplitudeConfig (channel, 1, G)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=2, triggerMode=0, startDelay=0, cycles=2, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=1, triggerMode=0, startDelay=0, cycles=3, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	
	'''
	AWGobj.AWGqueueWaveform(nAWG=2, waveformNumber=0, triggerMode=0, startDelay=0, cycles=7, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=2, waveformNumber=1, triggerMode=0, startDelay=0, cycles=4, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=2, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	'''

	#AWGqueueConfig (nAWG, mode)
	#mode:	0: one shot, 1: cyclic
	AWGobj.AWGqueueConfig (nAWG=0, mode=0)
	#AWGobj.AWGqueueConfig (nAWG=2, mode=0)


	#AWGqueueMarkerConfig (nAWG, markerMode, trgPXImask, trgIOmask, value, syncMode, length5Tclk, delay5Tclk)
	#markerMode: 	operation mode of the queue: 0: disabled, 1: on WF start, 2: on WF start after WF delay
	#					3: ON every cycle, 4: End (not implemented)
	#trgPXImask: 	mask to select PXI triggers to use (bit0: PXItrg0, etc, etc)
	#trgIO mask:	mask to select front-panel triggers to use (bit0: triggerIO)
	#vlaue: 		0: low, 1: high
	#syncMode:		0: immediate, 1: sync10
	#length:		pulse length in multiples of TCLK x 5
	#delay:			pulse delay in multiples of TCLK x 5
	AWGobj.AWGqueueMarkerConfig(nAWG=0, markerMode=ks.SD_MarkerModes.START, trgPXImask=0x01, 
				trgIOmask=0, value=ks.SD_TriggerValue.HIGH, syncMode=ks.SD_SyncModes.SYNC_CLK10, 
				length=10, delay=0)

	#AWGobj.triggerIOconfig (direction = ks.SD_TriggerDirections.AOU_TRG_OUT, syncMode = ks.SD_SyncModes.SYNC_NONE)
	#AWGobj.triggerIOwrite (value=1)

	AWGobj.AWGstart(0)
	for i in np.arange(3):
		time.sleep (1)
		print AWGobj.AWGisRunning(0)
	AWGobj.AWGstop(0)
	print AWGobj.AWGisRunning(0)
	#AWGobj.AWGreset(0)
	AWGobj.waveformFlush()
	print AWGobj.AWGisRunning(0)
	

	'''
	AWGobj.AWGstartMultiple (0x05)
	time.sleep(5)
	AWGobj.AWGstopMultiple (0xF)
	AWGobj.AWGstop(0)
	AWGobj.AWGstop(2)
	'''
	#AWGobj.triggerIOwrite(value=0)
	AWGobj.close()


def ramsey_waveform ():

	pi_length_ns = 300
	wait_time = 2000

	wf = np.zeros(2*pi_length_ns+wait_time)
	wf[:pi_length_ns] = np.ones(pi_length_ns)
	wf[-pi_length_ns:] = np.ones(pi_length_ns)

	return wf
	#plt.plot (wf)
	#plt.axis([0,3000, -0.2, 1.2])
	#plt.show()

def pi_pulse (duration_ns):
	return np.ones (duration_ns)

def gaussian_pulse (duration_ns):
	x = np.arange(duration_ns)-duration_ns/2
	wf = np.exp(-(x/(duration_ns/4.))**2)

	#plt.plot (x, wf)
	#plt.show()
	return wf



#wf = ramsey_waveform()
#amplitude_modulation(wf=wf)
amplitude_modulation_ramsey2 (fc=0e6, wait_time = 100)
