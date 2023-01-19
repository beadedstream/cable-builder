from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from components.cable_component import CableComponent
from lib.file_handler import load_json_cable
from serial_605 import serial_605
from datetime import datetime
from lib.helper import convert_mm_to_dimension

class ProgramTab(QWidget):
	def __init__(self, shell_605):
		super(ProgramTab, self).__init__()
		uic.loadUi("ui/tabs/program_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.cable_components = []
		

		self.verify_cable_btn.clicked.connect(self.verify_cable)
		self.write_to_eeprom_btn.clicked.connect(self.write_to_eeprom)

		self.cable = load_json_cable()
		self.units = self.cable["display_units"]

		if not self.cable["has_eeprom"]:
			self.write_to_eeprom_btn.setEnabled(False)

		self.sensor_widgets:list = []
		self.generate_built_cable()

	def check_eeprom(self, cable_info=False):
		check = False

		if not cable_info:
			info_on_cables = self.shell.initialize_cables()

			# Testing if cable is in the right slot and port
			for c_info in info_on_cables:
				if c_info["port"] == '2' or c_info["slot"] == 1:
					cable_info = c_info

		if not cable_info: # if cable_info is empty
			self.update_response_text("Cable not found. Make sure to plug cable into port 2")
			return False

		# Testing if cable is suppose to and does or doesn't have an EEPROM or Mlink
		if not self.cable["has_eeprom"]:
			if cable_info["has_eeprom"]:
				self.update_response_text("This cable is not suppose to have an Eeprom")
				return False
		elif not cable_info["has_eeprom"]:
			if self.cable["is_mlink"]:
				self.update_response_text("Missing MLink board")
				return
			elif not self.cable["is_mlink"] and self.cable["has_eeprom"]:
				self.update_response_text("Missing protection board")
				return False

		return True

	def write_to_eeprom(self):
		if not self.check_eeprom():
			return

		self.shell.write_serial("1", "2", self.cable["serial"])
		# write exact positions - lead
		if self.cable["is_mlink"]:
			self.shell.write_ids_to_eeprom(self.cable["serial"])
		#else: this step is already done

		positions:list = []
		for s in self.cable["sensors"]:
			positions.append(s["position"])

		self.shell.write_spacings(self.cable["serial"], positions)
		self.write_metadata()

	def write_metadata(self):
		connector_to_first = 0
		connector_to_zero = 0
		
		for sensor in self.cable["sensors"]:
			if sensor["component"].split(" ")[-1] == '1':
				connector_to_first = self.cable["lead"] + sensor["position"]

		pairs:dict = {
			"date_created": datetime.utcnow().strftime("%m%d%y"),
			"lead": connector_to_first,
			"connect_to_0"
			"coefficients": "43.0,-0.18,0.000139",
			"manufacturer": "Beadedstream",
			"cable_type": "DTC"
		}

		if "zero_marker_length" in self.cable.keys():
			pairs["connect_to_0"] = self.cable["zero_marker_position"]

		for key in pairs:
			self.shell.write_metadata(self.cable["serial"], key, pairs[key])

	def verify_cable(self):

		info_on_cables = self.shell.initialize_cables()

		for c_info in info_on_cables:
			if c_info["port"] == '2' or c_info["slot"] == 1:
				cable_info = c_info

		if not self.check_eeprom(cable_info=cable_info):
			return

		# Testing if the correct number of sensors are found on the cable
		if int(cable_info["sensors"]) > (len(self.cable["sensors"])):
			self.update_response_text(cable_info["sensors"] + " sensors found on cable. Only " + str(len(self.cable["sensors"])) + " needed")
			return

		cable_ids = self.shell.read_ids(cable_info["generated_serial"])
		
		# Test for missing or wrong ids 
		if not self.validate_ids(cable_ids):
			return

		# Test if part of or the entire cable is parasitically powered
		pwr_results = self.shell.run_sensor_pwr_test(cable_info["generated_serial"])
		if isinstance(pwr_results, list):
			failed = False
			for i, result in enumerate(pwr_results):
				if result.lower() == "parasitic":
					self.append_response_text("Position " + str(i) + " Power Failure")
					self.sensor_widgets[i].change_background_color()
					failed = True
			if failed:
				return
		else:
			if pwr_results.lower() == "parasitic":
				self.update_response_text("Cable Power Failure")
				return

		# Test cable temperatures
		self.shell.set_offsets_to_0(cable_info["generated_serial"]) # removes any preloaded offsets
		temps = self.shell.read_sensor_temperatures(cable_info["generated_serial"])
		# writing temps to screen
		for i, widget in enumerate(self.sensor_widgets):
			widget.set_bottom_label(str(temps[i]) + "C")

		failed = False

		# checking for valid temps
		for i, widget in enumerate(self.sensor_widgets):
			# TODO: output muliple failures
			if temps[i] >= 90:
				self.append_response_text("Position " + str(i) + "Failed")
				widget.change_background_color()
				failed = True

			elif (temps[i] > 84) and (temps[i] <= 86):
				self.append_response_text("Position " + str(i) + " Power Failure")
				widget.change_background_color()
				failed = True

		if not failed:
			self.update_response_text("Test passed", is_err=False)

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
			h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(self.cable["zero_marker_length"], self.units)), "cable.jpg"))
		else:
			h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(self.cable["lead"], self.units)), cable_color + "cable.jpg"))

		p_text:str = ""
		extra_sensor:int = 0
		# if first sensor has a protection board
		if first_sensor["component"].lower().find("protection") != -1:
			p_text = "_protection"
			extra_sensor = 1
		if first_sensor["mold"]["type"].find("90") == -1:
			cc = CableComponent(str(1 - extra_sensor), "mold" + p_text + ".jpg")
		else:
			cc = CableComponent(str(1 - extra_sensor), "mold_RA" + p_text +".jpg")

		h_layout.addWidget(cc)
		self.sensor_widgets.append(cc)

		cable_color = ""
		if first_sensor["cableColor"].lower().find("armor") != -1:
			cable_color = "armored_"
		h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(first_sensor["length"], self.units)), cable_color + "cable.jpg"))
		
		total_sensors = len(self.cable["sensors"])
		for i, component in enumerate(self.cable["sensors"][1:]):
			cable_color = ""
			# if 6 components have been added place next set on another row
			if int(h_layout.count()) >= 8:
				self.built_cable_layout.addLayout(h_layout)
				h_layout = QHBoxLayout()
				h_layout.setAlignment(Qt.AlignLeft)

			if component["mold"]["type"].find("90") == -1:
				cc = CableComponent(str((i+2) - extra_sensor), "mold" + "" + ".jpg")
			else:
				cc = CableComponent("", "mold_RA" + "" +".jpg")

			h_layout.addWidget(cc)
			self.sensor_widgets.append(cc)

			if component["cableColor"].lower().find("armor") != -1:
				cable_color = "armored_"

			if (i+1) != total_sensors-1:
				h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(component["length"], self.units)), cable_color + "cable.jpg"))

		if int(h_layout.count()) != 0:
			self.built_cable_layout.addLayout(h_layout)

	def update_response_text(self, txt, is_err = True):
		if is_err:
			self.response_text.setStyleSheet("QLabel { background-color : red;}")
		else:
			self.response_text.setStyleSheet("QLabel { background-color : green; color : black; }")

		self.response_text.setText(txt)

	def append_response_text(self, text):

		old_text = self.response_text.text()

		if old_text == "":
			self.response_text.setStyleSheet("QLabel { background-color : red;}")

		self.response_text.setText(old_text + text + "\n")

	def update_cable(self):
		self.cable = load_json_cable()