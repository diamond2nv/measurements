
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from measurements.libs.QPLser import StreamCanvas as SC
import random

from importlib import reload
reload (SC)

class Ui_Panel(object):
    def setupUi(self, Panel):
        Panel.setObjectName("Panel")
        Panel.resize(1155, 754)
        self.vbl = QtWidgets.QVBoxLayout(Panel)
        self.vbl.setContentsMargins(0,0,0,0)
        self.canvas = SC.MultiStreamCanvas(Panel, width=7, height=3, dpi=200)
        self.vbl.addWidget (self.canvas)
        self.Hscrollbar = QtWidgets.QScrollBar(Panel)
        self.Hscrollbar.setGeometry(QtCore.QRect(10, 590, 1131, 21))
        self.Hscrollbar.setMaximum(50)
        self.Hscrollbar.setSingleStep(7)
        self.Hscrollbar.setPageStep(100)
        self.Hscrollbar.setOrientation(QtCore.Qt.Horizontal)
        self.Hscrollbar.setObjectName("Hscrollbar")
        self.label_view_time = QtWidgets.QLabel(Panel)
        self.label_view_time.setGeometry(QtCore.QRect(430, 660, 51, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_view_time.setFont(font)
        self.label_view_time.setObjectName("label_view_time")
        self.cb_D2 = QtWidgets.QCheckBox(Panel)
        self.cb_D2.setGeometry(QtCore.QRect(80, 713, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D2.setFont(font)
        self.cb_D2.setObjectName("cb_D2")
        self.cb_A0 = QtWidgets.QCheckBox(Panel)
        self.cb_A0.setGeometry(QtCore.QRect(260, 713, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_A0.setFont(font)
        self.cb_A0.setObjectName("cb_A0")
        self.botton_zoom_in = QtWidgets.QPushButton(Panel)
        self.botton_zoom_in.setGeometry(QtCore.QRect(530, 640, 61, 51))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.botton_zoom_in.setFont(font)
        self.botton_zoom_in.setObjectName("botton_zoom_in")
        self.cb_D7 = QtWidgets.QCheckBox(Panel)
        self.cb_D7.setGeometry(QtCore.QRect(200, 733, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D7.setFont(font)
        self.cb_D7.setObjectName("cb_D7")
        self.sb_rep_nr = QtWidgets.QSpinBox(Panel)
        self.sb_rep_nr.setGeometry(QtCore.QRect(90, 663, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.sb_rep_nr.setFont(font)
        self.sb_rep_nr.setObjectName("sb_rep_nr")
        self.button_full_view = QtWidgets.QPushButton(Panel)
        self.button_full_view.setGeometry(QtCore.QRect(390, 700, 131, 51))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.button_full_view.setFont(font)
        self.button_full_view.setObjectName("button_full_view")
        self.cb_D3 = QtWidgets.QCheckBox(Panel)
        self.cb_D3.setGeometry(QtCore.QRect(80, 733, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D3.setFont(font)
        self.cb_D3.setObjectName("cb_D3")
        self.cb_D5 = QtWidgets.QCheckBox(Panel)
        self.cb_D5.setGeometry(QtCore.QRect(140, 733, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D5.setFont(font)
        self.cb_D5.setObjectName("cb_D5")
        self.label_repNr = QtWidgets.QLabel(Panel)
        self.label_repNr.setGeometry(QtCore.QRect(20, 663, 61, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_repNr.setFont(font)
        self.label_repNr.setObjectName("label_repNr")
        self.cb_D4 = QtWidgets.QCheckBox(Panel)
        self.cb_D4.setGeometry(QtCore.QRect(140, 713, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D4.setFont(font)
        self.cb_D4.setObjectName("cb_D4")
        self.cb_A1 = QtWidgets.QCheckBox(Panel)
        self.cb_A1.setGeometry(QtCore.QRect(260, 733, 41, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_A1.setFont(font)
        self.cb_A1.setObjectName("cb_A1")
        self.cb_D6 = QtWidgets.QCheckBox(Panel)
        self.cb_D6.setGeometry(QtCore.QRect(200, 713, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D6.setFont(font)
        self.cb_D6.setObjectName("cb_D6")
        self.label_nr_steps_finelaser_2 = QtWidgets.QLabel(Panel)
        self.label_nr_steps_finelaser_2.setGeometry(QtCore.QRect(20, 620, 321, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.label_nr_steps_finelaser_2.setFont(font)
        self.label_nr_steps_finelaser_2.setObjectName("label_nr_steps_finelaser_2")
        self.button_zoom_out = QtWidgets.QPushButton(Panel)
        self.button_zoom_out.setGeometry(QtCore.QRect(600, 640, 61, 51))
        font = QtGui.QFont()
        font.setPointSize(30)
        self.button_zoom_out.setFont(font)
        self.button_zoom_out.setObjectName("button_zoom_out")
        self.cb_D1 = QtWidgets.QCheckBox(Panel)
        self.cb_D1.setGeometry(QtCore.QRect(20, 733, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D1.setFont(font)
        self.cb_D1.setObjectName("cb_D1")
        self.cb_D0 = QtWidgets.QCheckBox(Panel)
        self.cb_D0.setGeometry(QtCore.QRect(20, 710, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D0.setFont(font)
        self.cb_D0.setObjectName("cb_D0")
        self.radioButton = QtWidgets.QRadioButton(Panel)
        self.radioButton.setGeometry(QtCore.QRect(770, 640, 181, 20))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.radioButton.setFont(font)
        self.radioButton.setObjectName("radioButton")
        self.button_cursors = QtWidgets.QPushButton(Panel)
        self.button_cursors.setGeometry(QtCore.QRect(530, 700, 131, 51))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.button_cursors.setFont(font)
        self.button_cursors.setObjectName("button_cursors")
        self.label_c0 = QtWidgets.QLabel(Panel)
        self.label_c0.setGeometry(QtCore.QRect(770, 670, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_c0.setFont(font)
        self.label_c0.setObjectName("label_c0")
        self.label_c1 = QtWidgets.QLabel(Panel)
        self.label_c1.setGeometry(QtCore.QRect(770, 700, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_c1.setFont(font)
        self.label_c1.setObjectName("label_c1")
        self.label_diff = QtWidgets.QLabel(Panel)
        self.label_diff.setGeometry(QtCore.QRect(770, 730, 101, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_diff.setFont(font)
        self.label_diff.setObjectName("label_diff")
        self.text_c1 = QtWidgets.QLabel(Panel)
        self.text_c1.setGeometry(QtCore.QRect(880, 700, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.text_c1.setFont(font)
        self.text_c1.setText("")
        self.text_c1.setObjectName("text_c1")
        self.text_diff = QtWidgets.QLabel(Panel)
        self.text_diff.setGeometry(QtCore.QRect(880, 730, 101, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.text_diff.setFont(font)
        self.text_diff.setText("")
        self.text_diff.setObjectName("text_diff")
        self.text_c0 = QtWidgets.QLabel(Panel)
        self.text_c0.setGeometry(QtCore.QRect(880, 670, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.text_c0.setFont(font)
        self.text_c0.setText("")
        self.text_c0.setObjectName("text_c0")

        self.retranslateUi(Panel)
        QtCore.QMetaObject.connectSlotsByName(Panel)

    def retranslateUi(self, Panel):
        _translate = QtCore.QCoreApplication.translate
        Panel.setWindowTitle(_translate("Panel", "Panel"))
        self.label_view_time.setText(_translate("Panel", "Zoom"))
        self.cb_D2.setText(_translate("Panel", "D2"))
        self.cb_A0.setText(_translate("Panel", "A0"))
        self.botton_zoom_in.setText(_translate("Panel", "+"))
        self.cb_D7.setText(_translate("Panel", "D7"))
        self.button_full_view.setText(_translate("Panel", "Full View"))
        self.cb_D3.setText(_translate("Panel", "D3"))
        self.cb_D5.setText(_translate("Panel", "D5"))
        self.label_repNr.setText(_translate("Panel", "Rep nr"))
        self.cb_D4.setText(_translate("Panel", "D4"))
        self.cb_A1.setText(_translate("Panel", "A1"))
        self.cb_D6.setText(_translate("Panel", "D6"))
        self.label_nr_steps_finelaser_2.setText(_translate("Panel", "[QPLser] - PulseStream Viewer"))
        self.button_zoom_out.setText(_translate("Panel", "-"))
        self.cb_D1.setText(_translate("Panel", "D1"))
        self.cb_D0.setText(_translate("Panel", "D0"))
        self.radioButton.setText(_translate("Panel", "show cursors"))
        self.button_cursors.setText(_translate("Panel", "cursors"))
        self.label_c0.setText(_translate("Panel", "cursor-0:"))
        self.label_c1.setText(_translate("Panel", "cursor-1:"))
        self.label_diff.setText(_translate("Panel", "difference:"))

