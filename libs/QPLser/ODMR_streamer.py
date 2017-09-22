
import numpy as np
import matplotlib.pyplot as plt


class pulsedODMR ():

	def __init__ (self, streamer):
		self.stream_ctrl = None
		self.RF_source = None
		self.time_tagger = None
		self.RF_sequence = None

		if (streamer.__class__.__name__ == 'PulseStreamer'):		
			self.stream_ctrl = sm.StreamController(streamer = streamer, logging_level=logging.DEBUG)
		else:
			print "Invalid streamer!"

	def add_streamer (self, streamer):
		if (streamer.__class__.__name__ == 'PulseStreamer'):		
			self.stream_ctrl = sm.StreamController(streamer = streamer, logging_level=logging.DEBUG)
		else:
			print "Invalid streamer!"

	def add_RF_source (self, RF_source):
		if (RF_source.get_instr_type() == 'RF_source'):
			self.RF_source = RF_source
		else:
			print "Invalid RF source"

	def add_laser (self, name):
		if (self.stream_ctrl == None):
			print "No streamer found! Please add a streamer to proceed"
		else:
			self.stream_ctrl.add_laser(name)

	def add_time_tagger (self, tagger):
		self.time_tagger = tagger

	def set_RF_params (self, frequency, power):
		self._RF_frq = frequency
		self._RF_pow = power

	def set_init_laser_params (self, name, power, duration, delay = 0.):
		if (self.stream_ctrl == None):
			print "Please add Streamer, first!"
		else:
			if (name in self.stream_ctrl.lasers):
				self.stream_ctrl.add_laser_pulse (laser=name, function='init', duration = duration, 
							delay = delay, power = power)
			else:
				print "Laser name unknown!"			

	def set_readout_laser_params (self, name, power, duration, delay = 0.):
		if (self.stream_ctrl == None):
			print "Please add Streamer, first!"
		else:
			if (name in self.stream_ctrl.lasers):
				self.stream_ctrl.add_laser_pulse (laser=name, function='readout', duration = duration, 
							delay = delay, power = power)
			else:
				print "Laser name unknown!"			

	def set_RF_sequence (self, delay = 0):
		self.stream_ctrl.upload_sequence 

	def view_streamer_sequence(self):
		self.stream_ctrl.view_stream()

	def run (self):
		self.stream_ctrl.add_trigger (to = 'time_tagger')
		pass

	def save(self):
		pass


class pulsedODMR_awg (pulsedODMR):

	def add_AWG(self):
		pass

