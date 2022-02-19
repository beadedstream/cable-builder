from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from components.cable_component import CableComponent
from lib.file_handler import load_json_cable
from serial_605 import serial_605

class BuildTab(QWidget):
	def __init__(self, shell_605):
		super(BuildTab, self).__init__()
		uic.loadUi("ui/tabs/build_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.test_cable_btn.clicked.connect(self.test_cable)

		self.cable = load_json_cable()
		self.sensor_widgets:list = []
		self.generate_cable()

	def generate_cable(self):

		h_layout = QHBoxLayout()
		h_layout.addWidget(CableComponent("", "bare.jpg"))
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
		
		# if first sensor has a protection board
		if first_sensor["component"].lower().find("protection") != -1:
			cc = CableComponent("", "sensor_protection.jpg")
		else:
			cc = CableComponent("", "sensor.jpg")

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
				self.cable_layout.addLayout(h_layout)
				h_layout = QHBoxLayout()

			cc = CableComponent("", "sensor.jpg")
			h_layout.addWidget(cc)
			self.sensor_widgets.append(cc)

			if (i+1) != total_sensors-1:
				h_layout.addWidget(CableComponent(str(component["length"]), "cable.jpg"))

		if int(h_layout.count()) != 0:
			self.cable_layout.addLayout(h_layout)
		
	def test_cable(self):
		info_on_cables =  self.shell.initialize_cables()

		eeprom_id:str
		extra_sensor_id:str

		for cable_info in info_on_cables():
			if cable_info["port"] == '2' and cable_info["slot"] == 1:
				if cable_info["has_eeprom"]:
					if self.cable["is_mlink"] or self.cable["sensors"][0].lower().find("protection") != -1:
						self.update_response_text("This cable is not suppose to have an EEProm", is_err = True)
						return
					
				else:
					if self.cable["is_mlink"]:
						self.update_response_text("Missing MLink board", is_err = True)
						return
					elif self.cable["sensors"][0].lower().find("protection") != -1:
						self.update_response_text("Missing protection board", is_err = True)
						return

				if int(cable_info["sensors"]) > len(self.cable["sensors"]):
					self.update_response_text(cable_info["sensors"] + " sensors found on cable. Only " + str(len(self.cable["sensors"])) + " needed", is_err = True)
					return
				if int(cable_info["sensors"]) < len(self.cable["sensors"]):
					self.update_response_text("Too many sensors found on cable", is_err = True)
					return
			else:
				self.update_response_text("Cable not found. Make sure to plug cable into port 2", is_err = True)
				return
		
		self.shell.read_sensor_temperatures(self.cable["serial"])

		for widget in self.sensor_widgets:
			widget.set_label("0.0C")
		self.update_response_text("Pass")

	def update_response_text(self, txt, is_err = False):
		if is_err:
			self.response_text.setStyleSheet("QLabel { background-color : red;}")
		else:
			self.response_text.setStyleSheet("QLabel { background-color : green; color : black; }")

		self.response_text.setText(txt)