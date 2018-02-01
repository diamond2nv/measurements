# -*- coding: utf-8 -*-
"""
Created on 01/02/2018

@author: raphael proux
"""

import pylab as pl
import measurements.programs.attopos.AttoPos import attopos_run

config = {"attoAxes": {"Px": 1, "Py": 2, "Pz": 3, "Sx": 4, "Sy": 5, "Sz": 6}, 
          "attoVisaScannersId": "ASRL1::INSTR", 
          "attoVisaPositionersId": "ASRL1::INSTR", 
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}

attopos_run(config)

