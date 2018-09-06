# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scan_gui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from measurements.libs.QPLser import StreamCanvas as SC


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(786, 286)
        self.pushButton_save = QtWidgets.QPushButton(Form)
        self.pushButton_save.setGeometry(QtCore.QRect(590, 40, 93, 28))
        font = QtGui.QFont()
        font.setFamily("MS Sans Serif")
        font.setPointSize(12)
        self.pushButton_save.setFont(font)
        self.pushButton_save.setObjectName("pushButton_save")
        self.pushButton_start = QtWidgets.QPushButton(Form)
        self.pushButton_start.setGeometry(QtCore.QRect(590, 80, 93, 28))
        font = QtGui.QFont()
        font.setFamily("MS Sans Serif")
        font.setPointSize(12)
        self.pushButton_start.setFont(font)
        self.pushButton_start.setObjectName("pushButton_start")
        self.doubleSpinBox_xmin = QtWidgets.QDoubleSpinBox(Form)
        self.doubleSpinBox_xmin.setGeometry(QtCore.QRect(50, 230, 101, 31))
        self.doubleSpinBox_xmin.setSingleStep(0.5)
        self.doubleSpinBox_xmin.setProperty("value", 2.0)
        self.doubleSpinBox_xmin.setObjectName("doubleSpinBox_xmin")
        #self.vbl = QtWidgets.QVBoxLayout(Form)
        #self.vbl.setContentsMargins(0,0,0,0)
        #self.canvas = SC.MplCanvas(Form, width=7, height=3, dpi=200)
        #self.vbl.addWidget (self.canvas)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_save.setText(_translate("Form", "SAVE"))
        self.pushButton_start.setText(_translate("Form", "START"))

