
# Measurement libraries

Readme file by Raphael Proux (13/03/2018).

Libraries used for doing measurements – please note the `instruments` folder contains the libraries specifically written to communicate directly with an instrument.


## Mapper libraries

The mapper libraries are split in four different files:

* `mapper.py` contains the classes and programs to be called for measurements (like `XYScan.py`),

* `mapper_general.py` should nearly never be changed (only for some architecture change). It contains a generic `DeviceCtrl` class which serves as a generic base for scanners and detectors classes,

* `mapper_detectors.py` defines the device classes specific to detectors (`DetectorCtrl` based on the parent class `DeviceCtrl` from `mapper_general.py`). This is the file to modify to add a new detector.

* `mapper_scanners.py` defines the device classes specific to scanners (`ScannerCtrl` based on the parent class `DeviceCtrl` from `mapper_general.py`). This is the file to modify to add a new detector. 

### `Mapper.py` library

This file contains the measurement classes themselves. For now, there is only one measurement class called `XYScan`.

#### `XYScan` class