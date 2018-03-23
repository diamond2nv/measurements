# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 09:23:52 2016

@author: raphael proux, mauro brotons

Solstis laser sweep in wavelength while measuring spectra with the Acton spectrometer
"""

import datetime
import os.path
from measurements.libs import mapper 
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet

from importlib import reload
reload(mapper)
reload(mscan)
reload(mdet)

#######################
#     Parameters      #

delayBetweenPoints = 0.5
delayBetweenRows = 0.

xLims = (820, 830)  # (0, 5)
xStep = 2

voltsDirectory = r'C:\Users\QPL\Desktop\temporary_meas'

#######################
# instruments

laserCtrl = mscan.SolstisLaserScanner(laser_ip_address='192.168.1.222', pc_ip_address='192.168.1.130', port_number=39933, timeout=40, finish_range_radius=0.01, max_nb_of_fails=10)

spectroCtrl = mdet.ActonLockinCtrl(lockinVisaAddress=r"GPIB0::14::INSTR")
multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::22::INSTR')

d = datetime.datetime.now()
voltsFilePath = os.path.join(voltsDirectory, 'powerInVolts_{:%Y-%m-%d_%H-%M-%S}.txt'.format(d))

# Scanning program
laser_scan = mapper.XYScan(scanner_axes=laserCtrl, detectors=[spectroCtrl, multimeterCtrl])
laser_scan.set_range(xLims=xLims, xStep=xStep)
laser_scan.set_delays(between_points=delayBetweenPoints, between_rows=delayBetweenRows)
laser_scan.set_back_to_zero()

laser_scan.run_scan()

laser_scan.save_to_txt(voltsFilePath, array=volts_scan.counts[1])

