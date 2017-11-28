from measurement.panel.cav1_cav_control_panel import set_slide_p1
from measurement.panel.cav1_cav_control_panel import set_p1
import datetime
import win32com.client as comclt
import numpy as np

steps = 3 #number of steps
v_start = -2
v_stop = 10
waiting =1 # waitcycle between steps and data acquisition (seconds)
it = 5 #integration time of spectrometer (seconds)

wsh= comclt.Dispatch("WScript.Shell")

moc = qt.instruments['master_of_cavity']
sweep_voltage = np.linspace(v_start,v_stop,steps)

for v in sweep_voltage:
    moc.set_fine_piezo_voltages (v,v,v) # setting a step with the fine piezos
    time.sleep(waiting)
    wsh.AppActivate("LightField") # select application Lightfield
    wsh.SendKeys("{F10}") # send the keys you want
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(it)
    time.sleep(waiting)
    print 'step' v 'executed at' st





