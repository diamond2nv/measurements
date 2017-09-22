
from measurements.instruments import PulseStreamer82 as psLib
from measurements.instruments import RS_SMBV100A as rfLib
import logging
from measurements.libs import ODMR_streamer as streamer_odmr
from measurements.libs import StreamerSequence as seq
from measurements.libs import StreamerMeasurement as SM

reload(streamer_odmr)
reload(psLib)
reload (rfLib)
reload (seq)
reload (SM)


def spin_echo_sequence (time, verbose = False):

	s = seq.StreamerSequence()
	s.add_pulse (duration = 100, amplitude = 1, phase = 0)
	s.add_wait (duration = time)
	s.add_pulse (duration = 200, amplitude = 1, phase = 0)
	s.add_wait (duration = time)
	s.add_pulse (duration = 100, amplitude = 1, phase = 45)
	s.set_pmod ('on')
	
	s.calculate_IQ_sequence()
	if verbose:
		s.print_sequence()
		s.print_IQ()

	return s


def test_odmr(sequence):
	strCtrl = SM.StreamController ()
	strCtrl.add_sections (['init', 'rf', 'readout'])
	strCtrl.add_laser ('res_laser')
	strCtrl.add_laser_pulse (section='init',laser='res_laser', duration = 200, 
	                                             power = 0.5, delay = 0, name = 'inP')
	strCtrl.add_rf_sequence (section = 'rf', sequence=sequence)
	strCtrl.add_laser_pulse (section='readout',laser='res_laser', duration = 500, 
	                                             power = 0.5, delay = 0)

	strCtrl.generate_ctrl_stream()
	strCtrl.view_stream()
	
#test_repeated_sweep()
s = spin_echo_sequence(time = 1500, verbose = True)
test_odmr (sequence = s)