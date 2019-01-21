
import os, sys, time
from datetime import datetime
import random
import pylab as plt
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs import ui_scan_gui as uM
from importlib import reload
reload (uM)


class ScanGUI(QtWidgets.QMainWindow):

    def __init__(self):

        QtWidgets.QWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uM.Ui_Form()
        self.ui.setupUi(self)

        #SETTINGS ELEMENTS
        #self.ui.doubleSpinBox_xmin.setSingleStep(1)

        #CONNECT SIGNALS TO EVENTS
        #self.ui.pushButton_start.clicked.connect (self._start_scan)

    def _start_scan (self):
        print ("Starting scan...")
        
    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        print ("Close window...")
        ce.accept()




qApp=QtWidgets.QApplication.instance() 
if not qApp: 
    qApp = QtWidgets.QApplication(sys.argv)

gui = ScanGUI ()
gui.setWindowTitle('QPL-ScanGUI')
gui.show()
sys.exit(qApp.exec_())
