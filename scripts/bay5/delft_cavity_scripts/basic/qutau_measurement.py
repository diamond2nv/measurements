import qt
import msvcrt
import time
import datetime
import scipy
import numpy as np


_qutau_counter = qt.instruments['qutau_counter']
_green_aom = qt.instruments['GreenAOM']
_pulse_aom = qt.instruments['PulseAOM']

def qutau_msmt(roi_min,roi_max,integration_time=1,dt=10,msmt_type=''):

    print 'running %s measurement using the qutau'%(msmt_type)
    _qutau_counter.set_roi_min(roi_min)
    _qutau_counter.set_roi_max(roi_max)
    _qutau_counter.set_integration_time(integration_time)

    # Suggested by Wouter, 3 may 2017 (maybe in qutau_simple_counter)
    # qutau.switch_termination(True)
    # qutau.set_active_channels([1 2])

    if msmt_type == 'lifetime':
        pass
        #_pulse_aom.turn_on()
    elif msmt_type ==  'HBT':
        green_power = 800e-6
        _green_aom.set_power(green_power)
        print 'green power is ', int(green_power*1e6), 'uW'


    print 'current time:', datetime.datetime.now()
    print 'total time to run is ', dt ,'s'

    _qutau_counter.start()
    qt.msleep(0.05)
    t0 = time.time()

    # print time.time()
    while time.time()<t0+dt:
        qt.msleep(1)
        #print time.time()
        if (msvcrt.kbhit() and (msvcrt.getch()=='q')):
            break

    _qutau_counter.stop() 


    qt.msleep(0.1)
    # print 'running',_qutau_counter.get_is_running()
    _qutau_counter.plot_last_histogram()

    qt.msleep(0.1)
    _qutau_counter.save_last_histogram(msmt_type)
    # print .HDF5Data(name=msmt_type)


if __name__=='__main__':
    #lifetime measurement: 
    qutau_msmt(500,700,dt=2,msmt_type='lifetime')
    #HBT:
    # qutau_msmt(35,500,dt=200,msmt_type='HBT')