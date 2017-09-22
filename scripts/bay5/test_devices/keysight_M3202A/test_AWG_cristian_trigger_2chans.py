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


def spin_echo_wf (wait_time):
	wf_pi = square_pulse(200)
	wf_echo = np.hstack ((np.zeros(wait_time), wf_pi, np.zeros(wait_time)))
	print np.shape(wf_echo)
	plt.plot (wf_echo)
	plt.axis([-20, len(wf_echo)+20, -0.1, 1.1])
	plt.show()
	return wf_echo

def waveform_gen_test (ch1=0, ch2=2, fc = 50e6, phase = 0, wait_time=10, AM=False):

	#configuring trigger
	AWGobj.triggerIOconfig (direction = ks.SD_TriggerDirections.AOU_TRG_IN, 
					syncMode = ks.SD_SyncModes.SYNC_CLK10)
	AWGobj.AWGtriggerExternalConfig (nAWG=ch1, externalSource=ks.SD_TriggerExternalSources.TRIGGER_EXTERN, 
					triggerBehavior=ks.SD_TriggerBehaviors.TRIGGER_RISE)
	AWGobj.AWGtriggerExternalConfig (nAWG=ch2, externalSource=ks.SD_TriggerExternalSources.TRIGGER_EXTERN, 
					triggerBehavior=ks.SD_TriggerBehaviors.TRIGGER_RISE)

	for i in [ch1, ch2]:
		print 'Config ch. ',i
		if AM:
			A = 0.
			AWGobj.channelAmplitude(i, A)
			AWGobj.channelWaveShape(i, ks.SD_Waveshapes.AOU_SINUSOIDAL)
			AWGobj.channelFrequency(i, fc)
			G = 0.25 #modulation gain
			AWGobj.modulationAmplitudeConfig (i, 1, G)
		else:
			AWGobj.channelAmplitude(i, .3)
			AWGobj.channelWaveShape(i, ks.SD_Waveshapes.AOU_AWG)
			AWGobj.modulationAmplitudeConfig (i, 1, 0)
			#AWGobj.
		AWGobj.AWGflush(i)

	AWGobj.channelPhase (0, 0)
	AWGobj.channelPhase (2, 90)


	wf_gauss = ks.SD_Wave()
	wf_gauss.newFromArrayDouble (waveformType = 0, waveformDataA = gaussian_pulse(200))
	wf_wait = ks.SD_Wave()
	wf_wait.newFromArrayDouble (waveformType = 0, waveformDataA = np.zeros(wait_time))
	wf_rect = ks.SD_Wave()
	wf_rect.newFromArrayDouble (waveformType = 0, waveformDataA = square_pulse(150))

	AWGobj.waveformFlush() 
	AWGobj.waveformLoad(wf_gauss, 0); 
	AWGobj.waveformLoad(wf_wait, 1); 
	AWGobj.waveformLoad(wf_rect, 2); 

	#trigger mode: 0 = Auto, 2: external, 6: external-cyclic
	#AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=0, triggerMode=2, startDelay=0, cycles=2, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=0, triggerMode=2, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=5, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=5, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=5, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=7, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=5, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=10, prescaler=0)
	#AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)

	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=0, triggerMode=2, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)

	AWGobj.AWGqueueConfig (nAWG=ch1, mode=1)
	AWGobj.AWGqueueConfig (nAWG=ch2, mode=1)

	ch_mask = 0xF#2**ch1+2**ch2
	print 'AWG start...'
	AWGobj.AWGstartMultiple(ch_mask)
	time.sleep(50)
	AWGobj.AWGstopMultiple(ch_mask)
	print 'AWG stop...'
	AWGobj.waveformFlush()
	
	'''
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_OFF)
	AWGobj.AWGqueueConfig (nAWG=channel, mode=0)
	AWGobj.AWGstart(channel)
	AWGobj.AWGstop(channel)
	'''

	AWGobj.AWGflush(ch1)
	AWGobj.AWGflush(ch2)
	AWGobj.close()

