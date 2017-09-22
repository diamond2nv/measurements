
import numpy as np
from measurements.libs.config import odmr_config as cfg_file


class PulseSequence ():

	def __init__ (self, save_folder=None):
		self.sequence = {}
		self.ctr = 0
		self.folder = save_folder

	def add_pulse (self, pulse):
		self.sequence['P'+str(self.ctr)] = pulse
		self.ctr += 1

	def add_wait_time (self, duration):
		self.sequence['P'+str(self.ctr)] = {'type': 'wait', 'duration': duration}
		self.ctr += 1

	def save (self):
		'''
		for k in self.sequence.keys():
			if isinstance(self.sequence[k], dict):
				grp = file_handle.create_group(k)
				self.save_dict_to_file (d = d[k], file_handle = grp)
			elif (type (d[k]) in [int, float, str]):
				file_handle.attrs[k] = d[k]
			elif isinstance(d[k], np.int32):
				file_handle.attrs[k] = d[k]
			elif isinstance(d[k], np.float64):
				file_handle.attrs[k] = d[k]
			elif isinstance(d[k], np.ndarray):
				file_handle.create_dataset (k, data = d[k])	
		'''
		pass	

	def generate_sequence (self):
		'''
		Generates a sequence specific to a given implementation
		(will be defined for each polymorphic child)
		'''
		pass

	def load (self):
		pass


class Pulse ():

	def __init__ (self, duration, amplitude, phase):
		self.time_unit_ns = cfg.config['system']['time_unit_ns']
		self.duration = int(duration/self.time_unit_ns)
		self.amplitude = amplitude
		self.phase = phase



class SquarePulse (Pulse):

	def __init__ (self, duration, amplitude, phase):
		super().__init__()
		self.type = 'square'

	def generate (self):
		return self.amplitude*np.ones (self.duration)




