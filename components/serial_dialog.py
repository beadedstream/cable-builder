from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

class SerialDialog(QDialog):
	def __init__(self, text, api):
		super(SerialDialog, self).__init__()

		uic.loadUi("./ui/components/serial_dialog.ui", self)
		self.label.setText(text)
		self.api = api

		self.serial:str = ""

		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

		self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
		self.setWindowFlag(Qt.WindowCloseButtonHint, False)

		self.buttonBox.accepted.connect(self.valid)
		self.buttonBox.rejected.connect(self.invalid)
		self.buttonBox.button(QDialogButtonBox.Ignore).clicked.connect(self.ignore)
		
		self.serial_lineEdit.textChanged.connect(self.validate_serial)

	def validate_serial(self):
		text = self.serial_lineEdit.text()

		if len(text) < 4:
			pass
		elif len(text) > 4:
			self.error_label.setText("Serial number is too long")

		elif not all([x.isdigit() for x in text if x != '']):
			self.error_label.setText("Serial can not contain any numbers")

		else:
			err_msg = self.validate_api_call(self.api.get_cable_by_serial(text))

			if err_msg != "":
				self.error_label.setText(err_msg)
			else:
				self.error_label.setText("")
				self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
				self.serial = text
				return

		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

	def validate_api_call(self, response:dict):
		for key in response.keys():
			if key == "error":
				return response[key]
			if response[key] == []:
				return "No record found in database"

		return ""

	def disable_ignore(self):
		self.buttonBox.button(QDialogButtonBox.Ignore).setEnabled(False)

	def get_serial(self):
		return self.serial

	# define return values
	def valid(self):
		self.done(1)

	def invalid(self):
		self.done(-1)

	def ignore(self):
		self.done(0)