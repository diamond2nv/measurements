
import datetime
import sys
from measurements.libs import dummy_scanners as mscan, mapper_detectors as mdet
from  measurements.libs import mapper_iter as mapper
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mdet)

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
dummy_scanner = mscan.ScannerCtrl(channels = [0,1,2], ids = ['dummy-1', 'dummy-2', 'dummy-3'])

apd0 = mdet.dummyAPD(work_folder = 'C:/')
apd0.set_integration_time_ms(ctr_time_ms)
apd1 = mdet.dummyAPD(work_folder = 'C:/')
apd1.set_integration_time_ms(ctr_time_ms)

d = datetime.datetime.now()

XYscan = mapper.XYScanIterative(scanner_axes = dummy_scanner, detectors = [apd0, apd1])
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.set_back_to_zero()
XYscan.open_GUI()
#XYscan.save_to_txt(r'C:\Users\cristian\Research\test_txt')
#XYscan.save_to_hdf5(file_name=r'C:\Users\cristian\Research\test7.hdf5')
#XYscan.plot_counts()


