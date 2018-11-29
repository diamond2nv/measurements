
from measurements.libs import mapper 
from measurements.libs import mapper_scanners as mscan, mapper_detectors as mdet


#######################
# instruments
attoCtrl = mscan.AttocubeVISA(VISA_address=r'ASRL13::INSTR', chX=1, chY=2)
apdCtrl = mdet.APDCounterCtrl (ctr_port = 'pfi0',
                               work_folder = r"C:\Users\ted\Desktop\temporary_meas",
                               debug = True)
multimeterCtrl = mdet.MultimeterCtrl(VISA_address=r'GPIB0::13::INSTR')

# Scanning program
XYscan = mapper.XYScan(scanner_axes=attoCtrl, detectors=[apdCtrl, multimeterCtrl])
XYscan.set_range(xLims=(0, 1), xStep=0.2, yLims=(0, 1), yStep=0.2)
XYscan.set_delays(between_points=0.5, between_rows=0.5)
XYscan.set_back_to_zero()
XYscan.run_scan()
XYscan.save_to_txt(voltsFilePath, array=XYscan.counts[1], flatten=True)

