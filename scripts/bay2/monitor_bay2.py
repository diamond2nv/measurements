import time
import msvcrt
import getpass
from importlib import reload
from measurements.instruments import Lakeshore335 as LS335
from measurements.libs import Monitor 
reload (LS335)
reload (Monitor)


tCtrl = LS335.Lakeshore335('ASRL19::INSTR')
tCtrl.id()
t = tCtrl.get_kelvin(channel='B')
print ("Temperature: ", float(t), " kelvin")


bay2_monitor = Monitor.Monitor (bay=2, temperature_ctrl=tCtrl, wait_email=30, wait_T_readout=900)
bay2_monitor.set_max_temperature (15)
bay2_monitor.set_channel('B')
bay2_monitor.login()
bay2_monitor.start()
