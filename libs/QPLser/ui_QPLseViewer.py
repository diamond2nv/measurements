# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QPLser_view.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import h5py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2*np.pi*t)
        self.axes.plot(t, s)


class Ui_Panel(object):
    def setupUi(self, Panel):
        Panel.setObjectName("Panel")
        Panel.resize(1155, 750)
        self.button_save = QtWidgets.QPushButton(Panel)
        self.button_save.setGeometry(QtCore.QRect(940, 672, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.button_save.setFont(font)
        self.button_save.setObjectName("button_save")
        self.plot_canvas = QtWidgets.QVBoxLayout(Panel)
        self.plot_canvas.setGeometry(QtCore.QRect(10, 10, 1131, 561))
        self.plot_canvas.setObjectName("plot_canvas")
        self.sc = MyStaticMplCanvas(self.plot_canvas, width=5, height=4, dpi=100)

        self.lineEdit_fileTag = QtWidgets.QLineEdit(Panel)
        self.lineEdit_fileTag.setGeometry(QtCore.QRect(940, 710, 181, 20))
        self.lineEdit_fileTag.setObjectName("lineEdit_fileTag")
        self.label_fileTag = QtWidgets.QLabel(Panel)
        self.label_fileTag.setGeometry(QtCore.QRect(880, 710, 51, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.label_fileTag.setFont(font)
        self.label_fileTag.setObjectName("label_fileTag")
        self.sb_rep_nr = QtWidgets.QSpinBox(Panel)
        self.sb_rep_nr.setGeometry(QtCore.QRect(100, 650, 81, 31))
        self.sb_rep_nr.setObjectName("sb_rep_nr")
        self.label_view_time = QtWidgets.QLabel(Panel)
        self.label_view_time.setGeometry(QtCore.QRect(540, 680, 151, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.label_view_time.setFont(font)
        self.label_view_time.setObjectName("label_view_time")
        self.label_repNr = QtWidgets.QLabel(Panel)
        self.label_repNr.setGeometry(QtCore.QRect(30, 650, 61, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.label_repNr.setFont(font)
        self.label_repNr.setObjectName("label_repNr")
        self.dsb_view_time = QtWidgets.QDoubleSpinBox(Panel)
        self.dsb_view_time.setGeometry(QtCore.QRect(541, 711, 81, 21))
        self.dsb_view_time.setObjectName("dsb_view_time")
        self.Hscrollbar = QtWidgets.QScrollBar(Panel)
        self.Hscrollbar.setGeometry(QtCore.QRect(10, 580, 1131, 21))
        self.Hscrollbar.setPageStep(50)
        self.Hscrollbar.setOrientation(QtCore.Qt.Horizontal)
        self.Hscrollbar.setObjectName("Hscrollbar")
        self.cb_D0 = QtWidgets.QCheckBox(Panel)
        self.cb_D0.setGeometry(QtCore.QRect(30, 687, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D0.setFont(font)
        self.cb_D0.setObjectName("cb_D0")
        self.cb_D1 = QtWidgets.QCheckBox(Panel)
        self.cb_D1.setGeometry(QtCore.QRect(30, 710, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D1.setFont(font)
        self.cb_D1.setObjectName("cb_D1")
        self.cb_D3 = QtWidgets.QCheckBox(Panel)
        self.cb_D3.setGeometry(QtCore.QRect(90, 710, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D3.setFont(font)
        self.cb_D3.setObjectName("cb_D3")
        self.cb_D2 = QtWidgets.QCheckBox(Panel)
        self.cb_D2.setGeometry(QtCore.QRect(90, 690, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D2.setFont(font)
        self.cb_D2.setObjectName("cb_D2")
        self.cb_D5 = QtWidgets.QCheckBox(Panel)
        self.cb_D5.setGeometry(QtCore.QRect(150, 710, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D5.setFont(font)
        self.cb_D5.setObjectName("cb_D5")
        self.cb_D4 = QtWidgets.QCheckBox(Panel)
        self.cb_D4.setGeometry(QtCore.QRect(150, 690, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D4.setFont(font)
        self.cb_D4.setObjectName("cb_D4")
        self.cb_D7 = QtWidgets.QCheckBox(Panel)
        self.cb_D7.setGeometry(QtCore.QRect(210, 710, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D7.setFont(font)
        self.cb_D7.setObjectName("cb_D7")
        self.cb_D6 = QtWidgets.QCheckBox(Panel)
        self.cb_D6.setGeometry(QtCore.QRect(210, 690, 61, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_D6.setFont(font)
        self.cb_D6.setObjectName("cb_D6")
        self.cb_A1 = QtWidgets.QCheckBox(Panel)
        self.cb_A1.setGeometry(QtCore.QRect(300, 710, 41, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_A1.setFont(font)
        self.cb_A1.setObjectName("cb_A1")
        self.cb_A0 = QtWidgets.QCheckBox(Panel)
        self.cb_A0.setGeometry(QtCore.QRect(300, 690, 51, 17))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        self.cb_A0.setFont(font)
        self.cb_A0.setObjectName("cb_A0")
        self.comboBox_units = QtWidgets.QComboBox(Panel)
        self.comboBox_units.setGeometry(QtCore.QRect(630, 710, 73, 22))
        self.comboBox_units.setObjectName("comboBox_units")
        self.label_nr_steps_finelaser_2 = QtWidgets.QLabel(Panel)
        self.label_nr_steps_finelaser_2.setGeometry(QtCore.QRect(30, 610, 251, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.label_nr_steps_finelaser_2.setFont(font)
        self.label_nr_steps_finelaser_2.setObjectName("label_nr_steps_finelaser_2")

        self.retranslateUi(Panel)
        QtCore.QMetaObject.connectSlotsByName(Panel)

    def retranslateUi(self, Panel):
        _translate = QtCore.QCoreApplication.translate
        Panel.setWindowTitle(_translate("Panel", "Panel"))
        self.button_save.setText(_translate("Panel", "SAVE view"))
        self.label_fileTag.setText(_translate("Panel", "file tag:"))
        self.label_view_time.setText(_translate("Panel", "View time interval"))
        self.label_repNr.setText(_translate("Panel", "Rep nr"))
        self.cb_D0.setText(_translate("Panel", "D0"))
        self.cb_D1.setText(_translate("Panel", "D1"))
        self.cb_D3.setText(_translate("Panel", "D3"))
        self.cb_D2.setText(_translate("Panel", "D2"))
        self.cb_D5.setText(_translate("Panel", "D5"))
        self.cb_D4.setText(_translate("Panel", "D4"))
        self.cb_D7.setText(_translate("Panel", "D7"))
        self.cb_D6.setText(_translate("Panel", "D6"))
        self.cb_A1.setText(_translate("Panel", "A1"))
        self.cb_A0.setText(_translate("Panel", "A0"))
        self.label_nr_steps_finelaser_2.setText(_translate("Panel", "QPLser - Stream Viewer"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Panel = QtWidgets.QWidget()
    ui = Ui_Panel()
    ui.setupUi(Panel)
    Panel.show()
    sys.exit(app.exec_())

