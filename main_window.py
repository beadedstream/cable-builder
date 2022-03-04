from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTabWidget
from serial_605 import serial_605
from lib.file_handler import update_json_field

from tabs.details_tab import DetailsTab
from tabs.scan_tab import ScanTab
from tabs.build_tab import BuildTab
from tabs.program_tab import ProgramTab
from serial_605 import serial_605
import time
import sys
import json
import os

from lib.popup_box import PopupBox

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

os.chdir(application_path)

class Ui(QMainWindow):
	def __init__(self):
		super(Ui, self).__init__() # Call the inherited classes __init__ method
		uic.loadUi('ui/main.ui', self) # Load the .ui file
		self.show() # Show the GUI
		self.popup_box = PopupBox()
		self.shell = serial_605(self.popup_box)

		while not self.detect_and_connect_605():
			pass

		self.details_tab = DetailsTab()
		self.details_tab.serial_comboBox.currentTextChanged.connect(self.serial_selected)
		self.tabWidget.tabBarClicked.connect(self.clicked_tabbar)

		self.tabWidget.addTab(self.details_tab, "Cable Details")
		self.show() # Show the GUI

	def detect_and_connect_605(self):
		ports = self.shell.find_devices()

		if len(ports) == 0:
			QMessageBox.critical(self, "No devices found", "Need a least one device plugged in")
			return False

		for port in ports:
			if self.shell.get_port_name() == None:
				self.shell.set_port(port)
				if self.shell.is_605_shell():
					break
				self.shell.set_port(None)

		if self.shell.get_port_name() == None:
			QMessageBox.critical(self, "Connection Failure", "Failed to find 605. May need to wait a couple of seconds if device was just powered on.")
			return False
		
		return True

	def serial_selected(self, serial_num):
		if serial_num != "":
			with open(self.details_tab.json_dir) as f:
				cable_obj = json.load(f)

			if isinstance(cable_obj, list):
				for cable in cable_obj:
					if int(serial_num) in cable["serial"]:
						if not any(x in self.details_tab.current_ids for x in cable["serial"]):
							self.details_tab.parse_cable_obj(cable, serial_num)
						else:
							print("Cable already generated")
							update_json_field("serial", serial_num)
							return
							
			else: # if single cable build found
				self.details_tab.parse_cable_obj(cable_obj, serial_num)

		# all tab info is generated based from the current_cable file generated by the details tab
		if self.tabWidget.count() > 1:
			for i in range(self.tabWidget.count(), 0, -1):
				self.tabWidget.removeTab(i)

		self.tabWidget.addTab(ScanTab(self.shell, self.tabWidget), "Scan and Sort")
		self.tabWidget.addTab(BuildTab(self.shell), "Build")
		self.tabWidget.addTab(ProgramTab(self.shell), "Program")

	def clicked_tabbar(self, index):
		if index == 2 or index == 3:
			# makes sure build and program tabs hold the most recent cable information
			self.tabWidget.widget(index).update_cable()

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = Ui()
	sys.exit(app.exec_())