def gaussian_pulse (duration_ns):
	x = np.arange(duration_ns)-duration_ns/2
	wf = np.exp(-(x/(duration_ns/4.))**2)
	return wf

def square_pulse (duration_ns):
	#x = np.arange(duration_ns)-duration_ns/2
	#wf = 0.9*np.exp(-(x/(2.*duration_ns))**2)
	wf = 1.*np.ones (duration_ns)
	#wf[:20] = 0*np.ones(20)
	#wf[-20:] = 0
	return wf

def spin_echo_test (ch1=0, ch2=2, fc = 50e6, AM=False):

	#configuring trigger
	AWGobj.triggerIOconfig (direction = ks.SD_TriggerDirections.AOU_TRG_IN, 
					syncMode = ks.SD_SyncModes.SYNC_CLK10)
	AWGobj.AWGtriggerExternalConfig (nAWG=ch1, externalSource=ks.SD_TriggerExternalSources.TRIGGER_EXTERN, 
					triggerBehavior=ks.SD_TriggerBehaviors.TRIGGER_RISE)
	AWGobj.AWGtriggerExternalConfig (nAWG=ch2, externalSource=ks.SD_TriggerExternalSources.TRIGGER_EXTERN, 
					triggerBehavior=ks.SD_TriggerBehaviors.TRIGGER_RISE)

	for i in [ch1, ch2]:
		print 'Config ch. ',i
		if AM:
			A = 0.
			AWGobj.channelAmplitude(i, A)
			AWGobj.channelWaveShape(i, ks.SD_Waveshapes.AOU_SINUSOIDAL)
			AWGobj.channelFrequency(i, fc)
			G = 0.25 #modulation gain
			AWGobj.modulationAmplitudeConfig (i, 1, G)
		else:
			AWGobj.channelAmplitude(i, .3)
			AWGobj.channelWaveShape(i, ks.SD_Waveshapes.AOU_AWG)
			AWGobj.modulationAmplitudeConfig (i, 1, 0)
			#AWGobj.
		AWGobj.AWGflush(i)

	AWGobj.channelPhase (ch1, 0)
	AWGobj.channelPhase (ch2, 90)


	wf_echo = ks.SD_Wave()
	wf_echo.newFromArrayDouble (waveformType = 0, waveformDataA = spin_echo_wf (1000))
	wf_pi2 = ks.SD_Wave()
	wf_pi2.newFromArrayDouble (waveformType = 0, waveformDataA = square_pulse(100))
	wf_wait = ks.SD_Wave()
	wf_wait.newFromArrayDouble (waveformType = 0, waveformDataA = np.zeros(50))

	AWGobj.waveformFlush() 
	AWGobj.waveformLoad(wf_pi2, 0); 
	AWGobj.waveformLoad(wf_echo, 1); 
	AWGobj.waveformLoad(wf_wait, 2); 

	#trigger mode: 0 = Auto, 2: external, 6: external-cyclic
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=2, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=400, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)

	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=2, triggerMode=2, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=1, triggerMode=0, startDelay=0, cycles=5, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=ch2, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)

	AWGobj.AWGqueueConfig (nAWG=ch1, mode=1)
	AWGobj.AWGqueueConfig (nAWG=ch2, mode=1)

	ch_mask = 0xF#2**ch1+2**ch2
	print 'AWG start...'
	AWGobj.AWGstartMultiple(ch_mask)
	time.sleep(20)
	AWGobj.AWGstopMultiple(ch_mask)
	print 'AWG stop...'
	AWGobj.waveformFlush()
	
	
	AWGobj.channelWaveShape(ch1, ks.SD_Waveshapes.AOU_OFF)
	AWGobj.AWGqueueConfig (nAWG=ch1, mode=0)
	AWGobj.AWGstart(ch1)
	AWGobj.AWGstop(ch1)
	

	AWGobj.AWGflush(ch1)
	AWGobj.AWGflush(ch2)
	AWGobj.close()



waveform_gen_test (ch1=0, ch2=2, fc=20e6, phase=90,wait_time = 160, AM=True)
#spin_echo_test (ch1=0, ch2=2, fc=20e6, AM=False)
