# -*- coding: utf-8 -*-
"""
Created on 01/02/2018

@author: raphael proux
"""

from measurements.programs.attopos.AttoPos import attopos_run

config = {"attoAxes": {"Px": 2, "Py": 1, "Pz": 3, "Sx": 0, "Sy": 0, "Sz": 0}, 
          "attoVisaScannersId": "ASRL22::INSTR", 
          "attoVisaPositionersId": "ASRL20::INSTR", 
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}

attopos_run(config)

