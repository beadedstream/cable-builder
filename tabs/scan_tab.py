from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QTableWidget, QGridLayout, QMessageBox
from serial_605 import serial_605
from components.sensor_component import SensorComponent
from random import randrange
from time import sleep

class ScanTab(QWidget):
	def __init__(self, shell_605):
		super(ScanTab, self).__init__()
		uic.loadUi("ui/tabs/scan_tab.ui", self)
		self.shell:serial_605 = shell_605
		self.sensor_ids:list = []
		self.total_sensors = 0
		self.img_folder = "components/images/PCBA"
		self.tray_char = 'A'
		self.tray_num = 0
		self.sensors_scanned = 0

		self.scan_sensors_btn.clicked.connect(self.add_sensor)
		self.sort_sensors_btn.clicked.connect(self.sort_sensors)
		self.replace_sensor_btn.clicked.connect(self.replace_sensor)
		#self.sensor_table.clicked.connect(self.replace_sensor)

		# q = QTableWidget()
		# q.removeCellWidget()

	def scan_sensors(self):

		# TODO: create a 605 method for reading sensor ids from a specific port without reinitialing cables
		ids:list = self.shell.read_ids(1,1)

		iint = 0
		while i < (self.total_sensors - 1):

			if len(ids) > 1:
				QMessageBox.critical(self, "Sensor Not Selected", "Need to select a sensor before repacing one")
				return

			if ids == None:
				print("No sensors found on cable. Re-scanning...")
				return

			id = ids[0]

			if len(id) == 16 and id[-2:] == '28':
				self.add_sensor(id[2:-2])
			else:
				QMessageBox.critical(self, "Invalid Id found", "Sensor with id " + id + " found.")

			i+=1
			sleep(2)

	def add_sensor(self):
		id = self.generate_id()
		readable_id = id[0] + id[1]
		for i in range(2, len(id), 2):
			readable_id += " " + id[i] + id[i+1]
		comp = SensorComponent(self.tray_char+str(self.tray_num+1), readable_id)

		self.sensor_table.horizontalHeader().setDefaultSectionSize(comp.get_img_width())
		self.sensor_table.setCellWidget(int(self.sensors_scanned / 6), self.sensors_scanned % 6, comp)
		self.sensors_scanned += 1
		self.tray_num += 1
		if self.tray_num == 30:
			self.tray_num = 0
			self.tray_char = chr(ord(self.tray_char) + 1)

		self.sensor_ids.append(id)

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
			self.sensor_table.cellWidget(int(i / 6), i % 6).set_order_number(str(total[1]))

		self.sort_sensors_btn.setEnabled(False)
		# return [[new_sen_order[i], sorted_ids[i]] for i in range(len(reversed_hex_totals))]

	def replace_sensor(self):
		cell_widget = self.sensor_table.cellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn())

		if cell_widget == None:
			QMessageBox.critical(self, "Sensor Not Selected", "Need to select a sensor before repacing one")
			return

		cell_widget.set_id("00 00 00 12 A6 3C")

	def delete_sensor(self):

		if self.sensor_table.cellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn()) == None:
			QMessageBox.critical(self, "Sensor Not Selected", "Need to select a sensor before repacing one")
			return

		self.sensor_table.removeCellWidget(self.sensor_table.currentRow(), self.sensor_table.currentColumn())

	def update_sensor_total(self, sensor_num):
		self.total_sensors = sensor_num