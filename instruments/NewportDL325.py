import visa
import time


class DelayStage:
    '''
    Operate the delay stage once it is properly initialised by the software.
    The function reset is here in case if one would like to use python to operate
    the delay stage independently.
    '''
    def __init__(self, address,accel=50,vel=300):
        self.rm = visa.ResourceManager()
        self.scanner = self.rm.open_resource (address)
        self.scanner.baud_rate = 9600
        self.scanner.timeout = 2000
        self.scanner.data_bits=8
        self.scanner.parity = visa.constants.Parity.none
        self.scanner.stop_bits = visa.constants.StopBits.one
        self.setaccel(accel) # set it to 50 mm/s^2
        self.setvelocity(vel) # set the velocity to be 300 mm/s
        
    def setaccel(self,accel):
        self.scanner.write('AC'+str(accel))
    
    def setvelocity(self,velo):
        self.scanner.write('VA'+str(velo))
        
    def getvelocity(self):
        vel = self.scanner.query('VA?')
        return float(vel[2:])
    
    def move_absolute (self, position):     #works
        self.scanner.write('PA'+str(position))

    def move_relative (self, distance):    #works
        self.scanner.write('PR'+str(distance))

    def get_position (self):
        I=self.scanner.query('TP')
        Pos=float(I[2:])
        return Pos
    def get_travel_time(self,rel_dis):
        '''
        This function is useful to determine the required amount of time interval 
        between movements.
        '''
        traveltime = self.scanner.query('PTT'+str(rel_dis)) #  return the travel time in seconds
        return float(traveltime[3:])

    def stop(self):
        self.scanner.write('ST')

    def getaccel(self):
        acceleration = self.scanner.query('AC?')
        return float(acceleration[2:])
    
    def reset (self):    #works
        self.scanner.write('RS')
        time.sleep(5)
        self.scanner.write('OR') # home
    
    def close(self):    #works
        self.scanner.clear()
        self.scanner.close()

if __name__=='__main__':
    scanner = DelayStage(u'ASRL23::INSTR')
    scanner.move_absolute(100)
    print (scanner.get_position())
    time.sleep(10)
    scanner.move_absolute(0)
    print (scanner.get_position())
    scanner.close()