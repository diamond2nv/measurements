import time
import msvcrt
import getpass
from importlib import reload
from measurements.instruments import Lakeshore335 as LS335
from measurements.libs import Monitor 
reload (LS335)
reload (Monitor)
bay2_monitor = Monitor.Monitor (bay=2)
bay2_monitor.login()
bay2_monitor.start()





#email.send_mail(to='m.brotons_i_gisbert@hw.ac.uk', subject='Greetings!', message='The python code for sending emails works :)')

