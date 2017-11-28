import datetime
import time
import win32com.client as comclt
import numpy as np
import msvcrt

steps = 51 #number of steps
v_start = 0
v_stop = 10

waiting = 1 # waitcycle between steps and data acquisition (seconds)
it = 2 #integration time of spectrometer (seconds) #not

moc = qt.instruments['master_of_cavity']
sweep_voltage = np.linspace(v_start,v_stop,steps)
wsh= comclt.Dispatch("WScript.Shell")

for v in sweep_voltage:
    moc.set_fine_piezo_voltages (v,v,v) # setting a step with the fine piezos
    time.sleep(2*waiting)
    print 'activating lightfield'
    wsh.AppActivate("Untitled Experiment - LightField")
    wsh.SendKeys("{F10}")
    print 'measurement started'
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(it)
    time.sleep(waiting)
    if (msvcrt.kbhit() and (msvcrt.getch() == 'q')):
        print "You hit q, stopping wait time"
        break 
    print 'step', v, 'executed at', st





