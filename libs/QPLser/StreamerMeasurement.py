
import numpy as np
import matplotlib.pyplot as plt
import logging
import copy

from measurements.libs.config import odmr_config as cfg_file
reload (cfg_file)

class Stream ():

	def __init__(self, logging_level = logging.WARNING):
		self.dig_outputs = {'D0':[], 'D1':[], 'D2':[], 'D3':[], 'D4':[], 'D5':[], 'D6':[], 'D7':[]}
		self.anlg_outputs = {'A0':[], 'A1':[]}
		self.pulse_stream = []
		self.dig_timers = [0,0,0,0,0,0,0,0]
		self.anlg_timers = [0,0]
		self.active_ch = None
		self.total_duration = 0

		self.logger = logging.getLogger(__name__)
		self.logger.setLevel (logging_level)

		self.ext_plot_settings = False

	def concatenate (self, stream):

		for i in np.arange(8):
			self.dig_outputs ['D'+str(i)] = self.dig_outputs ['D'+str(i)] + stream.dig_outputs ['D'+str(i)]
		for i in np.arange(2):
			self.anlg_outputs ['A'+str(i)] = self.anlg_outputs ['A'+str(i)] + stream.anlg_outputs ['A'+str(i)]
		self._update_timers()


	def clean_void_channels (self):
		self._update_timers()
		ind = np.where(self.dig_timers<1)
		print 
		for i in ind:
			self.dig_outputs['D'+str(i)] = []
		ind = np.where(self.anlg_timers<1)
		for i in ind:
			self.anlg_outputs['A'+str(i)] = []

	def add_dig_pulse (self, duration, channel):
		'''
		adds a pulse on one of the 8 digital channels (0..7)
		Duration in ns
		'''

		if (duration>0):
			go_on = True

			if ((type(channel) == int) or isinstance(channel, np.int64)):
				ch = channel
			elif ((type(channel) == str) and channel[0] == 'D'):
				ch = int(channel[1])
			else:
				print channel, ': unknown channel type', type(channel)
				go_on = False

			if go_on:
				if ((ch>=0)&(ch<=7)):
					self.dig_outputs['D'+str(ch)].append ([1, duration])
				else:
					self.logger.warning ('Specified channel does not exist!')

	def add_wait_pulse (self, duration, channel):
		"""
		adds wait time on one of the 8 digital channels (0..7)
		Duration in ns
		"""
		if (duration>0):
			go_on = True

			if (type(channel) == int):
				ch = channel
			elif ((type(channel) == str) and channel[0] == 'D'):
				ch = int(channel[1])
			else:
				print channel, ': unknown channel type', type(channel)
				go_on = False

			if go_on:
		 		if ((ch>=0)&(ch<=7)):
					self.dig_outputs['D'+str(ch)].append ([0, duration])
				else:
					self.logger.warning ('Specified channel does not exist!')

	def add_analog (self, duration, amplitude, channel):

		if (duration>0):
			go_on = True

			if (type(channel) == int):
				ch = channel
			elif ((type(channel) == str) and channel[0] == 'A'):
				ch = int(channel[1])
			else:
				print channel, ': unknown channel type', type(channel)
				go_on = False

	 		if ((ch>=0)&(ch<=1)):
				self.anlg_outputs['A'+str(ch)].append ([amplitude, duration])
			else:
				self.logger.warning ('Specified channel does not exist!')

	def add_pulse (self, duration, channel, amplitude = 1):

		if (duration>0):
			pulse_type = channel[0]
			ch = int(channel[1])

			if (pulse_type == 'D'):
				self.add_dig_pulse (duration = duration, channel = ch)
			elif (pulse_type == 'A'):
				self.add_analog (duration = duration, amplitude = amplitude, channel = ch)
			else:
				print "Pulse type unknown. Please set either digital ('D') or analog ('A')"

	def add_digital (self, value, duration, channel):
		"""
		adds value to digital channel (either 0 or 1)
		Duration in ns
		"""
		if (duration>0):
			if ((value ==0) or (value==1)):
		 		if ((channel>0)&(channel<=7)):
					self.dig_outputs['D'+str(channel)].append ([value, duration])
				else:
					self.logger.warning ('Specified channel does not exist!')


	def add_digital_stream (self, sequence, channel):
		"""
		Adds a digital sequence
		sequence is a string with pulses separated by underscore ('_')
		P = pulse ('1'), W = wait time ('0')
		the integer after P/W is the duration in ns
		example: P100_W50_P100_W200
		"""

 		if ((channel>0)&(channel<=7)):
 			try:
 				str_list = sequence.split("_")
 				for i in str_list:
 					x = i[0]
 					duration = int(i[1:])
 					if (x=='P'):
 						value = 1
 					elif (x=='W'):
 						value = 0
 					else:
 						value = -1
 						print 'Unknown value: ', i

 					if (value>-1):
 						self.dig_outputs['D'+str(channel)].append ([value, duration])
 			except:
 				self.logger.warning ('Error in sequence encoding!')			
		else:
			self.logger.warning ('Specified channel does not exist!')


	def _update_timers (self):

		'''
		Goes through all the (digital and analog) channels and calculates the total durations
		'''

		for i in np.arange(8):
			plist = self.dig_outputs ['D'+str(i)]
			self.dig_timers[i] = sum([pair[1] for pair in plist])
		for i in np.arange(2):
			plist = self.anlg_outputs ['A'+str(i)]
			self.anlg_timers[i] = sum([pair[1] for pair in plist])

	def fill_wait_time (self, channels = 'used'):
		'''
		fills all channels with zeros up to the length of the longest channel
		'''

		self._update_timers()
		max_t = self.get_max_time()

		if (channels == 'all'):
			dch = np.arange(8)
			ach = np.arange(2)
		else:
			dch = np.nonzero(self.dig_timers)[0]
			ach = np.nonzero(self.anlg_timers)[0]
		for i in dch:
			self.add_wait_pulse (duration=max_t-self.dig_timers[i], channel = 'D'+str(i))
		for i in ach:
			self.add_analog (duration=max_t-self.anlg_timers[i], channel = 'A'+str(i), amplitude = 0)


	def get_max_time (self):
		return max([max(self.dig_timers), max(self.anlg_timers)])

	def get_active_channels (self):
		'''
		Returns channel with active pulses

		Output: A, B
		A = list of non-null digital channels
		B = list of non-null analog channels
		'''

		dig = []
		anlg = []

		for i in np.arange (8):
			if (len (self.dig_outputs['D'+str(i)])>0):
				dig.append(i)
		for i in np.arange (2):
			if (len (self.anlg_outputs['A'+str(i)])>0):
				anlg.append(i)
		return dig, anlg

	def __select_active_channels (self):
		'''
		checks which channels have non-zero pulses 
		and fills with wait time to get equal channel length
		'''

		self._update_timers()
		max_t_dig = max(self.dig_timers)
		max_t_anlg = max(self.anlg_timers)
		max_t = max(max_t_anlg, max_t_dig)
		self.active_ch_dig, self.acgtive_ch_anlg = self.get_active_channels()

		self.seq_active_ch = {}
		for i in self.active_ch_dig:
			if self.dig_timers[i]<max_t:
				self.add_wait_pulse (duration=max_t-self.dig_timers[i], channel = i)
			self.seq_active_ch ['D'+str(i)] = self.dig_outputs ['D'+str(i)]

		self.seq_active_anlg_ch = {}
		for i in self.active_ch_anlg:
			if self.anlg_timers[i]<max_t:
				self.add_analog (amplitude = 0, duration=max_t-self.dig_timers[i], channel = i)
			self.seq_active_ch ['A'+str(i)] = self.anlg_outputs ['A'+str(i)]
		
		self.active_channels = self.seq_active_ch
		self.nr_active_chans = len (self.active_ch_dig) + len (self.active_ch_anlg)
		self.total_duration = max_t
		self.logger.debug ('SELECT ACTIVE CHANNELS')
		self.logger.debug ('Active chanels: '+str(self.active_ch))
		self.logger.debug ('Total durations: '+str(self.total_duration))

	def __pop_out (self):

		next_durations = np.zeros(self.nr_active_chans)
		next_values = np.zeros(self.nr_active_chans)
		ch_keys = []

		i = 0
		for k in self.active_channels.keys():
			next_durations[i] = self.active_channels[k][0][1]
			next_values[i] = self.active_channels[k][0][0]
			ch_keys.append(k)
			i += 1

		min_dur = min(next_durations)
		min_ch_key = ch_keys[np.argmin(next_durations)]

		self.logger.debug('POP-OUT --- Minimum duration: '+str(min_dur)+' at channel: '+min_ch_key)

		v = 0
		i = 0
		for k in self.active_channels.keys():
			d = next_durations[i]
			ch = int(k[1])
			v = v+(2**ch)*next_values[i]
			if (k[0]=='D'):
				if ((d-min_dur)>0):
					self.dig_outputs ['D'+str(ch)][0][1] = self.dig_outputs ['D'+str(ch)][0][1] - min_dur
				else:
					self.dig_outputs ['D'+str(ch)] = self.dig_outputs ['D'+str(ch)][1:]
			elif (k[0]=='A'):
				if ((d-min_dur)>0):
					self.anlg_outputs ['A'+str(ch)][0][1] = self.anlg_outputs ['A'+str(ch)][0][1] - min_dur
				else:
					self.anlg_outputs ['A'+str(ch)] = self.anlg_outputs ['A'+str(ch)][1:]

			i += 1


		self.total_duration = self.total_duration - min_dur
		self.logger.debug ('Pop-out value: '+str(v))
		return min_dur, int(v)

	def generate_stream (self):
		"""
		Converts the pulses in the library to a stream for the pulse streamer
		"""
		
		self._update_timers()		
		self.__select_active_channels()
		self.pulse_stream = []
		old_outs = self.dig_outputs.copy()
		while (self.total_duration>0):
			t, value = self.__pop_out()
			self.pulse_stream.append([t, value, 0, 0])

		self.dig_outputs = old_outs.copy()

		return self.pulse_stream

	def print_channels (self, channel = 'all'):
		"""
		Prints content of pulse library
		channel can be 'dig', 'anlg', 'all' or a list of channels, as in ['D0', 'A1'], etc
		"""
		if isinstance (channel, basestring):
			if (channel == 'dig'):
				print 'Digital Channels D0..D8:'
				print self.dig_outputs
			if (channel == 'anlg'):
				print 'Analog Channels A0, A1:'
				print self.anlg_outputs
			if (channel == 'all'):
				print 'Digital Channels D0..D8:'
				print self.dig_outputs
				print 'Analog Channels A0, A1:'
				print self.anlg_outputs
		elif isinstance (channel, list):
			for j in channel:
				print 'Channel: ', channel
				if (channel [0] == 'D'):
					print self.anlg_outputs[channel]
				elif (channel [0] == 'D'):
					print self.anlg_outputs[channel]
				else:
					print 'Channel unknown.'
		else:
			print 'Channel should be a list or dig/anlg/all'

	def set_plot (self, channels, labels, colors, xaxis = None):
		self.ext_plot_settings = True
		self.ch_list = channels
		self.labels_list = labels
		self.color_list = colors
		self.xaxis = xaxis

	def plot_channels (self):

		"""
		Plots waveforms loaded on digital/analog channels
		"""

		self._update_timers()
		act_dig_ch, act_anlg_ch = self.get_active_channels()

		if not(self.ext_plot_settings):
			self.ch_list = []
			colormap = plt.get_cmap('YlGnBu')
			color_list_D = [colormap(k) for k in np.linspace(0.4, 1, len(act_dig_ch))]
			for i in act_dig_ch:
				self.ch_list.append ('D'+str(i))
			colormap = plt.get_cmap('YlOrRd')
			color_list_A = [colormap(k) for k in np.linspace(0.6, 0.8, len(act_anlg_ch))]
			for i in act_anlg_ch:
				self.ch_list.append ('A'+str(i))
			self.labels_list = self.ch_list
			self.color_list = color_list_D + color_list_A

		d = int(self.get_max_time())
		offset = 2

		fig = plt.figure(figsize = (20, 8))
		ax = plt.subplot (1,1,1)
		c = 0
		
		curr_offset = 0
		tick_pos = []
		for ch in self.ch_list:
			y = np.zeros(d)
			i = 0

			if (ch[0] == 'D'):
				for j in self.dig_outputs[ch]:
					y[i:i+int(j[1])] = 0.5*int(j[0])*np.ones(int(j[1]))
					i = i + j[1]

				plt.plot (1e-3*np.arange (d), y+curr_offset*np.ones(len(y)), linewidth = 5, color = self.color_list[c])
				plt.fill_between (1e-3*np.arange (d), curr_offset, y+curr_offset*np.ones(len(y)), color = self.color_list[c], alpha=0.2)
				tick_pos.append (curr_offset)
				plt.plot (1e-3*np.arange (d), curr_offset*np.ones(len(y)), '--', linewidth = 2, color = 'gray')
				plt.plot (1e-3*np.arange (d), (0.5+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'gray')
				curr_offset += 0.5*offset

			elif (ch[0] == 'A'):
				for j in self.anlg_outputs[ch]:
					y[i:i+int(j[1])] = j[0]*np.ones(int(j[1]))
					i = i + j[1]
				curr_offset += 0.25*offset
				plt.plot (1e-3*np.arange (d), 0.75*y+curr_offset*np.ones(len(y)), linewidth = 5, color = self.color_list[c])
				plt.plot (1e-3*np.arange (d), curr_offset*np.ones(len(y)), '--', linewidth = 2, color = 'gray')
				tick_pos.append (curr_offset)
				plt.plot (1e-3*np.arange (d), (-0.75+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'r')
				plt.plot (1e-3*np.arange (d), (0.75+curr_offset)*np.ones(len(y)), ':', linewidth = 1, color = 'r')

				curr_offset += 0.5*offset

			c += 1

		ax.yaxis.set_ticks([0, len(self.labels_list)]) 
		ax.yaxis.set(ticks=tick_pos, ticklabels=self.labels_list)

		for label in (ax.get_xticklabels() + ax.get_yticklabels()):
			#label.set_fontname('Arial')
			label.set_fontsize(20)
		if self.xaxis:
			plt.xlim ([1e-3*self.xaxis[0], 1e-3*self.xaxis[1]])
		plt.xlabel ('time (us)', fontsize = 20)
		plt.ion()
		plt.show()

	def return_stream (self):
		return self.pulse_streamer_seq


class StreamSection ():

	def __init__ (self, name, idx, cfg):
		self.name = name
		self.idx = idx
		self._cfg = cfg

		# variable to store info about laser and trigger pulses
		self._lasers_in_use = []
		self._laser_channel = {}

		self._laser_pulse_ctr = 0
		self._laser_pulse_names = []
		self._laser_dict = {}

		self._trg_pulse_ctr = 0
		self._trg_pulse_names = []
		self._trg_dict = {}

		# attach sequence (StreamerSequence)
		self._rf_sequence = None
		self._pmod = False

		# variables to store sweep parameters for laser and triggers
		self._section_sweep = False #only turned to True if there is any pulse to sweep
		self._sweep_laser_pulses = []
		self._sweep_laser_par = []
		self._sweep_laser_dict = {}		
		self._sweep_trg_pulses = []
		self._sweep_trg_par = []
		self._sweep_trg_dict = {}			

	def add_laser_pulse (self, laser, duration, power, delay, channel, name = None):
		if (name == None):
			name = 's'+str(self.idx)+'_L'+str(self._laser_pulse_ctr)
		self._laser_pulse_names.append (name)
		self._laser_pulse_ctr += 1

		if (laser not in self._lasers_in_use):
			self._lasers_in_use.append(laser)
			self._laser_channel [laser] = channel

		self._laser_dict [name] = {
				'laser':	laser,
				'duration':	duration,
				'power':	power,
				'delay':	delay,
				'channel':	channel,
		}

	def add_trigger_pulse (self, delay, channel, to):
		name = 's'+str(self.idx)+'_trg'+str(self._trg_pulse_ctr)+'_'+to
		self._trg_pulse_names.append (name)
		self._trg_pulse_ctr += 1

		self._trg_dict [name] = {
				'delay':		delay,
				'channel':		channel,
				'destination':	to,
		}

	def add_rf_sequence (self, sequence, pulse_mod = False):
		self._rf_sequence = sequence
		self._pmod = pulse_mod

	def print_pulses (self):

		print '----- Section ', self.idx, ' ('+self.name+') -----'
		print 'Laser pulses: ', self._laser_pulse_names
		print 'Trigger pulses: ', self._trg_pulse_names

	def return_pulse_names (self):
		return self._laser_pulse_names, self._trg_pulse_names

	def _generate (self):
		"""
		Generates a control pulse-stream for the section, 
		based on the pulses added to the sequence
		"""

		# How can we take care of sweep parameters in repetitions?
		# I thinkt he best way may be to have a list of pulse names in a dictionary
		# and use that for a 'one-shot' replacement, like we do for the sequence
		# It may be faster to do that at Stream level, though, not at section level

		# But, at first, let's see how bad it is if we do it at a 'Section' level

		stream = Stream ()
		
		# Lasers
		#-----------------------
		for laser in self._lasers_in_use:
			stream.add_wait_pulse (duration = 10, channel = self._laser_channel[laser])

		for i in np.arange (self._laser_pulse_ctr):
			name = self._laser_pulse_names[i]
			d = self._laser_dict [name]

			stream.add_wait_pulse (duration = d['delay'], channel = d['channel'])

			stream.add_pulse (duration = d['duration'], channel = d['channel'])
			#			amplitude = d['amplitude'])

		for laser in self._lasers_in_use:
			stream.add_wait_pulse (duration = 10, channel = self._laser_channel[laser])

		# Triggers
		for i in np.arange (self._trg_pulse_ctr):
			name = self._trg_pulse_names[i]
			d = self._trg_dict [name]

			stream.add_wait_pulse (duration = d['delay'], 
							channel = d['channel'])
			#stream.add_wait_pulse (duration = self._cfg['trigger']['wait_before'], 
			#				channel = d['channel'])			
			stream.add_dig_pulse (duration = self._cfg['trigger']['duration'], 
							channel = d['channel'])
			#stream.add_wait_pulse (duration = self._cfg['trigger']['wait_after'], 
			#				channel = d['channel'])		
		# I need to decide how to upload the sequence and where to target the repetitions (alter)

		# at the end, I need to fill wait time to make the length of all channels equal
		stream.fill_wait_time ('all')
		self.stream_duration = stream.get_max_time()

		#radio_frequency sequence
		#if self._streamer_seq:
		#	self._upload_rf_sequence(delay = t)
		return stream

	def generate_stream (self, n):

		'''
		Generates stream for the Section. If sweeping, then the stream is stored in a dictionary [stream_dict],
		otherwise in a variable [stream]

		Input
		n 		[int]		number of repetitions
		'''

		print self._sweep_laser_dict
		if self._section_sweep:
			self.stream_dict = {}
			for i in np.arange(n):
				for lpname in self._sweep_laser_pulses:
					idx = self._sweep_laser_pulses.index(lpname)
					self._laser_dict[lpname][self._sweep_laser_par[idx]] = self._sweep_laser_dict[lpname][i]
				for tpname in self._sweep_trg_pulses:
					idx = self._sweep_trg_pulses.index(tpname)
					self._trg_dict[lpname][self._sweep_trg_par[idx]] = self._sweep_trg_dict[tpname][i]
				s = self._generate()
				self.stream_dict [str(i)] = s
		else:
			s = self._generate ()
			self.stream = s
					


class StreamController ():

	def __init__(self, streamer = None, logging_level = logging.INFO):

		if (streamer.__class__.__name__ == 'PulseStreamer'):		
			self.ps = streamer
			self._run_mode = True
		else:
			print 'Invalid streamer object! Entering simulation mode'
			self._run_mode = False

		self.lasers = []
		self.triggers = []
		self.laser_pulses = {}
		self.rf_sequence = None
		self.ps_seq = None 
		self._cfg = cfg_file.config
		self._streamer_channels = self._cfg['streamer_channels']
		self._awg_wait_time = 0
		self._awg_trig = False
		self._tt_trig = False
		self._streamer_seq = False
		self._init_pulse_nr = -1
		self._ro_pulse_nr = -1

		self._sections = []
		self._channels_in_use = []

		self._sweep_reps = 1

		self.logging_level = logging_level
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel (self.logging_level)

	def set_simulation_mode (self, value):
		if isinstance (value, bool):
			self._sim_mode = value
		else:
			print "Boolean value required!"

	def add_streamer (self, streamer):
		if (streamer.__class__.__name__ == 'PulseStreamer'):		
			self.ps = streamer
		else:
			print 'Invalid streamer object! Entering simulation mode'
			self._run_mode = False

	def add_sections (self, name_list):
		self._section_names = name_list
		for i in np.arange (len(self._section_names)):
			setattr (self, 'sect'+str(i), StreamSection(name = name_list[i], idx = i, cfg = self._cfg))

	def add_laser (self, name):
		"""
		Adds laser channel to the system
		name: laser name (channel must be defined in 'config' file)
		"""
		self.lasers.append (name)

	def add_laser_pulse (self, section, laser, duration, power, delay, name = None):
		"""
		Adds laser-pulse to the pulse sequence
		laser: laser name (as added earlier with 'add_laser')
		function: either 'init' or 'readout'
		duration: in ns
		power:
		delay: with respect to previous laser pulse, in ns
		"""

		if (laser in self.lasers):
			if section in self._section_names:
				idx = self._section_names.index(section)
				a = getattr (self, 'sect'+str(idx))
				ch = self._streamer_channels[laser]
				if (ch[0]=='D'):
					if (power>0):
						power = 1
				a.add_laser_pulse (laser=laser, duration=duration, power=power, 
											delay=delay, channel = ch, name = None)
				if ch not in self._channels_in_use:
					self._channels_in_use.append(ch)
				setattr (self, 'sect'+str(idx), a)

			else: 
				print 'Unknown section!'
				return None
		else:
			print 'Specified laser ('+laser+') does not exist.'

	def add_trigger (self, section, destination, delay = 10):
		"""
		Adds trigger pulse
		to: 'awg' or 'time_tagger'
		delay: in ns
		"""
		trg_name = 'trigger_'+destination


		if trg_name in self._streamer_channels:
			if trg_name not in self.triggers:
				self.triggers.append(trg_name)
			if section in self._section_names:
				idx = self._section_names.index(section)
				a = getattr (self, 'sect'+str(idx))

				ch = self._streamer_channels[trg_name]
				if (ch[0] != 'D'):
					print 'Trigger on analogue channel!'
				a.add_trigger_pulse (delay=delay, to = destination, channel  = ch)
				if ch not in self._channels_in_use:
					self._channels_in_use.append(ch)
				setattr (self, 'sect'+str(idx), a)

			else: 
				print 'Unknown section!'
				return None	
		else:
			print 'Unknown trigger name. Please make sure a channel for '+trg_name+' is defined in config file.'


	def add_rf_sequence (self, sequence, section, pulse_mod = False):
		if (sequence.__class__.__name__ == 'StreamerSequence'):		
			self.rf_sequence = sequence
		else:
			print "Invalid streamer sequence!"

		if section in self._section_names:
			idx = self._sections.index(section)
			a = getattr (self, 'sect'+str(idx))
			a = a.add_rf_sequence (sequence = sequence, pmod = pulse_mod)
			setattr (self, 'sect'+str(i), a)
		else: 
			self.logging.warning ('Unknown section!')
			return None	

	def set_AWG_wait_time (self, duration):
		self._awg_wait_time = duration

	def _upload_rf_sequence(self, delay = 0):

		# for the moment we have a for loop that converts from a dictionary
		# to the format required for the streamer
		# However, this may be too slow if we have many pulses and we may want to avoid it
		# and already format the sequence properly in libs.StreamerSequence.StreamerSequence
		# as a list of lists [ampl, duration]
		
		self.ps_seq.add_analog (duration = delay, 
								amplitude = 0, 
								channel = self._anlg_ch['I_channel'])

		self.ps_seq.add_analog (duration = delay, 
								amplitude = 0, 
								channel = self._anlg_ch['Q_channel'])

		self.ps_seq.add_digital (duration = delay, 
								value = 0, 
								channel = self._dig_ch['PM_channel'])

		for i in np.arange(self.rf_sequence.get_nr_pulses()):
			#update I waveform
			self.ps_seq.add_analog (duration = int(self.rf_sequence._Ichan['duration'][i]), 
								amplitude = self.rf_sequence._Ichan['amplitude'][i], 
								channel = self._anlg_ch['I_channel'])
			#update Q waveform
			self.ps_seq.add_analog (duration = int(self.rf_sequence._Qchan['duration'][i]), 
								amplitude = self.rf_sequence._Qchan['amplitude'][i], 
								channel = self._anlg_ch['Q_channel'])
			#update PM channel
			self.ps_seq.add_digital (duration = int(self.rf_sequence._PMchan['duration'][i]), 
								value = int(self.rf_sequence._PMchan['amplitude'][i]), 
								channel = self._dig_ch['PM_channel'])

	def set_sweep_repetitions (self, n):

		'''
		Sets number of repetitions of the pulse stream

		Input: n [int]
		'''

		self._sweep_reps = n

	def set_sweep_parameter (self, section, pulse_name, parameter, sweep_array):

		'''
		Sets pulse to be swept

		Input
		pulse_name 		[str]
		parameter 		[str] 		parameter to sweep (e.g. 'amplitude' or 'phase')
		sweep_array		[array]		array of sweep values 
		'''


		if (len(sweep_array) == self._sweep_reps):
			if section in self._section_names:
				idx = self._section_names.index(section)
				a = getattr (self, 'sect'+str(idx))

				lp, trgp = a.return_pulse_names()

				if pulse_name in lp:
						a._section_sweep = True
						a._sweep_laser_pulses.append (pulse_name)
						a._sweep_laser_par.append(parameter)
						a._sweep_laser_dict[pulse_name] = sweep_array			
				elif pulse_name in trgp:
						a._section_sweep = True
						a._sweep_trg_pulses.append (pulse_name)
						a._sweep_trg_par.append(parameter)
						a._sweep_trg_dict[pulse_name] = sweep_array			
				else:
					print "Pulse ", pulse_name, ' unknown!'
				setattr (self, 'sect'+str(idx), a)
			else: 
				print 'Unknown section!'
				return None	
		else:
			print "Length of sweep-array must match number of sweep repetitions (currently set to "+str(self._sweep_reps)+")"

	def generate_ctrl_stream (self):

		'''
		Gos through the sections and generate stream for each of them (single or repeated, 
		depending on the specific section).
		At the end, combines the streams to have a stream for each repetition
		'''

		for i in np.arange(len(self._section_names)):
			print " ****** Stream Section ", i, " ("+self._section_names[i]+")"
			x = getattr (self, 'sect'+str(i))
			x.generate_stream (self._sweep_reps)

		self._stream_dict = {}
		self._max_t = []
		for n in np.arange(self._sweep_reps):
			stream = Stream()
			for i in np.arange(len(self._section_names)):
				x = getattr (self, 'sect'+str(i))
				if x._section_sweep:
					secStr = x.stream_dict[str(n)]
				else:
					secStr = x.stream
				stream.concatenate (secStr)

			stream.clean_void_channels()
			self._stream_dict ['rep_'+str(n)] = stream
			self._max_t.append(stream.get_max_time())


	def view_stream (self, repetitions = 'all', scale_equal = True):

		if (repetitions == 'all'):
			repetitions = np.arange(self._sweep_reps)
		elif (len(repetitions) == 1):
			repetitions = [repetitions]

		#Define colors and labels for the plots
		#We use: blue (laser pulses), gray (triggers), red (RF drive pulses)
		channels = []
		labels = []
		colors = []

		col_map = plt.get_cmap('PuBu')
		c = [col_map(k) for k in np.linspace(0.4, 0.8, len(self.lasers))]
		idx = 0
		for i in self.lasers:
			labels.append (self._streamer_channels[i])
			channels.append (self._streamer_channels[i])
			colors.append (c[idx])
			idx = idx+1

		col_map = plt.get_cmap('binary')
		c = [col_map(k) for k in np.linspace(0.3, 0.6, len(self.triggers))]
		idx = 0
		for i in self.triggers:
			labels.append (self._streamer_channels[i])
			channels.append (self._streamer_channels[i])
			colors.append (c[idx])
			idx = idx+1

		'''
		if self._streamer_seq:
			labels.append ('A'+str(self._anlg_ch['I_channel']))
			labels.append ('A'+str(self._anlg_ch['Q_channel']))
			labels.append ('D'+str(self._dig_ch['PM_channel']))

			channels.extend (['A'+str(self._anlg_ch['I_channel']), 'A'+str(self._anlg_ch['Q_channel']), 
						'D'+str(self._dig_ch['PM_channel'])])
			colors.extend (['crimson', 'orangered', 'darkred'])
		'''

		if scale_equal:
			xaxis = [0, max(self._max_t)]
		else:
			xaxis = None
		for n in repetitions:
			self._stream_dict ['rep_'+str(n)].set_plot (channels=channels, labels=labels, colors=colors, xaxis=xaxis)
			self._stream_dict ['rep_'+str(n)].plot_channels()

	def run (self):
		if self._run_mode:
			self.ps.load_sequence (self.ps_stream)
		#how do I control how many runs I have? by counting trigger pulses to the time_tagger



