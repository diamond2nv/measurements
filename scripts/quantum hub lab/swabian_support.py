# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 10:47:23 2019

@author: QPL
"""
import time
import pylab as pl

import sys
sys.path.insert(0, "C:/Program Files (x86)/Swabian Instruments/Time Tagger/API/Python3.6/x64")
from measurements.instruments.TimeTagger import createTimeTagger, Counter
class SW():
    def __init__(self):
        self.dt = 0.1 # in s
        self.detID = 0
        self.running = True
    def SW_run(self):
        """Runs in own thread - reads data via Swabian box"""
        self.measure_data = pl.zeros((50,))
        try:
            self.tag = createTimeTagger()
            self.tag.setTriggerLevel(0, 0.15)
            self.tag.setTriggerLevel(1, 0.15)
            self.ctr = Counter(self.tag, [0,1], int(1e9), int(self.dt))
            while self.running:
                time.sleep(self.dt/500.)
                rates = self.ctr.getData()
                if self.detID == 0:
                    newCount = pl.mean(rates[0])*1000
                elif self.detID == 1:
                    newCount = pl.mean(rates[1])*1000
                else:
                    newCount = (pl.mean(rates[0]) + pl.mean(rates[1]))*1000
                self.measure_data[0] = newCount
                self.measure_data = pl.roll(self.measure_data, -1)
                print (self.measure_data)
                self.gotdata = True
                
        finally:
            self.ctr.stop()
            self.tag.reset()
            self.running = False


if __name__=='__main__':
    lugia = SW()
    lugia.SW_run()