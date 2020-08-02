import math
import PyQt5
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtWidgets import (
    QDialog,QGridLayout,QVBoxLayout,QFrame, QLabel,QMessageBox,QWidget
)
from PyQt5.uic.properties import QtWidgets


class Page_Dialog():
    def __init__(self,hex_list,temp_list):
        super.__init__()
        self.test_gridlayout = QGridLayout()
        self.frame_list = []

        for i in range(sizeof(hex_list)):
            self.frame_list.append(self.test_frame(hex_list[i],temp_list[i]))
            self.test_gridlayout.addWidget(0,i,self.frame_list[i])

        self.send_back()

    def test_frame(self,hex,temps):
        box_frame = QFrame()
        box_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        box_frame.setFrameShadow(QtWidgets.QFrame.Raised)

        hex_label = QtWidgets.QLabel(box_frame)
        hex_label.setGeometry(QtCore.Rect(0, 0, 10, 10))
        hex_label.setFont(self.fonts(10,10,True))
        hex_label.setText("Sensor Hex: ", hex)

        temp_label = QtWidgets.QLabel(box_frame)
        temp_label.setGeometry(QtCore.Rect(10, 10, 100, 100))
        temp_label.setFont(self.fonts(10,10,True))
        temp_label.setText("Temperature: ", str(temps))

        if temps > 40:
            box_frame.setAutoFillBackground(True)
            box_frame.setPalette(self.palette(255,139,119))
        return box_frame

    def fonts(self,ptSize, weigth, bold):
            font = QtGui.QFont()
            font.setFamily("System")
            font.setPointSize(ptSize)
            font.setBold(bold)
            font.setWeight(weigth)
            return font

    def palette(self, red, green, blue):
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(red, green, blue))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        return palette

    def send_back(self):
        return self.test_gridlayout