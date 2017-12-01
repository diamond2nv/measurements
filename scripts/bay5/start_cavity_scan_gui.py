########################################
# Cristian Bonato, 2015
# cbonato80@gmail.com
########################################

from __future__ import unicode_literals
import os, sys, time
from datetime import datetime
from PySide.QtCore import *
from PySide.QtGui import *
import random
from matplotlib.backends import qt4_compat
use_pyside = qt4_compat.QT_API == qt4_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore, uic
else:
    from PyQt4 import QtGui, QtCore, uic

import pylab as plt
import h5py
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm
from analysis.lib.fitting import fit

from measurement.lib.cavity.cavity_scan_v2 import

from measurement.lib.cavity.panels import control_panel_2 as control_panel
from measurement.lib.cavity.panels import scan_panel_v9 as scan_panel
from measurement.lib.cavity.panels import XY_scan_panel as XYscan_panel

from measurement.lib.cavity.cavity_scan_v2 import CavityExpManager, CavityScan


###we actually want cyclopeaninstruments, as well as a gui based on panel. these two go together very nicely. 

# qApp = QtGui.QApplication(sys.argv)

#this will become a (cyclopean??) instrument, or is removed.? instead uyse the cavity_scan_manager
# this would mean I actually want to go for the all-cyclopean setup. to me it makes sense to do it.
from main_window import MainWindow
mainwindow = MainWindow()
mainwindow.show()

from measurement.lib.cavity.panels.control_panel_2 import ControlPanelGUI
add_panel(ControlPanelGUI, title='Control Panel', sampling=100, ins='master_of_cavity')


# expMngr = CavityExpManager(adwin=qt.instruments['adwin'], 
#     wm_adwin=qt.instruments['physical_adwin_cav1'], laser=qt.instruments['newfocus1'], 
#     moc=qt.instruments['master_of_cavity'], counter =  qt.instruments['counters'])

aw_ctrl = control_panel.ControlPanelGUI(exp_mngr = expMngr)
aw_ctrl.setWindowTitle ('Control Panel')
aw_ctrl.show()

aw_scan = scan_panel.ScanGUI(exp_mngr = expMngr)
aw_scan.setWindowTitle('Laser & Piezo Scan Interface')
aw_scan.show()

xyscan_gui = XYscan_panel.XYScanGUI (exp_mngr = expMngr)
xyscan_gui.setWindowTitle('XY Scan')
xyscan_gui.show()

sys.exit(qApp.exec_())

