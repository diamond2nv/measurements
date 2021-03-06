from measurements.instruments import PulseStreamer82 as psLib
from measurements.instruments import RS_SMBV100A as rfLib
from measurements.libs.QPLser import ODMR_streamer as streamer_odmr
from measurements.libs.QPLser import Sequence as seq
from measurements.libs.QPLser import StreamerMeasurement as SM
import logging
from importlib import reload
import numpy as np

from measurements.instruments.Pulse_streamer_simple import PulseStreamer_simple as pss

reload(streamer_odmr)
reload(psLib)
reload (rfLib)
reload (seq)
reload (SM)

def spin_echo_sequence (time, verbose = False):

	N = 5

	s = seq.SequenceIQ()
	s.add_pulse (duration = 100, amplitude = 1, phase = 0)
	s.add_wait (duration = time)
	s.add_pulse (duration = 200, amplitude = 1, phase = 0)
	s.add_wait (duration = time)
	s.add_pulse (duration = 100, amplitude = 1, phase = 45)
	s.set_pmod ('on')
	
	s.set_sequence_repetitions (N)
	s.set_sweep_parameter (pulse_name='W0', parameter='duration', sweep_array = np.linspace (50, 1000, N))
	s.set_sweep_parameter (pulse_name='W1', parameter='duration', sweep_array = np.linspace (50, 1000, N))

	s.calculateIQ()
	return s

def test_odmr(sequence):
    ps = PulseStreamer_simple()
    strCtrl = SM.StreamController(streamer = ps)
    strCtrl.add_sections (['init', 'rf', 'readout'])
    strCtrl.print_sections()
    strCtrl.add_laser ('res_laser')
    strCtrl.add_laser_pulse (section='init',laser='res_laser', duration = 200, 
                                                 power = 0.5, delay = 0, name = 'inP')
    strCtrl.add_laser_pulse (section='readout',laser='res_laser', duration = 500, 
                                                 power = 0.5, delay = 0)
    
    
    strCtrl.add_rf_sequence (section = 'rf', sequence=sequence)
    
    strCtrl.generate_ctrl_stream()
    #strCtrl.view_stream()
    return strCtrl

if __name__ == "__main__":
    s = spin_echo_sequence(time = 1500, verbose = True)
    strCtrl = test_odmr(sequence = s)
    #strCtrl.view_stream_inline()
    #strCtrl.view()   