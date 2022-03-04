from re import T
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QFileDialog, QTabWidget
import json
import os
from lib.file_handler import write_cable_to_json

class DetailsTab(QWidget):
	def __init__(self):
		super(DetailsTab, self).__init__()

		uic.loadUi("ui/tabs/details_tab.ui", self)
		self.sensor_components = []

		self.load_json_btn.clicked.connect(self.get_json_file)
		self.serial_comboBox.addItem("")
		self.json_dir:str = ""
		self.current_ids:list = []

	def get_json_file(self):
		file_dir = QFileDialog.getOpenFileName(self, 'Open file', '.',"Json file (*.json)")[0]
		if file_dir == "":
			return

		with open(file_dir) as f:
			cable_objs = json.load(f)

		if isinstance(cable_objs, list):
			for cable in cable_objs:
				self.serial_comboBox.addItems([str(x) for x in cable["serial"]])
		else:
			self.serial_comboBox.addItems([str(x) for x in cable_objs["serial"]])

		self.json_dir = file_dir

	def serial_selected(self, serial_num):
		if serial_num != "":
			with open(self.json_dir) as f:
				cable_obj = json.load(f)

			if isinstance(cable_obj, list):
				for cable in cable_obj:
					if int(serial_num) in cable["serial"]:
						if not any(x in self.current_ids for x in cable["serial"]):
							self.parse_cable_obj(cable)
						else:
							print("Cable already generated")
			else:
				self.parse_cable_obj(cable_obj)

	def read_from_api(self):
		pass

	def parse_cable_obj(self, cable_obj, serial_num):
		self.current_ids = cable_obj["serial"]

		cable:dict = {}
		cable["sensors"] = []
		cable["units"] = cable_obj["units"]
		cable["serial"] = serial_num
		cable["connector"] = cable_obj["cable"][0]["component"]
		cable["lead"] = cable_obj["cable"][0]["length"]
		cable["total_length"] = cable["lead"]

		if "productionComment" in cable_obj.keys():
			cable["comment"] = cable_obj["productionComment"]
		
		if cable_obj["cable"][1]["component"].find("no mlink") != 1:
			cable["is_mlink"] = False
		else: 
			cable["is_mlink"] = True
			cable["has_eeprom"] = True

		cable["initial_cableColor"] = cable_obj["cable"][1]["cableColor"].lower()

		for i, component in enumerate(cable_obj["cable"]):
			c = component["component"].lower()
			if c.find("sensor") != -1:
				order = int(c.split(" ")[-1])
				component["order"] = order
				component["section"] = round(component["position"] - previous_position, 5)
				cable["sensors"].append(component)

				if order == 1:
					# if protection board aka eeprom prom is found and recognized as being in the same mold as the first sensor
					if c.find("protection") != -1:
						cable["has_eeprom"] = True
					
			elif c.find("zero") != -1:
				cable["zero_marker_length"] = cable["lead"]
				cable["lead"] = cable["lead"] + component["length"]
			
			previous_position = component["position"]

			if len(cable_obj["cable"]) == i+1:
				cable["total_length"] = component["position"]
				if component["mold"].lower().find("end") == -1:
					err_txt = "Could not find end mold for cable with serial(s)"
					for x in cable_obj["serial"]:
						err_txt += " " + str(x)
					QMessageBox.critical(self, "Missing End Mold", err_txt)

		write_cable_to_json(cable)
		self.load_cable_details(cable)

	def load_cable_details(self, cable):
		# defining cable details
		self.sensor_num_text.setText(str(len(cable["sensors"])))
		self.lead_text.setText(str(cable["lead"]) + cable["units"])
		self.connector_text.setText(cable["connector"])
		self.section_label.setText("Section" + " ("+cable["units"]+")")
		self.total_length_text.setText(str(cable["total_length"]))
		# self.total_length_text.setText(str(cable["total_length"]) + cable["units"])

		if "comment" in cable.keys():
			self.note_text.setText(cable["comment"])

		sensor_sects = ["component", "mold", "section", "cableColor"]
		# if "zero_marker_length" in cable.keys():
		# 	self.component_text.setText
		# 	sensor_details += "\n" + "zero marker" +"\t"+ "marker" +"\t\t"+ str(cable["zero_marker_length"]) + cable["units"] +"\t\t"+ "----"

		for sect in sensor_sects:
			temp_str = ""
			for s in cable["sensors"]:
				temp_str += "\n" + str(s[sect])
				
			if sect == "component":
				self.component_text.setText(temp_str)
			if sect == "mold":
				self.mold_text.setText(temp_str)
			if sect == "section":
				self.section_text.setText(temp_str)
			if sect == "cableColor":
				self.type_text.setText(temp_str)

		if "zero_marker_length" in cable.keys():
			self.component_text.setText("zero_marker" + self.component_text.text())
			self.mold_text.setText("marker"+ self.mold_text.text())
			self.section_text.setText(str(cable["zero_marker_length"]) + self.section_text.text())
			self.type_text.setText("------" + self.type_text.text())