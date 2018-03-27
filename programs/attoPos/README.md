
# AttoPos program

Readme file by Raphael Proux (30/03/2017).
AttoPos V3.1 (adapted to python 3 on the 31/01/18)

This program controls the scanners and positioners on an Attocube ANC300 controller with three 
axes of each (or less, XYZ style). It can also be interfaced with older ANC150 (positioners) and 
ANC200 (scanners) and handle both at the same time (one for the scanners, one for the 
positioners). It has only been tested with Python 3.6.


## Connecting the ANC controller to the computer

To use it with an __ANC300__, the controller can be plugged via USB and recognized by 
Windows as a Serial interface (COM port).

It works the same way for __ANC150/200__, except for the fact that, for some controllers, you will need to use a serial null-modem cable (IMPORTANT: Null-modem cables are not the usual serial 
straight-through cables). 

Note that the program can handle two different controllers (one for the scanners, one 
for the positioners).

## Execution
The main file is `AttoPos.py`, but it cannot be executed by itself. It needs to be called by a script in which you will define the configuration of the software – which address for the controller, which axis for which actuator, etc.

A typical script will contain the following:
```
from measurements.programs.attoPos.AttoPos import attopos_run

config = {"attoAxes": {"Px": 2, "Py": 1, "Pz": 3, "Sx": 0, "Sy": 0, "Sz": 0}, 
          "attoVisaScannersId": "ASRL22::INSTR", 
          "attoVisaPositionersId": "ASRL20::INSTR", 
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}

attopos_run(config)
```

You should change the `config` dictionary according to your system. For details see the next section.

The `attopos_run()` function is the call which launches the attoPos program.

### Shortcut for Windows users

A nice trick for Windows users: you can use a shortcut to launch the program as an executable. First, you need to create a shortcut to the call script file. Then open the properties (right-click > Properties) of the shortcut. The destination will have the full path to the call script file. Add `pythonw` in front – you may need to add double quotation marks around the filepath if it contains spaces.

If this does not work, you may not have `pythonw` in your `PATH` environment variable. You will then need to put the full path to your `pythonw.exe` file which should be at the root of your Anaconda install directory (or other distribution). 

## Configuration dictionary

As written above, the call script will contain a dictionary that is to be passed to `attopos_run()`. Here is a typical dictionary containing all the parameters:
```
config = {"attoAxes": {"Px": 2, "Py": 1, "Pz": 3, "Sx": 0, "Sy": 0, "Sz": 0}, 
          "attoVisaScannersId": "ASRL22::INSTR", 
          "attoVisaPositionersId": "ASRL20::INSTR", 
          "reversedMotion": {"Sx": 0, "Sy": 0, "Sz": 0, "Px": 0, "Py": 0, "Pz": 0}}
```

Modify it to set the parameters of the different positioners/scanners axes.
Px/y/z are the three positioner axes, Sx/y/z are the three scanner axes.

Here is a description of the parameters:

- VISA identifiers: `attoVisaScannersId` and `attoVisaPositionersId`  
The controllers are recognized as serial interfaces by Windows. You can use National Instruments MAX to check the VISA identifier. It should be of the form `ASRL9::INSTR`. Even if it is common that the number in the VISA identifier corresponds to the COM port number in Windows, they do not necessarily match.  
In the case where the controllers handling the scanners and the positioners are different, you can input the VISA identifier of each one in the `config` dictionary. If only one controller is used, the two VISA identifiers in the `config` dictionary must be identical.
- Axes: `attoAxes`  
ID numbers of the axes on the controller, usually between `1` and `6`. If you want to deactivate an axis (for example if it is not existing), put `0` as an ID number (it will then appear greyed out in the user interface).
- Direction of motion: `reversedMotion`  
For each axis, you can reverse the behaviour of the UP/DOWN orders given by the keyboard navigation and for the STEP UP/DOWN and CONT UP/DOWN buttons (positioners only). Concretely, for the positioners, if `reversedMotion` is set to `0`, the up/down orders will behave identically to the up/down buttons on the controller. If `reversedMotion` is set to `1`, it will behave in a reversed fashion. For the scanners, it only affects the keyboard navigation and the display still shows the actual voltage applied on the piezoelectric crystals.


## Troubleshooting

For a new computer being configured, please check you have the PyVISA package and PyQT5 installed.
With the Anaconda distribution, these can be installed using `pip install pyvisa` and 
`conda install pyqt=5` in the command prompt.

If the program does not work properly, check the following:

- check the controllers are switched on, connected properly and recognized in Windows. Note that
the old ANC150/200 need to be manually switched from grounded to computer control (CCON) mode, and
that all the active axes should be in computer control mode (if one is not, it will fail),

- check the config file, in particular the VISA identifiers and axes numbers,

- check no other program is currently running and using the controller. Note this can include 
a past python session which did not close properly the controller connection, so you can try
to restart all python kernels. In Spyder, this can be done in the menu at the top right corner of the console. Otherwise, use the Task manager of Windows or restart the computer,

- if all these steps have failed, disconnecting the device and restarting it might help, which means grounding all the connected piezo stacks. __ATTENTION:__ the controller must be disconnected from USB to be able to restart properly.


## Note: when you modify the Qt interface file

When you modify the `AttoPos.ui` file, you need to export it to Python using the `pyuic` tool provided by PyQt. Here:
```
pyuic5 AttoPos.ui -o UiAttoPos.py
```

You will then lose the arrows in the continuous and step command buttons, which comes from a relative path issue. When you apply `pyuic5` to generate the Python file, you will need to make some modifications. First, import `os.path` by adding `import os.path` at the beginning, and then modify the name of the files `"ArrowDown.png"` and `"ArrowUp.png"` by path reconstructing codes `os.path.join(os.path.dirname(__file__), "ArrowDown.png")` and `os.path.join(os.path.dirname(__file__), "ArrowUp.png")`.

