
import datetime
import sys
from measurements.libs.QPLMapper import  mapper_detectors as mdet
from measurements.libs.QPLMapper import dummy_scanners as mscan_dummy
from measurements.libs.QPLMapper import  mapper_Scanners as mscan
from measurements.libs.QPLMapper import mapper 
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan_dummy)
reload(mdet)
reload (mscan)

delayBetweenPoints = 0.1
delayBetweenRows = 0.1


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
dummyB = mscan.GalvoDummy (chX = '/Dev1/ao1', chY = '/Dev1/ao0', ids = ['galvo-x', 'galvo-y']) 

apd0 = mdet.dummyAPD(work_folder = 'C:/')
apd0.set_integration_time_ms(ctr_time_ms)
# #apd1 = mdet.dummyAPD(work_folder = 'C:/')
# #apd1.set_integration_time_ms(ctr_time_ms)


XYscan = mapper.Mapper2D_XYZ (scanner_axes = [dummyA, dummyB], detectors = [apd0])
XYscan.set_work_folder ('C:/Users/cristian/Research/Work-Data/')
# XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.set_back_to_zero()
XYscan.open_GUI()
# #XYscan.save_to_txt(r'C:\Users\cristian\Research\test_txt')
# #XYscan.save_to_hdf5(file_name=r'C:\Users\cristian\Research\test7.hdf5')
# #XYscan.plot_counts()


