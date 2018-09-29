import pylab as pl
import numpy as np
import datetime
import os.path
import sys
from astropy.convolution import convolve, Box1DKernel
#pl.close()


voltsDirectory = r'C:\Users\Daniel\Desktop\Voltmeter'
voltsFile = 'powerInVolts_2018-09-13_18-43-26.txt'

voltsFilePath = os.path.join(voltsDirectory, voltsFile)

x = pl.loadtxt(voltsFilePath)


#y = convolve(y, Box1DKernel(40))


#pl.plot(x, y, label = label1)
#pl.title('FL PL', x=0.9, y=0.75)
##pl.legend()
##pl.title(r'$\lambda$ = 715 - 755nm', x=0.8, y=0.8)
#pl.xlabel('Wavelength (nm)')
#pl.ylabel('Counts $\mathregular{(s^{-1}})$')
#
#pl.xlim(770 , 811.2)
##pl.ylim(-2,200)