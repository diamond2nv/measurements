
from measurements.instruments import PulseStreamer82 as psLib
import logging
from measurements.libs import StreamerMeasurement as sm

reload(sm)
reload(psLib)

m = sm.StreamController (logging_level=logging.DEBUG)
m.add_laser ('off_res_laser')
m.add_laser ('res_laser')

m.add_laser_pulse (laser='res_laser', function='init',
				duration =300, delay = 0, power = 1)
m.add_laser_pulse (laser='off_res_laser', function='init',
				duration =200, delay = 0, power = 1)
m.add_laser_pulse (laser='res_laser', function='init',
				duration =200, delay = 100, power = 1)
m.add_trigger (to = 'awg')

m.generate_ctrl_stream()

m.view_stream()


#ps = psLib.PulseStreamer()
'''
p.add_dig_pulse (duration = 50, channel = 1)
p.add_wait_pulse (duration = 150, channel = 1)
p.add_dig_pulse (duration = 100, channel = 1)
p.print_channels()

p.add_dig_pulse (duration = 100, channel = 5)
p.add_wait_pulse (duration = 50, channel = 5)
p.add_dig_pulse (duration = 200, channel = 5)
p.print_channels()

p.add_dig_pulse (duration = 50, channel = 2)
p.print_channels()

#p.select_active_channels()
#p.print_seq()
s = p.generate_stream()
print s
p.plot_dig_channels()
'''

'''

#p.add_digital_sequence (sequence = 'P30_W100_P50_W200_P100', channel=6)

p.select_active_channels()
#p.print_seq()

p.generate_pulse_streamer_sequence()
#print 'Do we still have a sequence??'
#p.print_seq()


p.plot_digital_channels()

'''

if 0:

	ps = PulseStreamer()
	ps.set_parameters(n_runs=-1)
	#s = ps.generate_random_seq()
	ps.load_sequence(s)
	ps.stream()



