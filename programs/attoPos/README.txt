Readme file by Raphael Proux (30/03/2017).
AttoPos V3.0

This program controls the scanners and positioners on an ANC300 controller with three 
axes of each (or less). It can also be interfaced with older ANC150 (positioners) and 
ANC200 (scanners) and handle both at the same time (one for the scanners, one for the 
positioners).

>>>>>>>>> The main file to execute is AttoPos.py <<<<<<<<<<


## CONNECTING THE ANC CONTROLLER TO THE COMPUTER ##

To use it with an ANC300, the controller can be plugged via USB and recognized by 
Windows as a Serial interface (COM port)

It works the same way for ANC150/200, except for the fact that you may need to use a 
serial null-modem cable (IMPORTANT! Null-modem cables are not the usual serial 
straight-through cables). 

Note that the program can handle two different controllers (one for the scanners, one 
for the positioners).


## CONFIGURATION ##

Modify the CONFIG.txt file to set the parameters of the different positioners/
scanners axes.
Px/y/z are the three positioner axes, Sx/y/z are the three scanner axes.


- VISA identifiers: "attoVisaScannersId" and "attoVisaPositionersId"
The controllers are recognized as serial interfaces by Windows. 
You can use National Instruments MAX to check the VISA identifier. It should be of the 
form "ASRL9::INSTR". Even if it is common that the number in the VISA identifier 
corresponds to the COM port number in Windows, they do not necessarily match.

In the case where the controllers handling the scanners and the positioners are 
different, you can input the VISA identifier of each one in the CONFIG.txt file. 
If only one controller is used, the two VISA identifiers in the CONFIG.txt file 
must be identical.

- Axes: "attoAxes"
ID numbers of the axes on the controller, usually between 1 and 6. If you want to 
deactivate an axis (for example if it is not existing), put 0 as an ID number (it
will then appear greyed out in the user interface).

- Direction of motion: "reversedMotion"
For each axis, you can reverse the behaviour of the UP/DOWN orders given by the keyboard
navigation and for the STEP UP/DOWN and CONT UP/DOWN buttons (positioners only).
Concretely, for the positioners, if reversedMotion is set to 0, the up/down orders will 
behave identically to the up/down buttons on the controller. If reversedMotion is set to 1,
it will behave in a reversed fashion. For the scanners, it only affects the keyboard 
navigation and the display still shows the actual voltage applied on the piezoelectric crystals.


## TROUBLESHOOTING ##

For a new computer being configured, please check you have the PyVISA package and PyQT4 installed.
With the Anaconda distribution, these can be installed using 'pip install pyvisa' and 
'conda install pyqt4' or 'conda install pyqt=4' in the command prompt.

If the program does not work properly, check the following:
- check the controllers are switched on, connected properly and recognized in Windows. Note that
the old ANC150/200 need to be manually switched from grounded to computer control (CCON) mode, and
that all the active axes should be in computer control mode (if one is not, it will fail).
- check the config file, in particular the VISA identifiers and axes numbers,
- check no other program is currently running and using the controller. Note this can include 
a past python session which did not close properly the controller connection, so you can try
to restart all python kernels (in Spyder, on the top right corner of the console)


