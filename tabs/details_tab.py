from re import T
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QFileDialog, QTabWidget, QInputDialog
import json
from lib.file_handler import write_cable_to_json
from lib.helper import convert_mm_to_dimension

from components.serial_dialog import SerialDialog
from lib.api import API

class DetailsTab(QWidget):
	def __init__(self, parent_widget):
		super(DetailsTab, self).__init__()

		uic.loadUi("ui/tabs/details_tab.ui", self)
		self.sensor_components = []

		self.get_by_serial_btn.clicked.connect(self.load_from_database)
		self.load_json_btn.clicked.connect(self.get_json_file)
		self.serial_comboBox.addItem("")
		self.json_dir:str = ""
		self.current_ids:list = []

		self.default_dimension = "cm"
		self.parent_widget = parent_widget

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

	def load_from_database(self):
		api = API()
		ser_dialog = SerialDialog("Type Serial Number to pull from the database", api)
		ser_dialog.disable_ignore()
		

		if ser_dialog.exec_() == -1: # if cancel
			return -1
			
		seri = ser_dialog.serial

		db_response = api.get_cable_by_serial(seri)
		if isinstance(db_response, str):
			QMessageBox.critical("DB issue", "Error: " + db_response)
			return

		if "cable" not in db_response:
			QMessageBox.critical("Error", "Cable not found" + db_response)

		self.parse_cable_obj(db_response["cable"], seri)
		self.serial_comboBox.setItemText(0, seri)
		self.parent_widget.serial_selected(seri, from_db = True)

	# def serial_selected(self, serial_num):
	# 	if serial_num != "":
	# 		with open(self.json_dir) as f:
	# 			cable_obj = json.load(f)

	# 		if isinstance(cable_obj, list):
	# 			for cable in cable_obj:
	# 				if int(serial_num) in cable["serial"]:
	# 					if not any(x in self.current_ids for x in cable["serial"]):
	# 						self.parse_cable_obj(cable)
	# 					else:
	# 						print("Cable already generated")
	# 		else:
	# 			self.parse_cable_obj(cable_obj)

	def parse_cable_obj(self, cable_obj, serial_num):
		self.current_ids = cable_obj["serial"]

		cable:dict = {}
		cable["display_units"] = self.default_dimension
		cable["sensors"] = []
		cable["serial"] = serial_num
		cable["connector"] = cable_obj["connector"]

		if "productionComment" in cable_obj.keys():
			cable["comment"] = cable_obj["productionComment"]
		
		if cable_obj["mlink"]:
			cable["is_mlink"] = True
			cable["has_eeprom"] = True
		else: 
			cable["is_mlink"] = False

		# TODO: create more cable colors and rename the pics to match the lowered cased color name
		cable["initial_cableColor"] = cable_obj["lead"][0]["cableColor"].lower()
		cable["lead"] = cable_obj["lead"][0]["length"]

		previous_position = 0

		for i, component in enumerate(cable_obj["body"]):
			c = component["component"].lower()
			if c.find("sensor") != -1:
				order = int(c.split(" ")[-1])
				component["order"] = order
				component["section"] = round(component["position"] - previous_position, 5)
				cable["sensors"].append(component)

				if order == 1:
					# if protection board aka eeprom is found and recognized as being in the same mold as the first sensor
					if c.find("protection") != -1:
						cable["has_eeprom"] = True
					
			elif c.find("zero") != -1:
				cable["zero_marker_length"] = component["length"]
				cable["zero_marker_position"] = component["position"] + cable["lead"]
			
			previous_position = component["position"]

			if len(cable_obj["body"]) == i+1:
				cable["total_length"] = component["position"]
				if component["mold"]["type"].lower().find("end") == -1:
					err_txt = "Could not find end mold for cable with serial(s)"
					if isinstance(cable_obj["serial"], list):
						for x in cable_obj["serial"]:
							err_txt += " " + str(x)
					else:
						err_txt += " " + str(cable_obj["serial"])
					
					QMessageBox.critical(self, "Missing End Mold", err_txt)

		write_cable_to_json(cable)
		self.load_cable_details(cable)

	def load_cable_details(self, cable):
		# defining cable details
		self.sensor_num_text.setText(str(len(cable["sensors"])))
		self.lead_text.setText(str(convert_mm_to_dimension(cable["lead"], self.default_dimension)) + self.default_dimension)
		self.connector_text.setText(cable["connector"])
		self.section_label.setText("Section" + " ("+self.default_dimension+")")
		self.total_length_text.setText(str(convert_mm_to_dimension(cable["total_length"], self.default_dimension)) + self.default_dimension)

		if "comment" in cable.keys():
			self.note_text.setText(cable["comment"])

		sensor_sects = ["component", "mold", "section", "cableColor"]
		# if "zero_marker_length" in cable.keys():
		# 	self.component_text.setText
		# 	sensor_details += "\n" + "zero marker" +"\t"+ "marker" +"\t\t"+ str(cable["zero_marker_length"]) + cable["units"] +"\t\t"+ "----"

		for sect in sensor_sects:
			temp_str = ""
			for s in cable["sensors"]:
				temp_str += "\n"
				if sect == "mold":
					temp_str += s["mold"]["type"]
				elif sect == "section":
					temp_str += str(convert_mm_to_dimension(s[sect], self.default_dimension)) 
				else:
					temp_str += s[sect]
				
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