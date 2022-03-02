from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PopupBox(QMessageBox):
	def __init__(self):
		super(PopupBox, self).__init__()

	def critical_message(self, description:str, msg:str):
		self.critical(self, description, msg)

	def info_message(self, description:str, msg:str):
		self.information(self, description, msg)

	def warning_message(self, description:str, msg:str):
		self.warning(self, description, msg)