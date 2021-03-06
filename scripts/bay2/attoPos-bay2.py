# -*- coding: utf-8 -*-
"""
Created on 01/02/2018
@author: raphael proux
"""

from measurements.programs.attoPos.AttoPos import attopos_run

config = {"attoAxes": {"Px": 3, "Py": 4, "Pz": 5, "Sx": 1, "Sy": 2, "Sz": 0},
          "attoVisaScannersId": "ASRL10::INSTR",
          "attoVisaPositionersId": "ASRL10::INSTR",
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}


attopos_run(config)
