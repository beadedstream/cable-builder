from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QWidget

class SensorComponent(QWidget):
	def __init__(self, cell_text, id):
		super(SensorComponent, self).__init__()
		uic.loadUi("ui/components/sensor_component.ui", self)
		self.max_img_height = 65
		self.cell_num.setText(cell_text)
		self.id.setText(id)
		
		self.img_folder = "ui/components/images/"
		# default img
		self.img = QPixmap(self.img_folder + "PCBA").scaledToHeight(self.max_img_height)
		self.sensor_img.setPixmap(self.img)

	def set_cell_text(self, text):
		self.cell_text.setText(text)

	def set_order_number(self, text):
		self.order_num.setText(text)

	def set_id(self, text):
		self.id.setText(text)

	def get_order_number(self):
		return self.order_num.text()

	def place_img(self, img_name):
		self.sensor_img.setPixmap(QPixmap(self.img_folder + img_name).scaledToHeight(self.max_img_height))

	def get_img_width(self):
		margins = self.gridLayout.getContentsMargins()
		# left and right margins
		return self.img.width() + margins[0] + margins[2]