
from measurements.instruments import PulseStreamer82 as psLib
from measurements.instruments import RS_SMBV100A as rfLib
import logging
from measurements.libs.QPLser import ODMR_streamer as streamer_odmr
from measurements.libs.QPLser import Sequence as seq
from measurements.libs.QPLser import StreamerMeasurement as SM
from importlib import reload

reload(streamer_odmr)
reload(psLib)
reload (rfLib)
reload (seq)
reload (SM)

def spin_echo_sequence ():
	s = seq.SequenceIQ()
	s.add_pulse (duration = 100, amplitude = 1, phase = 0)
	s.add_wait (duration = 500)
	s.add_pulse (duration = 200, amplitude = 1, phase = 0)
	s.add_wait (duration = 500)
	s.add_pulse (duration = 100, amplitude = 1, phase = 45)
	s.set_pmod ('on')
	s.print_sequence()

	#s.set_sequence_repetitions(10)
	#s.set_sweep_parameter ('P3', 'phase', np.linspace (0,90,10))
	#s.calculate_repetition_dictionary()

	s.calculateIQ ()
	#s.print_IQ (2)

	return s

strCtrl = SM.StreamController ()
strCtrl.add_sections (['init', 'rf', 'readout'])
strCtrl.print_sections()
strCtrl.add_laser ('res_laser')
strCtrl.add_laser_pulse (section='init',laser='res_laser', duration = 200, 
                                             power = 0.5, delay = 0, name = 'inP')
strCtrl.add_trigger (section = 'rf', destination = 'awg', delay = 0)

s = spin_echo_sequence()
strCtrl.add_rf_sequence (section = 'rf', sequence = s)
strCtrl.add_laser_pulse (section='readout',laser='res_laser', duration = 500, 
                                             power = 0.5, delay = 0)

strCtrl.set_sweep_repetitions (n=3)
swArr = [100, 300, 500]
strCtrl.set_sweep_parameter (section = 'init', pulse_name = 'inP', 
                                 parameter = 'duration', sweep_array = swArr)
strCtrl.generate_ctrl_stream()
#strCtrl._stream_dict['rep_0'].plot_channels()
#strCtrl._stream_dict['rep_1'].plot_channels()
#strCtrl._stream_dict['rep_2'].plot_channels()
strCtrl.view_stream_inline()




