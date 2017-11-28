import datetime
import time
import win32com.client as comclt
import numpy as np
import msvcrt

steps = 11 #number of steps
v_start = 0
v_stop = 1

waiting = 1 # waitcycle between steps and data acquisition (seconds)
it = 4 #integration time of spectrometer (seconds)

adwin = qt.instruments['adwin']
sweep_voltage = np.linspace(v_start,v_stop,steps)
wsh= comclt.Dispatch("WScript.Shell")

for v in sweep_voltage:
    adwin.set_dac_voltage('PI_fine_tuning',v) # setting a step with the fine piezos
    time.sleep(waiting)
    wsh.AppActivate("G300_CW640_ROI4060_F13 - LightField")
    wsh.SendKeys("{F10}")
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(it)
    time.sleep(waiting)
    if (msvcrt.kbhit() and (msvcrt.getch() == 'q')):
        print "You hit q, stopping wait time"
        break 
    print 'step', v, 'executed at', st