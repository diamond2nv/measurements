# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 16:51:51 2017

@author: Raphael Proux

Library to control the Solstis laser from MSquared. 
Based on an example from Msquared (for the Firefly)
"""

import socket
import json
import time

class SolstisError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class SolstisLaser():

    TUNING_NOT_ACTIVE = 0
    NO_LINK_TO_WAVEMETER = 1
    TUNING_IN_PROGRESS = 2
    WAVELENGTH_MAINTAINED = 3

    def __init__(self, laser_ip_address, pc_ip_address, port_number=39933, transmission_id=0):
        self._address = laser_ip_address # Ip address of the Solstis
        self._pc_ip = pc_ip_address  # ip-address of the pc
        self._port = port_number
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._transmission_id = transmission_id
        self._connection = False
        
        self.wavelength_current = -1
        self.wavelength_to_go = -1

        try:
            # The raw socket connection
            self._s.connect((self._address,self._port))
        except Exception as e:
            print('Something went wrong: '+str(e))

        # prepare the 'start_link' message
        message_dict = dict()
        message_dict["op"] = "start_link"
        message_dict["parameters"] = {"ip_address": self._pc_ip}
        
        reply_dict = self._send_message(message_dict)

        if reply_dict["parameters"]["status"] == "ok":
            self._connection = True
        else:
            raise SolstisError("The connection to the SolStis was not accepted")

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def _send_message(self,message_dict):
        """
        This method takes a dict obj (without 'message' at front), converts it to a string, sends it to the THz-FireFly laser and returns
        the replied message dict as a dict obj.
        """

        # Prepare the message to be send to the Solstis
        self._transmission_id += 1
        message_dict["transmission_id"] = [self._transmission_id]
        send_dict = {"message":message_dict}

        # The 'json' package takes care that the dictionary is converted
        # to a json formatted string.
        send_str = json.dumps(send_dict)

        self._s.send(send_str.encode())
        
        reply_message = json.loads(self._s.recv(256).decode())["message"]

        return reply_message
    
    def get_wavelength(self):
        reply = self._send_message({"op":"poll_wave_m"})
        self.wavelength_current = reply['parameters']['current_wavelength'][0]
        return self.wavelength_current
        
    def set_wavelength(self, newWavelength):
        message_dict = {"op":"set_wave_m","parameters":{"wavelength":[newWavelength]}}
        self._send_message(message_dict)
        self.wavelength_to_go = newWavelength
    
    def get_tuning_status(self):
        message_dict = {"op":"poll_wave_m"}
        response = self._send_message(message_dict)
#        print response
        return response['parameters']['status'][0]
        
#    def activateWavelengthLock(self, activate=True):
#        if activate:
#            operation = 'on'
#        else:
#            operation = 'off'
#        message_dict = {"op":"lock_wave_m","parameters":{"operation":operation}}
#        print message_dict
#        response = self._send_message(message_dict)
#        if response['parameters']['status'][0] == 1:  # operation unsuccessful
#            raise SolstisError('Wavelength could not get locked.')
        
        
    def maintain_wavelength(self, activate=True):
        if activate:
            operation = 'on'
        else:
            operation = 'off'
        message_dict = {"op":"lock_wave_m","parameters":{"operation":operation}}
        # print(message_dict)
        response = self._send_message(message_dict)
        if response['parameters']['status'][0] == 1:  # operation unsuccessful
            raise SolstisError('Wavelength could not get maintained.')
        else:
            time.sleep(0.1)  # necessary for the laser to take the order into account
            
    def get_ethalon_lock_status(self):
        message_dict = {"op":"etalon_lock_status"}
        response = self._send_message(message_dict)
        return response['parameters']['condition']
        
    def wait_for_ethalon_lock(self):
#        
#        while self.get_ethalon_lock_status() != 'on':
#            print self.get_ethalon_lock_status()
#            time.sleep(0.1)
#            pass
        while True:
            status = self.get_ethalon_lock_status()
#            print status
#            sys.stdout.flush()
            time.sleep(0.05)
            if status == 'on':
                break
        
    def wait_for_tuning_status_finished(self, nbOfPasses=100):
        for i in range(nbOfPasses):
            while True:
                tuning_status = self.get_tuning_status()
                if tuning_status == self.WAVELENGTH_MAINTAINED:
                    break
                elif tuning_status == self.TUNING_NOT_ACTIVE:
                    raise SolstisError('Tuning is not active')
    
    def wait_for_good_wavelength(self, timeout=60, finishRangeRadius=0.01):
        # timeout in seconds, -1 for infinite
        # finishRangeRadius in nm
        startTime = time.time()
        while True:
            curTime = time.time() - startTime
            
            curWave = self.get_wavelength()
            
            if timeout != -1 and curTime > timeout:
                print('WARNING: Timeout. Solstis did not reach exact wavelength ({} instead of {}).'.format(curWave, self.wavelength_to_go))
                break
            
            
            if self.wavelength_to_go - finishRangeRadius < curWave < self.wavelength_to_go + finishRangeRadius:
                break

    def wait_for_tuning(self, timeout=60, finishRangeRadius=0.01):
        try:
            self.wait_for_good_wavelength(timeout=timeout, finishRangeRadius=finishRangeRadius)
            self.wait_for_tuning_status_finished(nbOfPasses=10)
        except:
            raise

    def close(self):
        pass

if __name__ == "__main__":
    toto = SolstisLaser(laser_ip_address='192.168.1.222', pc_ip_address='192.168.1.120', port_number=39933)
#    messageDict = {"op":"ping","parameters":{"text_in":"ABCDEFabcdef"}}
#    returnMessage = toto._send_message(messageDict)
#    print returnMessage
#    
##    print toto._send_message({"op":"poll_wave_m"})
##    print toto._send_message({"op":"set_wave_m","parameters":{"wavelength":[836.90]}})
#    print toto._send_message({"op":"poll_wave_m"})
    toto.maintain_wavelength(True)
    toto.set_wavelength(800)
#    time.sleep(1)
    print(toto.get_tuning_status())
    print(toto.get_tuning_status())
    print(toto.get_tuning_status())
    toto.wait_for_tuning()
#    toto.wait_for_good_wavelength(timeout=20, finishRangeRadius=0.002)
#    print toto.get_wavelength()
#    print toto.get_tuning_status()
    