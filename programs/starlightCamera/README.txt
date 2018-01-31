WHAT PYTHON FILE SHOULD I RUN?

You should run starlightCapture.py


INSTALL A CAMERA / SOLVE CAMERA NOT RECOGNISED ISSUE

On Windows, the driver provided by Starlight will not work with the 
starlightCaptureUSB program. You have to use the libusb drivers provided together with this program in the libusb-win32-bin-1.2.6.0 folder or zip archive.

To install the correct drivers, go in the bin folder and execute inf-wizard.exe
1 - Click Next and select your camera in the list. 
    UltraStar cameras will have Vendor ID 0x1278 and Product ID 0x0525,
    LodeStar X2 cameras will have Vendor ID 0x1278 and Product ID 0x0507.
2 - Click Next and change Manufacturer Name and Device Name to your
    preference. The Device Name will appear in Windows Device manager.
3 - Click Next, save the Inf file in the libusb-win32-bin-1.2.6.0/bin
    folder.
4 - Click on Install now... Windows may prompt you saying the driver is
    not signed and click "Install anyway" or something similar.

Some additional information here: http://stackoverflow.com/questions/20315797/installing-libusb-1-0-on-windows-7