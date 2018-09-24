import u3

d = None
d = u3.U3()

d.debug = True

Volts = 0
bits = d.voltageToDACBits(volts = Volts, dacNumber = 0, is16Bits = True)

Sx = u3.DAC16(0, bits)
Sy = u3.DAC16(1, bits)

channels = [Sx, Sy]

for channel in channels:
    d.getFeedback(channel, bits)