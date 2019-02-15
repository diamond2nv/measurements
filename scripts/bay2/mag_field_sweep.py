# -*- coding: utf-8 -*-
"""
Created on Mon Nov 26 21:13:41 2018

@author: QPL
"""

from mag_field import mag4g
from ANC300Lib import ANC300
from LockIn7265 import LockIn7265
from NIBox import Trigger, InputCounter
import numpy as np
import time

#connecting ANC
ANC = ANC300()
Px = 4
Py = 5

#connecting DAC2
LockinAddress = r'GPIB0::12::INSTR'
dac = LockIn7265(LockinAddress)

#connecting magnetic field
field = mag4g()

#connecting APD
def init_bck():
    dt_bck = 1000 # ms
    frequency = int(np.ceil(1.0e7 / float(dt_bck)))
    trig_bck = Trigger(0, frequency)
    trig_bck.StartTask()
    ctr_bck = InputCounter(trig_bck.get_term(), ctr='1', in_port='PFI1')
    return trig_bck, ctr_bck

def count_bck(ctr_bck):
    dt_bck = 1000
    ctr_bck.data = np.zeros((10000,), dtype=np.uint32)
    ctr_bck.StartTask()
    ctr_bck.ReadCounterU32(10000, 10., ctr_bck.data, 10000, None, None)
    ctr_bck.StopTask()
    data = float((ctr_bck.data[-1])) / dt_bck * 1000
    return data

def close_bck(trig_bck, ctr_bck):
    ctr_bck.StopTask()
    ctr_bck.ClearTask()
    trig_bck.ClearTask()

def init_counter():
    dt = 20 # ms
    frequency = int(np.ceil(1.0e7 / float(dt)))
    trig = Trigger(0, frequency)
    trig.StartTask()
    counter = InputCounter(trig.get_term(), ctr='1', in_port='PFI1')
    return trig, counter

def count(counter):
    dt = 20 # ms
    counter.data = np.zeros((10000,), dtype=np.uint32)
    counter.StartTask()
    counter.ReadCounterU32(10000, 10., counter.data, 10000, None, None)
    counter.StopTask()
    data = float((counter.data[-1])) / dt * 1000
    return data

def close_counter(trig, counter):
    counter.StopTask()
    counter.ClearTask()
    trig.ClearTask()

def kill_bck(target, nClicks, attempts, vbck):
    """
    target: expected number of counts in Hz
    nClicks: number of clicks for the rotators
    attempts: number of attempts to reach the target
    vbck: bias where the background is measured
    """
    print "Cancelling the background"
    trig_bck, ctr_bck = init_bck() # initializing the counter with 1s integration time
    dac.set_DAC_voltage(output_id=2, voltage=vbck) # move to bck bias
    time.sleep(0.5) #   waiting because of the response time of the sample
    ctr0 = count_bck(ctr_bck) # first background count
    ctr1 = ctr0 # auxiliar variable
    err0 = abs(ctr0-target) # deviation from the target
    ok = False # define if continuing in the main loop
    moveXup = True # define if continuing in the moveXUp loop
    moveYup = True # define if continuing in the moveYUp loop
    i = 0 # variable compared to the number of attempts
    while not ok: # while the background is still not fine...
        if target > ctr0+ctr0**0.5: # if the background is already fine, get out of the loop
            ok = True
        else: # if the background is above the target + shotnoise
            PxOk = False # variable defining if still need to move Px
            xLimit = 3 # number of attempts for Px (this is used to stop moving Px if it cannot achieve the target)
            xi = 0 # variable compared to xLimit
            while not PxOk and not ok:
                if moveXup: # clicking Px up is defined as the first decision (line 87)
                    while moveXup:
                        ANC.stepUp(nClicks, Px) # clicking Px up
                        ctr1 = count_bck(ctr_bck) # measuring background after moving Px up
