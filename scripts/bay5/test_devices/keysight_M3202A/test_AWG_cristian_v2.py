
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



def waveform_gen_test (channel=0, fc = 50e6, wait_time=10, repeat_cycle = 0, load_waveforms = False):

	#set carrier cos(2pi fc t + phi)
	A = 0.
	AWGobj.channelAmplitude(channel, A)
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_SINUSOIDAL)
	AWGobj.channelFrequency(channel, fc)

	G = 0.5 #modulation gain
	#load modulating waveform AWG[t]

	if load_waveforms:
		wf_gauss = ks.SD_Wave()
		wf_gauss.newFromArrayDouble (waveformType = 0, waveformDataA = gaussian_pulse(50))
		wf_wait = ks.SD_Wave()
		wf_wait.newFromArrayDouble (waveformType = 0, waveformDataA = np.zeros(wait_time))
		wf_rect = ks.SD_Wave()
		wf_rect.newFromArrayDouble (waveformType = 0, waveformDataA = np.ones(50))

		AWGobj.waveformFlush() 
		AWGobj.AWGflush(0)
		AWGobj.waveformLoad(wf_gauss, 0); 
		AWGobj.waveformLoad(wf_wait, 1); 
		AWGobj.waveformLoad(wf_rect, 2); 

	AWGobj.modulationAmplitudeConfig (channel, 1, G)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=2, triggerMode=0, startDelay=0, cycles=2, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=1, triggerMode=0, startDelay=0, cycles=3, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	AWGobj.AWGqueueWaveform(nAWG=0, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0)
	
	AWGobj.AWGqueueConfig (nAWG=0, mode=repeat_cycle)

	print 'AWG start...'
	AWGobj.AWGstart(0)
	time.sleep(5)
	AWGobj.AWGstop(0)
	print 'AWG stop...'
	AWGobj.waveformFlush()
	
	
	AWGobj.channelWaveShape(channel, ks.SD_Waveshapes.AOU_OFF)
	AWGobj.AWGqueueConfig (nAWG=0, mode=0)
	AWGobj.AWGstart(0)
	AWGobj.AWGstop(0)
	
	AWGobj.AWGflush(0)
	
	AWGobj.close()

def gaussian_pulse (duration_ns):
	x = np.arange(duration_ns)-duration_ns/2
	wf = np.exp(-(x/(duration_ns/4.))**2)
	return wf

waveform_gen_test (fc=100e6, wait_time = 100, repeat_cycle=1, load_waveforms=False)
