
import datetime
import sys
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet
from measurements.libs import dummy_scanners as mscan_dummy
from  measurements.libs import mapper_iter as mapper
if sys.version_info.major == 3:
    from importlib import reload

reload(mapper)
reload(mscan)
reload(mscan_dummy)
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
dummy_scanner = mscan_dummy.ScannerCtrl(channels = [2])
min_lim = -5.
max_lim = 5.
GalvoCtrl = mscan.GalvoNI (chX = '/Dev1/ao1', chY = '/Dev1/ao0', ids = ['galvo-x', 'galvo-y']) 
GalvoCtrl.set_range(min_limit=min_lim, max_limit=max_lim)

#s = mscan.ScannerCtrl()
#s._scanner_axes = [GalvoCtrl[0], GalvoCtrl[1], dummy_scanner]
#s._scanner_axes._ids = ['galvo-x', 'galvo-y', 'dummy']

voltmeterCtrl = mdet.MultimeterCtrl(VISA_address=r'ASRL5::INSTR')
voltmeterCtrl._ctr_time_ms = 0

#apd0 = mdet.dummyAPD(work_folder = 'C:/')
#apd0.set_integration_time_ms(ctr_time_ms)
#apd1 = mdet.dummyAPD(work_folder = 'C:/')
#apd1.set_integration_time_ms(ctr_time_ms)

d = datetime.datetime.now()

XYscan = mapper.Mapper2D_3axes (scanner_axes = [GalvoCtrl, dummy_scanner], detectors = [voltmeterCtrl])
XYscan.set_work_folder (r'C:\Users\Daniel\Desktop\Voltmeter')
#XYscan.set_work_folder ('C:/Users/cristian/Research/Work-Data/')
XYscan.set_delays (between_points = delayBetweenPoints, between_rows = delayBetweenRows)
XYscan.set_back_to_zero()
XYscan.open_GUI()
#XYscan.save_to_txt(r'C:\Users\cristian\Research\test_txt')
#XYscan.save_to_hdf5(file_name=r'C:\Users\cristian\Research\test7.hdf5')
#XYscan.plot_counts()


