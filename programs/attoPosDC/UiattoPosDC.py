# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'attoPosDC.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(424, 366)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.formLayout_2 = QtWidgets.QFormLayout(Dialog)
        self.formLayout_2.setObjectName("formLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.formLayout_2.setLayout(3, QtWidgets.QFormLayout.LabelRole, self.formLayout)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(72)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.label_2 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(72)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.Y = QtWidgets.QDoubleSpinBox(Dialog)
        self.Y.setEnabled(True)
        self.Y.setMinimumSize(QtCore.QSize(0, 100))
        font = QtGui.QFont()
        font.setPointSize(90)
        self.Y.setFont(font)
        self.Y.setDecimals(1)
        self.Y.setMaximum(150.0)
        self.Y.setProperty("value", 150.0)
        self.Y.setObjectName("Y")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.Y)
        self.X = QtWidgets.QDoubleSpinBox(Dialog)
        self.X.setEnabled(True)
        self.X.setMinimumSize(QtCore.QSize(0, 100))
        font = QtGui.QFont()
        font.setPointSize(90)
        self.X.setFont(font)
        self.X.setDecimals(1)
        self.X.setMaximum(150.0)
        self.X.setProperty("value", 150.0)
        self.X.setObjectName("X")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.X)
        self.label_3 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(72)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.Z = QtWidgets.QDoubleSpinBox(Dialog)
        self.Z.setEnabled(True)
        self.Z.setMinimumSize(QtCore.QSize(0, 100))
        font = QtGui.QFont()
        font.setPointSize(90)
        self.Z.setFont(font)
        self.Z.setDecimals(1)
        self.Z.setMaximum(150.0)
        self.Z.setProperty("value", 150.0)
        self.Z.setObjectName("Z")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.Z)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "X "))
        self.label_2.setText(_translate("Dialog", "Y "))
        self.label_3.setText(_translate("Dialog", "Z "))

