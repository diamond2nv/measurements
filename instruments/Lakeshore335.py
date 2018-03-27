
import visa
import types
#import logging
#import re
#import math
#import time

class Lakeshore335():

    def __init__(self, visaAddress):
        rm = visa.ResourceManager()
        self._instr = rm.open_resource(visaAddress)
        self._instr.baud_rate = 57600
        self._instr.data_bits = 1
        self._instr.parity = visa.constants.Parity.odd
        self._instr.stop_bits = visa.constants.StopBits.one

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def id (self):
        print(self._instr.ask ('*IDN?'))

    def get_kelvin (self, channel):
        return instr.ask ('KRDG? '+str(channel))

    def close(self):
        self._instr.close()

