
import datetime
import sys
from measurements.libs.QPLMapper import  mapper_detectors as mdet
from measurements.libs.QPLMapper import dummy_scanners as mscan_dummy
from measurements.libs.QPLMapper import  mapper_scanners as mscan
from measurements.libs.QPLMapper import mapper 
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan_dummy)
reload(mdet)
reload (mscan)

delayBetweenPoints = 0.1
delayBetweenRows = 0.1

a = 3.3165
b = -0.2915
d = 0.002
xStep = 0.0001

delayBetweenPoints = 0.08
delayBetweenRows = 0.08

xLims = (a-d,a+d)
yLims = (b-d,b+d)
yStep = xStep

#attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL4::INSTR', chX=0, chY=5)
GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0') 
GalvoCtrl.set_range(min_limit=-5., max_limit=5.)
voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL13::INSTR')
# ROOM-TEMPERATURE: max 20V!!!!
#xLims = (0, 3)
#xStep = 1.
#yLims = (0, 3)
#yStep = 1.

#######################
# convert to Attocube DC drive voltage
toDC_drive_voltage = 1./15

# APD counter integration time (ms)
ctr_time_ms = 10
ctr_port = 'pfi0'

#######################
# instruments
dummyA = mscan_dummy.ScannerCtrl(channels = [2])


XYscan = mapper.Mapper2D_XYZ (scanner_axes = [dummyA, GalvoCtrl], detectors = [voltmeterCtrl])
XYscan.set_work_folder (r'C:\Users\Daniel\Desktop\Voltmeter')
# XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.set_back_to_zero()
XYscan.open_GUI()
# #XYscan.save_to_txt(r'C:\Users\cristian\Research\test_txt')
# #XYscan.save_to_hdf5(file_name=r'C:\Users\cristian\Research\test7.hdf5')
# #XYscan.plot_counts()


