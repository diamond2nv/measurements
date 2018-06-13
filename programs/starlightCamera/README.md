# StarlightCamera software

This software can be used to read data from a Starlight Xpress camera. It has only been tested with Lodestar X2 and Ultrastar cameras from Starlight Xpress, but should be able to handle other cameras adding slight modifications.

## What Python file should I run?

You should run `starlightCapture.py`


## Install a camera / solve the "camera not recognised" issue

On Windows, the driver provided by Starlight will not work with 
StarlightCamera. You have to use the `libusb` drivers provided together with this program in the `libusb-win32-bin-1.2.6.0.zip` archive.

__Please note__ that if you are installing this driver for the first time on any computer, it will work only if the camera is plugged on the computer. _Inputting the identifiers by hand will not work._

To install the correct drivers, go in the bin folder and execute `inf-wizard.exe`

1. Click "Next" and select your camera in the list.  
UltraStar cameras will have Vendor ID `0x1278` and Product ID `0x0525`, LodeStar X2 cameras will have Vendor ID `0x1278` and Product ID `0x0507`.
2. Click "Next" and change "Manufacturer Name" and "Device Name" to your
    preference. The Device Name will be the one appearing in Windows Device manager so it can help to put something useful.
3. Click "Next", save the .inf file anywhere you want.
4. Click on "Install now..." Windows may prompt you saying the driver is
    not signed and click "Install anyway" or something similar.

Some additional information here: [http://stackoverflow.com/questions/20315797/installing-libusb-1-0-on-windows-7](http://stackoverflow.com/questions/20315797/installing-libusb-1-0-on-windows-7)

## About interlacing

Some cameras like the Lodestar X2 are not capable of acquiring all the rows of the sensor at the same time. They interlace the rows, which means one can only acquire the odd or the even rows, or the two summed (vertical binning of 2). 

The vertical binning mode is the default one in the StarlightCamera software. 

If you activate `InterLacing acq.` without `IL corr double expo`, the odd rows will be read at the end of integration time, immediately followed by the even rows. The problem is that reading the odd rows and downloading them is quite slow, so when the even rows are read, they will have integrated a few tens of milliseconds more. For very long integration times of several tens of seconds, this may not be a problem, but for normal times of a few seconds down to milliseconds, the image will be strongly affected. 

If you activate `IL corr double expo`, the odd rows will be acquired after one integration time, the sensor is then cleaned and the even rows are finally acquired after a second integration time. This provides a reliable image, at the expense of doubling the integration time.

## Tips and tricks

To be able to capture images in the dark without switching on the screen, the shortcut `Ctrl+Space` starts the acquisition (and stops it if the acquisition is not finished) and, in capture mode, a sound will be played at the start and the end of the acquisition.

## How to read the files

The files are saved in the FITS format, which can be read by [imageJ](https://imagej.nih.gov/ij/). Be aware that for images acquired without interlacing correction, the height will be divided by two. This can be corrected in imageJ using a Y scaling of 2.

To read the FITS images in Python, we have a package `tools.instruments.readFits` which provides read and write capabilities.