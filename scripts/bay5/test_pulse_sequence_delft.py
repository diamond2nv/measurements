import numpy as np
from measurements.libs.delft import pulse
from measurements.libs.delft import pulselib
from measurements.libs.delft import element
from measurements.libs.delft import view

reload(pulse)
reload(element)
reload(view)
reload(pulselib)

e = element.Element('sequence_element', clock=1e9, min_samples=0)
e.define_channel('MW_Imod')
e.define_channel('MW_Qmod')
e.define_channel('MW_pulsemod')

X1 = pulselib.MW_IQmod_pulse('pi2_pulse', 
	I_channel='MW_Imod', Q_channel='MW_Qmod', 
	PM_channel='MW_pulsemod',
	frequency = 30e6,
	amplitude = 1.,
	length = 50e-9,
	phase = 0,
	PM_risetime = 5e-9,
	phaselock = False)

X2 = pulselib.MW_IQmod_pulse('pi2_pulse', 
	I_channel='MW_Imod', Q_channel='MW_Qmod', 
	PM_channel='MW_pulsemod',
	frequency = 30e6,
	amplitude = 1.,
	length = 50e-9,
	phase = 0,
	PM_risetime = 5e-9,
	phaselock = True)

T = pulse.SquarePulse(channel='MW_Imod', name='delay',
    length = 35e-9, amplitude = 0.)


e.append(X1)
e.append(T)
e.append(X2)
#e.print_overview()
print e.next_pulse_time('MW_Imod')*1e9, e.next_pulse_time('MW_Qmod')*1e9, \
    e.next_pulse_time('MW_pulsemod')*1e9

view.show_element(e)
#view.show_wf
