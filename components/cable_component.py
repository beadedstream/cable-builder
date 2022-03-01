from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QWidget

class CableComponent(QWidget):
	def __init__(self, top_label_text, img_name):
		super(CableComponent, self).__init__()
		uic.loadUi("ui/components/cable_component.ui", self)
		self.img_folder = "components/images/"
		self.max_img_height = 32

		self.top_label.setText(top_label_text)
		self.img_obj = QPixmap(self.img_folder + img_name).scaledToHeight(self.max_img_height)
		self.img.setPixmap(self.img_obj)
		#self.setMinimumSize(self.img_obj.width(), self.max_img_height+25)

	def set_top_label(self, text):
		# is usually a sensor id or spacing
		self.top_label.setText(text)

	def set_bottom_label(self, text):
		self.bottom_label.setText(text)

	def place_img(self, img_name):
		self.img.setPixmap(QPixmap(self.img_folder + img_name).scaledToHeight(self.max_img_height))

	def labels_to_img_dimensions(self):
		self.img.resize(self.img_obj.width(), self.max_img_height)

	def change_background_color(self, default=False):
		if default:
			self.setStyleSheet("QWidget { background-color : white;}")
			return

		self.setStyleSheet("QWidget { background-color : red;}")