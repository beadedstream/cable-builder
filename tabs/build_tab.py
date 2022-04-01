from tkinter.tix import Tree
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from components.cable_component import CableComponent
from lib.file_handler import load_json_cable
from lib.helper import convert_mm_to_dimension
from serial_605 import serial_605

class BuildTab(QWidget):
	def __init__(self, shell_605):
		super(BuildTab, self).__init__()
		uic.loadUi("ui/tabs/build_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.test_cable_btn.clicked.connect(self.test_cable)

		self.cable = load_json_cable()
		self.units = self.cable["display_units"]
		self.sensor_widgets:list = []
		self.generate_cable()
		
	def generate_cable(self):

		h_layout = QHBoxLayout()
		h_layout.addWidget(CableComponent("", "bare.jpg"))
		first_sensor = self.cable["sensors"][0]
		extra_sensor:int = 0

		cable_color = ""
		if self.cable["initial_cableColor"].find("armor") != -1:
			cable_color = "armored_"
		
		if "zero_marker_length" in self.cable.keys():
			h_layout.addWidget(CableComponent(str(self.cable["zero_marker_length"]), cable_color + "cable.jpg"))
			h_layout.addWidget(CableComponent("","zero_marker.jpg"))
			h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(self.cable["zero_marker_length"]), self.units), "cable.jpg"))
		else:
			h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(self.cable["lead"], self.units)), cable_color + "cable.jpg"))
		
		# if first sensor has a protection board
		if first_sensor["component"].lower().find("protection") != -1:
			cc = CableComponent("0", "sensor_protection.jpg")
			extra_sensor = 1
		else:
			cc = CableComponent("1", "sensor.jpg")

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
				self.cable_layout.addLayout(h_layout)
				h_layout = QHBoxLayout()
				h_layout.setAlignment(Qt.AlignLeft)

			cc = CableComponent(str((i+2) - extra_sensor), "sensor.jpg")
			h_layout.addWidget(cc)
			self.sensor_widgets.append(cc)

			if component["cableColor"].lower().find("armor") != -1:
				cable_color = "armored_"

			if (i+1) != total_sensors-1:
				h_layout.addWidget(CableComponent(str(convert_mm_to_dimension(component["length"], self.units)), cable_color + "cable.jpg"))

		if int(h_layout.count()) != 0:
			self.cable_layout.addLayout(h_layout)
		
	def test_cable(self):
		info_on_cables =  self.shell.initialize_cables()

		eeprom_id:str #IMPLEMENT

		extra_sensor:int = 0
		# if cable has extra sensor that can't be scanned
		if self.cable["has_eeprom"] and not self.cable["is_mlink"]: extra_sensor = 1

		cable_info:dict = {}

		# Testing if cable is in the right slot and port
		for c_info in info_on_cables:
			if c_info["port"] == '2' or c_info["slot"] == 1:
				cable_info = c_info

		if not cable_info: # if cable_info is empty
			self.update_response_text("Cable not found. Make sure to plug cable into port 2")
			return

		# Testing if cable is suppose to and does or doesn't have an EEPROM or Mlink
		if not self.cable["has_eeprom"]:
			if cable_info["has_eeprom"]:
				self.update_response_text("This cable is not suppose to have an Eeprom")
				return
		elif not cable_info["has_eeprom"]:
			if self.cable["is_mlink"]:
				self.update_response_text("Missing MLink board")
				return
			elif not self.cable["is_mlink"] and self.cable["has_eeprom"]:
				self.update_response_text("Missing protection board")
				return

		# Testing if the correct number of sensors are found on the cable
		if int(cable_info["sensors"]) > (len(self.cable["sensors"])):
			self.update_response_text(cable_info["sensors"] + " sensors found on cable. Only " + str(len(self.cable["sensors"])) + " needed")
			return

		cable_ids = self.shell.read_ids(cable_info["generated_serial"])
		
		# Test for missing or wrong ids 
		if not self.validate_ids(cable_ids):
			return

		# Test if id's match with those from a scanned list minus the sensor with the same mold as the eeprom
		# Next, parse out that subtracted sensor and use it's id to sort and store a sorted list of ids on the eeprom
		if cable_info["has_eeprom"] and not self.cable["is_mlink"]:
			if not self.sort_and_write_serial(self.cable["serial"], cable_ids):
				return
			else:
				cable_info["generated_serial"] = self.cable["serial"]

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

	def sort_and_write_serial(self, serial:str, cable_ids):
		# when the 605 reads a cable it checks if a serial can be found in the metadata
		# if found, it pulls a sorted list of ids from the eeprom (if id's are found)
		self.shell.write_serial("1", "2", serial)

		id_difference:list = []
		for id in cable_ids:
			if id not in self.cable["sensor_ids"]:
				id_difference.append(id)

		if len(id_difference) != 1 or (len(cable_ids) - 1) != len(self.cable["sensor_ids"]):
			self.update_response_text("Something went wrong, try again")
			return False

		self.shell.sort_and_write_sensors(serial, sensor_id=id_difference[0])
		return True

	def validate_ids(self, cable_ids):

		# with_eeprom:int = 0
		# # if cable has extra sensor that can't be scanned
		# if self.cable["has_eeprom"] and not self.cable["is_mlink"]: with_eeprom = 1

		id_difference:list = []

		for id in self.cable["sensor_ids"]:
			if id not in cable_ids:
				id_difference.append(id)

		if len(id_difference) > 0:
			missing_ids:str = ""
			for id in id_difference:
				missing_ids += " " + id
			
			self.update_response_text("Missing id(s) " + missing_ids, is_err = True)
			return False

		return True

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