import u3 

d = None
d = u3.U3()

d.debug = True

Volts = 2
bits = d.voltageToDACBits(volts = Volts, dacNumber = 0, is16Bits = True)


Sx = u3.DAC16(0, bits)
Sy = u3.DAC16(1, bits)

channels = [Sx, Sy]

for channel in channels:
    d.getFeedback(channel, bits)
    
    
class vOutU3(u3.DAC16):
    
    def __init__(self, Value):
        
        DAC16.__init(self, 0, Value)
        u3.DAC16__init__(self, Dac, Value)
        
        Bits = self.voltageToDACBits(volts = Volts, dacNumber=0, is16Bits = True)
        
    def write(self, Volts):
        bits = d.voltageToDACBits(Volts, channel, is16Bits = True)
        self.getFeedback(channel, bits)