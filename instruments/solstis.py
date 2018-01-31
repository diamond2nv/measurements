# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 16:51:51 2017

@author: Raphael Proux

Tests with the Solstis laser from MSquared

Tests with the socket library (based on Msquared)
"""

import socket
import json
import time

class SolstisError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class solstisLaser():

    TUNING_NOT_ACTIVE = 0
    NO_LINK_TO_WAVEMETER = 1
    TUNING_IN_PROGRESS = 2
    WAVELENGTH_MAINTAINED = 3

    def __init__(self, laserIpAddress, pcIpAddress, portNumber=39933, transmissionId=0):
        self._address = laserIpAddress # Ip address of the Solstis
        self._pc_ip = pcIpAddress  # ip-address of the pc
        self._port = portNumber
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._transmission_id = transmissionId
        self._connection = False
        
        self.wavelengthCurrent = -1
        self.wavelengthToGo = -1

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
        
    
    
    # The most important method.
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
    
    def getWavelength(self):
        reply = self._send_message({"op":"poll_wave_m"})
        self.wavelengthCurrent = reply['parameters']['current_wavelength'][0]
        return self.wavelengthCurrent
        
    def setWavelength(self, newWavelength):
        message_dict = {"op":"set_wave_m","parameters":{"wavelength":[newWavelength]}}
        self._send_message(message_dict)
        self.wavelengthToGo = newWavelength
    
    def getTuningStatus(self):
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
        
        
    def maintainWavelength(self, activate=True):
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
            
    def getEthalonLockStatus(self):
        message_dict = {"op":"etalon_lock_status"}
        response = self._send_message(message_dict)
        return response['parameters']['condition']
        
    def waitForEthalonLock(self):
#        
#        while self.getEthalonLockStatus() != 'on':
#            print self.getEthalonLockStatus()
#            time.sleep(0.1)
#            pass
        while True:
            status = self.getEthalonLockStatus()
#            print status
#            sys.stdout.flush()
            time.sleep(0.05)
            if status == 'on':
                break
        
    def waitForTuningStatusFinished(self, nbOfPasses=100):
        for i in range(nbOfPasses):
            while True:
                tuning_status = self.getTuningStatus()
                if tuning_status == self.WAVELENGTH_MAINTAINED:
                    break
                elif tuning_status == self.TUNING_NOT_ACTIVE:
                    raise SolstisError('Tuning is not active')
    
    def waitForGoodWavelength(self, timeout=60, finishRangeRadius=0.01):
        # timeout in seconds, -1 for infinite
        # finishRangeRadius in nm
        startTime = time.time()
        while True:
            curTime = time.time() - startTime
            
            curWave = self.getWavelength()
            
            if timeout != -1 and curTime > timeout:
                print('WARNING: Timeout. Solstis did not reach exact wavelength ({} instead of {}).'.format(curWave, self.wavelengthToGo))
                break
            
            
            if self.wavelengthToGo - finishRangeRadius < curWave < self.wavelengthToGo + finishRangeRadius:
                break

    def waitForTuning(self, timeout=60, finishRangeRadius=0.01):
        try:
            self.waitForGoodWavelength(timeout=timeout, finishRangeRadius=finishRangeRadius)
            self.waitForTuningStatusFinished(nbOfPasses=10)
        except:
            raise

    def close(self):
        pass

if __name__ == "__main__":
    toto = solstisLaser(laserIpAddress='192.168.1.222', pcIpAddress='192.168.1.120', portNumber=39933)
#    messageDict = {"op":"ping","parameters":{"text_in":"ABCDEFabcdef"}}
#    returnMessage = toto._send_message(messageDict)
#    print returnMessage
#    
##    print toto._send_message({"op":"poll_wave_m"})
##    print toto._send_message({"op":"set_wave_m","parameters":{"wavelength":[836.90]}})
#    print toto._send_message({"op":"poll_wave_m"})
    toto.maintainWavelength(True)
    toto.setWavelength(800)
#    time.sleep(1)
    print(toto.getTuningStatus())
    print(toto.getTuningStatus())
    print(toto.getTuningStatus())
    toto.waitForTuning()
#    toto.waitForGoodWavelength(timeout=20, finishRangeRadius=0.002)
#    print toto.getWavelength()
#    print toto.getTuningStatus()
    