import time
import msvcrt
import getpass
from importlib import reload
from measurements.instruments import Lakeshore335 as LS335
from measurements.libs import Monitor 
reload (LS335)
reload (Monitor)

bay2_monitor = Monitor.TemperatureMonitor (bay=2, wait_email = 6, wait_T_readout = 15)
bay2_monitor.set_max_temperature(10)
bay2_monitor.login()
bay2_monitor.start()
