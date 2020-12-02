import math
import PyQt5
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtWidgets import (
    QDialog,QGridLayout,QVBoxLayout,QFrame, QLabel,QMessageBox,QWidget
)
from PyQt5.uic.properties import QtWidgets


class Page_Dialog():
    def __init__(self,hex_list,temp_list):
        #super.__init__()
        self.page = QDialog()
        self.test_gl = QGridLayout()
        self.left_frame = QFrame()
        self.right_frame = QFrame()
        self.left_gbox = QGridLayout()
        self.right_gbox = QGridLayout()

        self.page.setLayout(self.test_gl)
        self.test_gl.addWidget(self.left_frame,1,0)
        self.test_gl.addWidget(self.right_frame,1,1)

        self.left_frame.setLayout(self.left_gbox)
        self.right_frame.setLayout(self.right_gbox)
        self.page.exec()
        self.send_back()
        self.left_frame_list = []
        self.right_frame_list = []
        #left
        self.install_frames(self.left_frame_list,hex_list,temp_list[0])
        #right
        self.install_frames(self.right_frame_list,hex_list,temp_list[1])

        self.list_to_grid(self.left_frame_list)
        self.list_to_grid(self.right_frame_list)

        self.send_back()
    def list_to_grid(self,list):
        x = 0
        for frame in range(len(list)):
            self.left_gbox.addWidget(list[frame],x,0)
            x += 1

    def install_frames(self,list,hex,temp):
        for i in range(len(hex)):
            list.append(self.test_frame(hex[i], temp[i]))
            self.test_gl.addWidget(0, i, list[i])

    def test_frame(self,hex,temps):
        box_frame = QFrame()
        # box_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        # box_frame.setFrameShadow(QtWidgets.QFrame.Raised)

        hex_label = QtWidgets.QLabel(box_frame)
        hex_label.setGeometry(QtCore.Rect(0, 0, 10, 10))
        hex_label.setPixmap(QtGui.QPixmap("Sensor_PCBA.jpg"))
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
        return self.page