# -*- coding: utf-8 -*-
"""
Created on 01/02/2018
@author: raphael proux
"""

from measurements.programs.multimeterOscillo.multimeterOscillo import multimeter_oscillo_run

config = {"keithleyVisaId": "GPIB1::1::INSTR", "meas_mode": "voltage"}

multimeter_oscillo_run(config)