# -*- coding: utf-8 -*-
"""
Created on 01/02/2018
@author: raphael proux
"""

from measurements.programs.attoPos.AttoPos import attopos_run

config = {"attoAxes": {"Px": 1, "Py": 2, "Pz": 3, "Sx": 5, "Sy": 4, "Sz": 0},
          "attoVisaScannersId": "ASRL6::INSTR",
          "attoVisaPositionersId": "ASRL6::INSTR",
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 1, "Pz": 0}}


attopos_run(config)
