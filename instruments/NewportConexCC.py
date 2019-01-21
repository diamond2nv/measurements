-*- coding: utf-8 -*-
"""
Created on Thu Nov 22 11:42:29 2018

@author: QPL
"""

#range<12 mm -0.001 accuracy
#min increment move = 0.1 µm

import visa
import time


#scanner.write('1PA0\r\n')
#pos = scanner.ask ('1TP?\r\n')
#print ('POS: ', pos)
#error = scanner.ask ('1TS?\r\n')
#print ('Error: ', error)
#
#time.sleep(5)
#
#n=0
#while n<=5:
#    n+=1
#    print(n)
#    print(scanner.ask('1TP\r\n'))
#    print(scanner.write('1PR0.0001\r\n'))
#    time.sleep(1)
    
I=[0]

class NewportConexCC:
    
    def __init__(self, address):
        self.rm = visa.ResourceManager()
        self.scanner = self.rm.open_resource (address)
        self.scanner.baud_rate = 921600
        self.scanner.timeout = 2000
        self.scanner.parity = visa.constants.Parity.none
        self.scanner.stop_bits = visa.constants.StopBits.one

    def move_absolute (self, position):     #works
        self.scanner.write('1PA'+str(position))

    def move_relative (self, distance):    #works
        self.scanner.write('1PR'+str(distance))

    def get_position (self):
#        self.scanner.ask('1TP')
        I=self.scanner.ask('1TP')
        Pos = float(I[3:])
        return Pos
        
    
    def reset (self):    #works
        self.scanner.write('1RS')
        time.sleep(5)
        self.scanner.write('1OR')
    
    def close(self):    #works
        self.scanner.clear()
        self.scanner.close()



scanner1 = Scanner (address = 'ASRL8::INSTR')
scanner1.move_relative(distance=0.001)     #move r in mm
#scanner1.move_absolute(position=0.005)     #move a
#time.sleep(0.1)

#p=scanner1.get_position()
#print(p)

#print(scanner1.scanner.ask('1TS'))     #error
#scanner1.close()


