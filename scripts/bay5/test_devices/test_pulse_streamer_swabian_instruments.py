import os
file_path = os.path.dirname(os.path.realpath(__file__))

proto_path = os.path.abspath(file_path+"../../../../proto")

import sys
sys.path.insert(0,proto_path)

import numpy as np

from grpc.beta import implementations

from pulse_streamer_pb2 import VoidMessage, PulseMessage, SequenceMessage, beta_create_PulseStreamer_stub

channel = implementations.insecure_channel('192.168.1.100', 50051)
stub = beta_create_PulseStreamer_stub(channel)

def get_random_seq(min_len=0, max_len=1024, n_pulses=1000):
    """
    Generate a sequence of random pulses on the digital
    channels 1-7 and the two analog channels.
    
    Digital channel 0 is used as a trigger.    
    """
    t = np.random.uniform(min_len, max_len, n_pulses).astype(int)
    seq = SequenceMessage()
    
    seq.pulse.extend([PulseMessage(ticks=8, digi=1, ao0=0,ao1=0)]) # 8 ns trigger pulse on channel 0
    for i, ti in enumerate(t):
        state = i%2
        p = PulseMessage(ticks=ti, digi=0xfe*state, ao0=0x7fff*state, ao1=-0x7fff*state)
        seq.pulse.extend([p])
    return seq

seq = get_random_seq(0, 1024, 10000)

# example how to set some values
initial = seq.initial
initial.ao0=0x1000
initial.ao1=0x1000
seq.start = seq.IMMEDIATE

reply = stub.stream(seq, timeout=100)

print("Pulse Streamer replied: "+str(reply.value))

reply = stub.isRunning(VoidMessage(), 100)

print('Pulse Streamer is running: '+str(reply.value))
