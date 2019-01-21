# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 11:42:29 2018

@author: QPL
"""

import visa
import time

rm = visa.ResourceManager()
scanner = rm.open_resource ('ASRL8::INSTR')
scanner.baud_rate = 921600
scanner.timeout = 2000
scanner.parity = visa.constants.Parity.none
scanner.stop_bits = visa.constants.StopBits.one

scanner.write('1PA0\r\n')
pos = scanner.ask ('1TP?\r\n')
print ('POS: ', pos)
error = scanner.ask ('1TS?\r\n')
print ('Error: ', error)

time.sleep(5)

n=0
while n<=5:
    n+=1
    print(n)
    print(scanner.ask('1TP\r\n'))
    print(scanner.write('1PR1\r\n'))
    time.sleep(1)

scanner.clear()
scanner.close()