#                        print 'Px up', ctr1
                        if target > ctr1+ctr1**0.5: # get out of the loop if target is achieved
                            ok = True
                            break
                        else: # if the target is not achieved...
                            if ctr1>ctr0-ctr0**0.5 and ctr1<ctr0+ctr0**0.5: # stop moving Px if stuck in the shot noise
                                PxOk = True
                                break
                            else: # if counts changed beyond the shot noise...
                                err = abs(ctr1-target) # deviation from the target
                                if err<err0:    # improved, just continue
                                    ctr0 = ctr1 # define new reference counts
                                    err0 = err # define new deviation from target
                                else: # worse, start moving down
                                    moveXup = False
                else: # clicking Px down
                    while not moveXup:
                        ANC.stepDown(nClicks, Px) # clicking Px down
                        ctr1 = count_bck(ctr_bck) # measuring background after moving Px down
#                        print 'Px dn', ctr1
                        if target > ctr1+ctr1**0.5: # get out of the loop if target is achieved
                            ok = True
                            break
                        else: # if the target is not achieved...
                            if ctr1>ctr0-ctr0**0.5 and ctr1<ctr0+ctr0**0.5: # stop moving Px if stuck in the shot noise
                                PxOk = True
                                break
                            else: # if counts changed beyond the shot noise...
                                err = abs(ctr1-target) # deviation from the target
                                if err<err0:    # improved, just continue
                                    ctr0 = ctr1 # define new reference counts
                                    err0 = err # define new deviation from target
                                else:           # worse, move up
                                    moveXup = True
                xi+=1 # tracking number of Px attempts
                if xi>xLimit: # stop Px loop if limit of Px attempts is achieced
                    PxOk = True
            ### repeating everything for Py ###
            PyOk = False
            yLimit = 3
            yi = 0
            while not PyOk and not ok:
                if moveYup:
                    while moveYup:
                        ANC.stepUp(nClicks, Py)
                        ctr1 = count_bck(ctr_bck)
#                        print 'Py up', ctr1
                        if target > ctr1+ctr1**0.5:
                            ok = True
                            break
                        else:
                            if ctr1>ctr0-ctr0**0.5 and ctr1<ctr0+ctr0**0.5: # stop if in the shot noise
                                PyOk = True
                                break
                            else:
                                err = abs(ctr1-target)
                                if err<err0:    # improved, just continue
                                    ctr0 = ctr1
                                    err0 = err
                                else:           # worse, move down
                                    moveYup = False
                else:
                    while not moveYup:
                        ANC.stepDown(nClicks, Py)
                        ctr1 = count_bck(ctr_bck)
#                        print 'Py dn', ctr1
                        if target > ctr1+ctr1**0.5:
                            ok = True
                            break
                        else:
                            if ctr1>ctr0-ctr0**0.5 and ctr1<ctr0+ctr0**0.5: # stop if in the shot noise
                                PyOk = True
                                break
                            else:
                                err = abs(ctr1-target)
                                if err<err0:    # improved, just continue
                                    ctr0 = ctr1
                                    err0 = err
                                else:           # worse, move up
                                    moveYup = True
                yi+=1
                if yi > yLimit:
                    PyOk = True
        i+=1 # tracking the number of attemps (main loop)
        if i > attempts: # if the number of attempts is achieved, stop
            ok = True
            print "Could not reach the target."
        if ok:
            print "The background is {:.0f} Hz for Vg = {:4.3f}".format(ctr1, vbck)
    close_bck(trig_bck, ctr_bck)
    return ctr1

vi, vf, dv = (-0.65, -0.25, 0.001) # for voltage sweep
bi, bf, db = (0, 6, 0.1) # for magnetic field sweep
Bs = np.linspace(bi, bf, int((bf-bi)/db)+1)
Vs = np.linspace(vi, vf, int((vf-vi)/dv)+1)

path = 'E:/MEASUREMENTS/Ted/20181218/'
f = open(path+'magnetic_field_sweep_wlen=971_985nm.dat', 'w')
try:
    for B in Bs:
        B = np.round(B, 4)
        field.move_to(B)
        kill_bck(4000, 5, 5, -0.7)
        print "Performing detuning spectrum"
        time.sleep(0.2)
        trig, counter = init_counter()
        for v in Vs:
            dac.set_DAC_voltage(output_id=2, voltage=v)
            ctemp = count(counter)
            f.write('{:.3f}\t{:4.3f}\t{:.0f}\n'.format(B, v, ctemp))
        close_counter(trig, counter)
except:
    pass
finally:
    field.close()
    dac.close()
    ANC.close()
    f.close()