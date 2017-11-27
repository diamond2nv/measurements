
'''
Python interface for Pulse Streamer 8/2 by Swabian Instruments
Code: Cristian Bonato, c.bonato@hw.ac.uk
'''

import numpy as np 
import pylab as plt
import logging

# we use the tinyrpc package to connect to the JSON-RPC server
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc import RPCClient
from tools import toolbox_delft as toolbox

# binary and base64 conversion
import struct
import base64

class PulseStreamer():
	#Class for Pulse Streamer 8/2, Swabian Instruments

	def __init__(self, address = '192.168.1.100'):

   		if (toolbox.validate_ip (address)):		
			self.ip = address
			self.url = 'http://'+self.ip+':8050/json-rpc'
			try:
				self.client = RPCClient(
			    	JSONRPCProtocol(),
			    	HttpPostClientTransport(self.url)
					)
			except:
				print 'Error: cannot create RPC client!'
			try:
				self.ps = self.client.get_proxy()
			except:
				print 'Error: cannot create proxy connection!'
		else:
			print "IP address not valid!"

	def load_sequence (self, sequence):
		self.sequence = sequence
	
	def generate_random_seq(self, min_len=0, max_len=1024, n_pulses=1000):
		ttt = np.random.uniform(min_len, max_len, n_pulses).astype(int)
		t = [int(x) for x in ttt]
		print t
		seq = [ (8, 1, 0, 0) ] # 8 ns trigger pulse on channel 0
		for i, ti in enumerate(t):
			state = int(i%2)
			sss = [ (int(ti), int(0xfe*state), int(0x7fff*state), -int(0x7fff*state))]
			print sss
			seq += sss
		print seq
		return seq

	def encode(self, seq):
	    """
	    Convert a human-readable python sequence to a base64-encoded string
	    """
	    s = b''
	    for pulse in seq:
	    	print 'pulse', pulse
	        s+=struct.pack('>IBhh', *pulse)
	    return base64.b64encode(s)

	def set_parameters (self, n_runs = -1, initial = (0,0xff,0,0), 
			final = (0,0x00,0x7fff,0), underflow = (0,0,0,0), start = 'IMMEDIATE'):

		self.n_runs = n_runs
		self.initial = initial
		self.final = final
		self.underflow = underflow
		self.start = start

	def start_stream (self):
		self.ps.stream(self.encode(self.sequence), self.n_runs, 
					self.initial, self.final, self.underflow, self.start)

	def isRunning (self):
		if (self.ps.isRunning()==1):
			print 'Yes'
		else:
			print 'No'

	def stop (self):
		self.ps.stream ([0,0,0,0])
		if (self.ps.isRunning()==0):
			print 'Pulse Streamer stopped'
