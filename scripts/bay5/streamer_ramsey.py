from measurements.instruments import PulseStreamer82 as psLib
from measurements.instruments import RS_SMBV100A as rfLib
import logging
from measurements.libs.QPLser import ODMR_streamer as streamer_odmr
from measurements.libs.QPLser import Sequence as seq
from measurements.libs.QPLser import StreamerMeasurement as SM
from importlib import reload
from measurements.instruments.Pulse_streamer_simple import PulseStreamer_simple
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


if __name__ == "__main__":
    ps = PulseStreamer_simple()
    strCtrl = SM.StreamController (streamer = ps)
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
    swArr = [100, 300, 500]
    strCtrl.set_sweep_repetitions (n=len(swArr)) # causes error if not same as 'number of repetitions in stream'(?) == 1
    
    strCtrl.set_sweep_parameter (section = 'init', pulse_name = 'inP', 
                                     parameter = 'duration', sweep_array = swArr)
    strCtrl.generate_ctrl_stream()
    
    doutr1 = strCtrl._stream_dict['rep_1'].dig_outputs
    aout = strCtrl.sect1.stream.anlg_outputs
    dout = strCtrl.sect1.stream.dig_outputs
    #strCtrl.view_stream_inline()