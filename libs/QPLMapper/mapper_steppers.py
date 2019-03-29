
import pylab as np
import time
import sys
import visa


class Stepper ():

    def __init__ (self):
        self._nr_axes = 0
        self.axes = {['0']={}, ['1']={},['2']={}}
        self.parameters = [[None, None], [None, None], [None, None]]

    def move (self, axis, target=None):
        pass

    def get_position (self, axis):
        pass

    def set_parameter (self, axis, parameter, value):
        pass


    def add_scanner_axis (self, scanner, axis, parameters = [], name = ''):
        if axis in [0,1,2]:
            self.axes[str(axis)]['scanner'] = scanner
            if (name == ''):
                self.axes[str(axis)]['name'] = 'axis-'+str(axis)
            else:
                self.axes[str(axis)]['name'] = name

            if len (parameters)>0:
                self.axes[str(axis)]['par-1'] = parameters[0]
                self.parameters[axis][0] = parameters[0]
            if len (parameters)>1:
                self.axes[str(axis)]['par-2'] = parameters[1]
                self.parameters[axis][1] = parameters[1]
            if len (parameters)>2:
                print ("Only two paramters are allowed, neglecting the rest.")
        else:
            print ("Maximum 3 axes allowed!")


