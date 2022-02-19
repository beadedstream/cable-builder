from PyQt5 import uic
from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QTableWidget, QGridLayout, QMessageBox, QPushButton
from serial_605 import serial_605
from components.sensor_component import SensorComponent
from random import randrange
from lib.file_handler import load_json_cable

class ScanTab(QWidget):
	def __init__(self, shell_605):
		super(ScanTab, self).__init__()
		uic.loadUi("ui/tabs/scan_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.sensor_ids:list = []

		cable = load_json_cable()["sensors"]
		self.total_sensors:int = len(cable["sensors"])
		if cable["sensors"][0].lower().find("protection") != -1:
			self.total_sensors -= 1

		del cable

		self.img_folder = "components/images/PCBA"
		self.tray_char = 'A'
		self.tray_num = 0
		self.sensors_scanned = 0

		self.scan_sensors_btn:QPushButton

		self.scan_sensors_btn.clicked.connect(self.scan_sensors)
		self.sort_sensors_btn.clicked.connect(self.sort_sensors)
		self.replace_sensor_btn.clicked.connect(self.replace_sensor)
		
		self.sort_sensors_btn.setEnabled(False)
		self.replace_sensor_btn.setEnabled(False)
		#self.sensor_table.clicked.connect(self.replace_sensor)

	def scan_sensors(self):
		
		i:int = 0
		last_sensor:str = ""

		self.scan_sensors_btn.setEnabled(False)

		while i < (self.total_sensors):
			ids:list = self.shell.find_sensors_on_port(1,1)

			if len(ids) > 1:
				QMessageBox.critical(self, "Too many ids", "Found multiple sensor ids. Can only scan one sensor at a time")

			elif len(ids) == 0:
				print("No sensors found on cable. Re-scanning...")

			elif ids[0] == last_sensor:
				print("No sensors found on cable. Re-scanning...")

			elif len(ids[0]) == 16 and ids[0][-2:] == '28':

				if ids[0] in self.sensor_ids:
					QMessageBox.critical(self, "Invalid id found", "Sensor with id " + ids[0] + " already scanned.")
				else:
					last_sensor = ids[0]
					self.add_sensor(ids[0])
					i+=1
			else:
				QMessageBox.critical(self, "Invalid id found", "Sensor with id " + ids[0] + " found.")

			loop = QEventLoop()
			QTimer.singleShot(500, loop.quit)
			loop.exec()

		self.sort_sensors_btn.setEnabled(True)
		self.replace_sensor_btn.setEnabled(True)

	def add_sensor(self, id):

		#id = self.generate_id()
		comp = SensorComponent(self.tray_char + str(self.tray_num + 1), self.format_id(id))

		self.sensor_table.horizontalHeader().setDefaultSectionSize(comp.get_img_width())
		self.sensor_table.setCellWidget(int(self.sensors_scanned / self.sensor_table.columnCount()), self.sensors_scanned % self.sensor_table.columnCount(), comp) #row, col, widget

		self.sensors_scanned += 1
		self.tray_num += 1
		if self.tray_num == 30:
			self.tray_num = 0
			self.tray_char = chr(ord(self.tray_char) + 1)

		self.sensor_ids.append(id)
		print("sensor with id "+ id + " added")

	def generate_id(self):
		id = "000000"
		for i in range(6):
			id += hex( randrange(16) )[-1]

		return id

	def sort_sensors(self, ignore_sen = 0):
		reversed_hex_totals:list = []

		for order_num, id in enumerate(self.sensor_ids):
			total:int = 0

			i:int = 2
			while(id[i] == '0'): i += 1
			# removing crc, leading 0's after crc, and family code. Reads ids from right to left
			for i, hex_char in enumerate(id[i:-2][::-1]):
				# converting char to int to binary string
				# [2:] removes '0b' from binary string and zfill adds filler bits
				# [::-1] reverses binary string
				reversed_binary = bin(int(hex_char, 16))[2:].zfill(4)[::-1]
				if i == 0:
					# string to base 2 int
					total = int(reversed_binary, 2)
				else:
					# left shift 4 and add in 4 LSBs -> ex: 1001 0000 + 0000 0101
					total = (total << 4) + int(reversed_binary, 2)

			reversed_hex_totals.append([total, order_num+1])
		# combining totals and ids and sorting by totals from lowest to highest
		print(reversed_hex_totals)
		
		# sorted_ids = [x for _, x in sorted(zip(reversed_hex_totals, self.sensor_ids))]
		# print(sorted_ids)

		reversed_hex_totals.sort(key=lambda pair: pair[0])
		print(reversed_hex_totals)

		for i, total in enumerate(reversed_hex_totals):
			self.sensor_table.cellWidget(int(i / self.sensor_table.columnCount()), i % self.sensor_table.columnCount()).set_order_number(str(total[1]))

		self.sort_sensors_btn.setEnabled(False)
		# return [[new_sen_order[i], sorted_ids[i]] for i in range(len(reversed_hex_totals))]

	def replace_sensor(self):
		cell_widget = self.sensor_table.cellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn())

		if cell_widget == None:
			QMessageBox.critical(self, "Sensor Not Selected", "Need to select a sensor before repacing one")
			return

		while True:
			ids:list = self.shell.find_sensors_on_port(1,1)

			if len(ids) > 1:
				QMessageBox.critical(self, "Too many ids", "Found multiple sensor ids. Can only scan one sensor at a time")

			elif len(ids) == 0:
				print("No sensors found on cable. Re-scanning...")

			elif len(ids[0]) == 16 and ids[0][-2:] == '28' and ids[0][:2] == '00':

				if ids[0] in self.sensor_ids:
					QMessageBox.critical(self, "Invalid id found", "Sensor with id " + ids[0] + " already scanned.")
				else:
					cell_widget.set_id(self.format_id(ids[0]))
					sensor_number = (self.sensor_table.currentRow() * self.sensor_table.columnCount()) + (self.sensor_table.currentColumn() + 1)
					self.sensor_ids[sensor_number - 1] = ids[0]
					print(self.sensor_ids)
					return
			else:
				QMessageBox.critical(self, "Invalid id found", "Sensor with id " + ids[0] + " found.")

			loop = QEventLoop()
			QTimer.singleShot(500, loop.quit)
			loop.exec()

	def delete_sensor(self):

		if self.sensor_table.cellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn()) == None:
			QMessageBox.critical(self, "Sensor Not Selected", "Need to select a sensor before repacing one")
			return

		self.sensor_table.removeCellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn())

	
	def update_sensor_total(self, sensor_num):
		self.total_sensors = sensor_num

	def format_id(self, id):

		formatted_id = id[2] + id[3]
		# removes crc and family code
		for i in range(4, len(id)-2, 2):
			formatted_id += " " + id[i] + id[i+1]

		return formatted_id

	