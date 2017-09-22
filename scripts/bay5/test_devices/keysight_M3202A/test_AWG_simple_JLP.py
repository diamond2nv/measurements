
#Test code provided by Jose Luis Preciado (Signadyne/Keysight)

import sys; 
import os;
import time;

sys.path.append ('C:\Research\measurements\libs')
sys.path.append(os.path.abspath("C:/Program Files (x86)/Signadyne/Libraries/Python"));
import keysightSD1 as signadyne;

class testSimple :
	wave = signadyne.SD_Wave();
	card = signadyne.SD_AOU();

	def burstexample(self):
		waveformFile = ['', '', '']
		waveformFile[0] = os.path.join(path_noisefiles, 'Signadyne/AWGN_A.csv')
		print waveformFile[0]
		waveformFile[1] = os.path.join(path_noisefiles, 'Signadyne/AWGN_B.csv')
		waveformFile[2] = os.path.join(path_noisefiles, 'Signadyne/AWGN_C.csv')
		# Create waveforms objects in PC RAM from waveforms files
		print(self.card.waveformFlush())
		print('wave0')
		print(self.wave.newFromFile(waveformFile[0]))
		print(self.card.waveformLoad(self.wave, 0))
		print('wave1')
		print(self.wave.newFromFile(waveformFile[1]))
		print(self.card.waveformLoad(self.wave, 1))
		print('wave2')
		print(self.wave.newFromFile(waveformFile[2]))
		print(self.card.waveformLoad(self.wave, 2))
		print('Channel')
		print(self.card.channelWaveShape(nChannel=1, waveShape=6))
		print(self.card.channelAmplitude(nChannel=1, amplitude=1.5))
		print('queues')
		print(self.card.AWGflush(1))
		print(self.card.AWGqueueWaveform(nAWG=1, waveformNumber=0, triggerMode=0, startDelay=0, cycles=1, prescaler=0))
		print(self.card.AWGqueueWaveform(nAWG=1, waveformNumber=1, triggerMode=0, startDelay=0, cycles=1, prescaler=0))
		print(self.card.AWGqueueWaveform(nAWG=1, waveformNumber=2, triggerMode=0, startDelay=0, cycles=1, prescaler=0))
		print('queueConfig',self.card.AWGqueueConfig(nAWG=1, mode=1))
		time.sleep(2)
		print('AWGstart',self.card.AWGstart(nAWG=1))
		return (True, "No Error")

path_noisefiles = 'Z:/Software_Local/Issue_ProcessFlow';

obj = testSimple()

obj.card.openWithSlot('',1,4)
obj.burstexample()
