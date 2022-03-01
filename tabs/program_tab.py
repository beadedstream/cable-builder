from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from components.cable_component import CableComponent
from lib.file_handler import load_json_cable
from serial_605 import serial_605

class ProgramTab(QWidget):
	def __init__(self, shell_605):
		super(ProgramTab, self).__init__()
		uic.loadUi("ui/tabs/program_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.cable_components = []

		self.verify_cable_btn.clicked.connect(self.verify_cable)
		self.write_to_eeprom_btn.clicked.connect(self.write_to_eeprom)

		self.cable = load_json_cable()

		if not self.cable["has_eeprom"]:
			self.write_to_eeprom_btn.setEnabled(False)

		self.sensor_widgets:list = []
		self.generate_built_cable()

	def write_to_eeprom(self):
		pass

	def verify_cable(self):
		self.update_response_text("Error Text")
		pass

	def generate_built_cable(self):
		h_layout = QHBoxLayout()
		h_layout.addWidget(CableComponent("", self.cable["connector"] + ".jpg"))
		first_sensor = self.cable["sensors"][0]

		cable_color = ""
		if self.cable["initial_cableColor"].find("armor") != -1:
			cable_color = "armored_"
		
		if "zero_marker_length" in self.cable.keys():
			h_layout.addWidget(CableComponent(str(self.cable["zero_marker_length"]), cable_color + "cable.jpg"))
			h_layout.addWidget(CableComponent("","zero_marker.jpg"))
			h_layout.addWidget(CableComponent(str(round(first_sensor["position"] - self.cable["zero_marker_length"], 5)), "cable.jpg"))
		else:
			h_layout.addWidget(CableComponent(str(first_sensor["position"]), cable_color + "cable.jpg"))

		p_text:str = ""
		extra_sensor:int = 0
		# if first sensor has a protection board
		if first_sensor["component"].lower().find("protection") != -1:
			p_text = "_protection"
			extra_sensor = 1
		if first_sensor["mold"].find("90") == -1:
			cc = CableComponent(str(1 - extra_sensor), "mold" + p_text + ".jpg")
		else:
			cc = CableComponent(str(1 - extra_sensor), "mold_RA" + p_text +".jpg")

		h_layout.addWidget(cc)
		self.sensor_widgets.append(cc)

		cable_color = ""
		if first_sensor["cableColor"].lower().find("armor") != -1:
			cable_color = "armored_"
		h_layout.addWidget(CableComponent(str(first_sensor["length"]), cable_color + "cable.jpg"))
		
		total_sensors = len(self.cable["sensors"])
		for i, component in enumerate(self.cable["sensors"][1:]):
			# if 6 components have been added place next set on another row
			if int(h_layout.count()) >= 8:
				self.built_cable_layout.addLayout(h_layout)
				h_layout = QHBoxLayout()

			if component["mold"].find("90") == -1:
				cc = CableComponent(str((i+2) - extra_sensor), "mold" + "" + ".jpg")
			else:
				cc = CableComponent("", "mold_RA" + "" +".jpg")

			h_layout.addWidget(cc)
			self.sensor_widgets.append(cc)

			if (i+1) != total_sensors-1:
				h_layout.addWidget(CableComponent(str(component["length"]), "cable.jpg"))

		if int(h_layout.count()) != 0:
			self.built_cable_layout.addLayout(h_layout)

	def update_response_text(self, txt, is_err = True):
		if is_err:
			self.response_text.setStyleSheet("QLabel { background-color : red;}")
		else:
			self.response_text.setStyleSheet("QLabel { background-color : green; color : black; }")

		self.response_text.setText(txt)

	def update_cable(self):
		self.cable = load_json_cable()