
import numpy as np
import tabulate as tb

class StreamerSequence ():

	def __init__(self):
		self._seq = {}
		self._pulse_ctr = 0
		self._wait_ctr = 0
		self._ctr = 0
		self._pulse_names = []
		self._Ichan = None
		self._Qchan = None
		self._PMchan = None
		self._iq = False
		self._pmod = False

		self.nr_repetitions = 1
		self._sweep_pulses = []
		self._sweep_par = []
		self._sweep_dict = {}
		self._sequence_dict = {}

		self._iq_pm_sequence_sweep ={}


	def add_pulse (self, duration, amplitude, phase, name = None):
		'''
		adds pulse to the streamer sequence

		Input:
		duration [ns]
		amplitude
		phase [degrees]
		name = None

		If (name==None), name is automatically set as Pn, with n counting index
		'''

		if (name == None):
			name = 'P'+str(self._pulse_ctr)
		self._seq [str(self._ctr)] = {
				'name':			name,
				'type':			'pulse',
				'duration': 	duration,
				'amplitude': 	amplitude,
				'phase':		phase,
		}
		self._ctr += 1
		self._pulse_ctr += 1
		self._pulse_names.append(name)

	def add_wait (self, duration, name = None):
		'''
		adds wait time to the streamer sequence

		Input:
		duration [ns]
		name = None

		If (name==None), name is automatically set as Wn, with n counting index
		'''
		if (name == None):
			name = 'W'+str(self._wait_ctr)
		self._seq [str(self._ctr)] = {
				'name':			name,
				'type':			'wait',
				'duration': 	duration,
		}
		self._ctr += 1
		self._wait_ctr += 1
		self._pulse_names.append(name)

	def set_pmod (self, value = True):

		'''
		Turn on/off pulse modulation (value = True/'on' or False/'off')
		'''

		if ((value==True) or (value=='on')):
			self._pmod = True
		else:
			self._pmod = False

	def _copy_element (self, position):
		a = self._seq [str(position)]
		if (a['type'] == 'pulse'):
			self.add_pulse (duration = a['duration'], amplitude = a['amplitude'], phase = a['phase'])
		elif (a['type'] == 'wait'):
			self.add_wait (duration = a['duration'])

	def repeat_segment (self, first, last, nr_repetitions):

		'''
		Adds (nr_repetitions) repetitions of the element (pulses nad wait time) between (first) and (last)

		Input:
		nr_repetitions: int
		first: pulse name (ex: 'P1' or 'W3')
		last: pulse name
		'''
		if ((first in self._pulse_names) and (last in self._pulse_names)):
			i0 = self._pulse_names.index(first)
			i1 = self._pulse_names.index(last)
			for n in np.arange (nr_repetitions):
				i = i0
				while (i <= i1):
					self._copy_element (position=i)
					i += 1
		else:
			print "Any of the selected pulse names does not exist! Operation aborted."

	def get_nr_pulses (self):
		return self._ctr

	def print_sequence (self, repetition = None):
		'''
		Displays the current pulse sequence

		Input
		repetition 		[int]	default = None
		'''

		if (repetition == None): 
			seq_dict = self._seq
			rep_str = '(no reps)'
		else:
			seq_dict = self._sequence_dict['rep'+str(repetition)]
			rep_str = '(rep nr '+str(repetition)+')'

		T = [['', 'type', 'dur', 'ampl', 'phase'], ['------', '------', '------', '------', '------']]

		for i in np.arange(self._ctr):
			a = seq_dict[str(i)]
			if (a['type'] == 'pulse'):
				T.append ([i, 'P', a['duration'], a['amplitude'], a['phase']])
			else:
				T.append ([i, 'W', a['duration'], '/', '/'])

		print tb.tabulate(T, stralign='center')


	def _print_iq (self, r):

		if (r == None): 
			rep_str = '(no reps)'
			Ichan = self._Ichan
			Qchan = self._Qchan
			if self._pmod:
				PMchan = self._PMchan
		else:
			rep_str = '(rep nr '+str(r)+')'
			Ichan = self._iq_pm_sequence_sweep ['rep'+str(r)+'_I']
			Qchan = self._iq_pm_sequence_sweep ['rep'+str(r)+'_Q']
			if self._pmod:
				PMchan = self._iq_pm_sequence_sweep ['rep'+str(r)+'_PM']

		if self._pmod:
			T = [['', 'I ampl', 'I dur', 'Q ampl', 'Q dur', 'PM', 'PM dur'], ['------', '------', '------', '------', '------', '------', '------']]
			for i in np.arange(self._ctr):
				T.append ([i, int(100*Ichan['amplitude'][i])/100., int(Ichan['duration'][i]),
						int(100*Qchan['amplitude'][i])/100., int(Qchan['duration'][i]),
						PMchan['amplitude'][i], int(PMchan['duration'][i])])
		else:
			T = [['', 'I ampl', 'I dur', 'Q ampl', 'Q dur'], ['------', '------', '------', '------', '------']]
			for i in np.arange(self._ctr):
				T.append ([i, int(100*Ichan['amplitude'][i])/100., int(Ichan['duration'][i]),
						int(100*Qchan['amplitude'][i])/100., int(Qchan['duration'][i])])
		
		print
		print '******** Sequence - IQ '+rep_str+'********'
		print tb.tabulate(T, stralign='center')

	def print_IQ (self, repetition = None):

		'''
		Display the current I, Q and pulse modulation (PM) channels of the pulse sequence

		Input
		repetition 		[int]	default = None, value can be int or 'all'
		'''

		if (repetition == None):
			self._print_iq (None)
		elif (repetition != 'all'):
			self._print_iq (repetition)
		else:
			for r in np.arange(self.nr_repetitions):
				self._print_iq (r)
			

	def _calculate_IQ (self, repetition = None):

		Ichan = {
			'amplitude':	np.zeros(self._ctr),
			'duration':		np.zeros(self._ctr)
		}
		
		Qchan = {
			'amplitude':	np.zeros(self._ctr),
			'duration':		np.zeros(self._ctr)
		}

		if (repetition == None): 
			seq_dict = self._seq
		else:
			seq_dict = self._sequence_dict['rep'+str(repetition)]

		for i in np.arange(self._ctr):
			a = seq_dict[str(i)]
			if (a['type' ] == 'pulse'):
				Ichan['amplitude'][i] = a['amplitude']*np.cos(a['phase']*np.pi/180.)
				Ichan['duration'][i] = a['duration']
				Qchan['amplitude'][i] = a['amplitude']*np.sin(a['phase']*np.pi/180.)
				Qchan['duration'][i] = a['duration']
			else:
				Ichan['amplitude'][i] = 0
				Ichan['duration'][i] = a['duration']
				Qchan['amplitude'][i] = 0
				Qchan['duration'][i] = a['duration']

		return Ichan, Qchan

	def _calculate_PM (self, repetition=None, offset = 10):
		'''
		Calculates the digital pulse modulation channel 
		'''
			
		PMchan = {
			'amplitude':	np.zeros(self._ctr),
			'duration':		np.zeros(self._ctr),
		}

		if (repetition == None): 
			seq_dict = self._seq
		else:
			seq_dict = self._sequence_dict['rep'+str(repetition)]

		for i in np.arange(self._ctr):
			a = seq_dict [str(i)]
			if (a['type'] == 'pulse'):
				PMchan['amplitude'][i] = 1
			else:
				PMchan['amplitude'][i] = 0
			
			PMchan['duration'][i] = a['duration']

		prev_pulse = 0
		for i in np.arange(self._ctr):

			a = seq_dict[str(i)]

			if (a['type'] == 'pulse'):
				if (i>0):
					PMchan['duration'][i-1] = PMchan['duration'][i-1] - offset
					PMchan['duration'][i] = PMchan['duration'][i] + offset
				if (i<self._ctr-1):
					PMchan['duration'][i+1] = PMchan['duration'][i+1] - offset
					PMchan['duration'][i] = PMchan['duration'][i] + offset

		return PMchan


	def _calculate_IQ_sequence (self, offset = 10):
		'''
		Calculates the IQ (and PM) channels for the current pulse sequence (including all repetitions, if relevant)
		'''

		if (self._sequence_dict == {}):
			self._Ichan, self._Qchan = self._calculate_IQ ()
			if self._pmod:
				self._PMchan = self._calculate_PM (offset = offset)
		else:
			for r in np.arange(self.nr_repetitions):
				I, Q = self._calculate_IQ (r)
				self._iq_pm_sequence_sweep ['rep'+str(r)+'_I'] = {'amplitude': np.copy(I['amplitude']), 
																	'duration': np.copy(I['duration'])}
				self._iq_pm_sequence_sweep ['rep'+str(r)+'_Q'] = {'amplitude': np.copy(Q['amplitude']), 
																	'duration': np.copy(Q['duration'])}
				if self._pmod:
					PM = self._calculate_PM (r, offset = offset)
					self._iq_pm_sequence_sweep ['rep'+str(r)+'_PM'] = {'amplitude': np.copy(PM['amplitude']), 
																		'duration': np.copy(PM['duration'])}


	def set_sequence_repetitions (self, n):

		'''
		Sets number of sequence repetitions

		Input: n [int]
		'''
		if (n>1):
			self.nr_repetitions = n

	def set_sweep_parameter (self, pulse_name, parameter, sweep_array):

		'''
		Sets pulse to be swept

		Input
		pulse_name 		[str]
		parameter 		[str] 		parameter to sweep (e.g. 'amplitude' or 'phase')
		sweep_array		[array]		array of sweep values 
		'''

		print "Pulse names: ", self._pulse_names
		if pulse_name in self._pulse_names:
			if (len(sweep_array) == self.nr_repetitions):
				self._sweep_pulses.append (pulse_name)
				self._sweep_par.append(parameter)
				self._sweep_dict[pulse_name] = sweep_array
			else:
				print "Length of sweep_array should be: ", self.nr_repetitions, "instead of ", len (sweep_array)
		else:
			print "Pulse ", pulse_name, " does not exist."

	def calculateIQ (self):

		if ((self.nr_repetitions > 0)):

			# deep-copy of nr_repetitions copy of self._seq dictionary 
			for r in np.arange (self.nr_repetitions):
				self._sequence_dict ['rep'+str(r)] = {}

				for j in np.arange(self._ctr):
					self._sequence_dict ['rep'+str(r)] [str(j)] = self._seq[str(j)].copy()

			# modify instances according to sweep specifications
			for j in np.arange(len(self._sweep_pulses)):
				pname = self._sweep_pulses[j]
				prop = self._sweep_par[j]
				ind = self._pulse_names.index(pname)

				for r in np.arange (self.nr_repetitions):
					self._sequence_dict ['rep'+str(r)][str(ind)][prop] = self._sweep_dict[pname][r]
		
			self._calculate_IQ_sequence()

		else:
			print "Nothing to sweep."

