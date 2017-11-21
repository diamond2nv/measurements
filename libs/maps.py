import pylab as py
import time
#import sys
import datetime
import os.path
from AttocubeANC300 import AttocubeANC300
#from pylonWeetabixTrigger import trigSender, trigReceiver
from Keithley import Keithley


class XYMap ():

	def __init__(self, atto_ctrl):
		self._atto = atto_ctrl
		

