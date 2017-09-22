
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

AWGobj = ks.SD_AOU()
AWGid = AWGobj.openWithSlot(product, chassis, slot_awg)

if AWGid < 0:
	print("Error opening module IN - error code:", AWGid)
else:
	print("===== MODULE IN =====")
	print("ID:\t\t", AWGid)
	print("Product name:\t", AWGobj.getProductName())
	print("Serial number:\t", AWGobj.getSerialNumber())
	print("Chassis:\t", AWGobj.getChassis())
	print("Slot:\t\t", AWGobj.getSlot())



def waveform_gen_test (channel = 0, fc = 50e6, wait_time=10, AM=False):

	#configuring trigger
	AWGobj.triggerIOconfig (direction = ks.SD_TriggerDirections.AOU_TRG_IN, 
					syncMode = ks.SD_SyncModes.SYNC_CLK10)
	AWGobj.AWGtriggerExternalConfig (nAWG=channel, externalSource=ks.SD_TriggerExternalSources.TRIGGER_EXTERN, 
					triggerBehavior=ks.SD_TriggerBehaviors.TRIGGER_RISE)

	if AM:
		A = 0.
		AWGobj.channelAmplitude(channel, A)
		AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_SINUSOIDAL)
		AWGobj.channelFrequency(channel, fc)
		G = 1 #modulation gain
		AWGobj.modulationAmplitudeConfig (channel, 1, G)
	else:
		AWGobj.channelAmplitude(channel, 1.)
		AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_AWG)

	wf_gauss = ks.SD_Wave()
	wf_gauss.newFromArrayDouble (waveformType = 0, waveformDataA = gaussian_pulse(200))
	wf_wait = ks.SD_Wave()
	wf_wait.newFromArrayDouble (waveformType = 0, waveformDataA = np.zeros(wait_time))
	wf_rect = ks.SD_Wave()
	sq_pulse = 0.5*np.ones(200)
	wf_rect.newFromArrayDouble (waveformType = 0, waveformDataA = sq_pulse)

	#plt.plot (sq_pulse)
	#plt.show()

	AWGobj.waveformFlush() 
	AWGobj.AWGflush(channel)
	AWGobj.waveformLoad(wf_gauss, 0); 
	AWGobj.waveformLoad(wf_wait, 1); 
	AWGobj.waveformLoad(wf_rect, 2); 

	#trigger mode: 0 = Auto, 2: external, 6: external-cyclic
	#AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=0, triggerMode=2, startDelay=0, cycles=2, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=channel, waveformNumber=0, triggerMode=2, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=channel, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=channel, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=channel, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)

	AWGobj.AWGqueueConfig (nAWG=channel, mode=1)

	print 'AWG start...'
	AWGobj.AWGstart(channel)
	time.sleep(5)
	AWGobj.AWGstopMultiple(channel)
	print 'AWG stop...'
	AWGobj.waveformFlush()
	
	
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_OFF)
	AWGobj.AWGqueueConfig (nAWG=channel, mode=0)
	AWGobj.AWGstart(channel)
	AWGobj.AWGstop(channel)
	

	AWGobj.AWGflush(channel)
	AWGobj.close()

def gaussian_pulse (duration_ns):
	x = np.arange(duration_ns)-duration_ns/2
	wf = np.exp(-(x/(duration_ns/4.))**2)
	return wf

waveform_gen_test (channel=2, fc=25e6, wait_time = 300, AM=True)
