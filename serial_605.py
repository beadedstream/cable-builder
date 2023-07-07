from enum import unique
from queue import Empty
import time
from lib.helper import write_to_log
from lib.popup_box import PopupBox
from lib.usb_serial import usb_serial

from lib.api import API
from datetime import datetime
from colorama import Style, Fore

calibration_cmd_prefix = "dtc"
onewire_cmd_prefix = "1wire"
class serial_605(usb_serial):

	def __init__(self, popup_box):
		# write and read timeouts don't matter when talking with the zephyr shell
		usb_serial.__init__(self, 115200, 0.5, 10)
		self.popup_box = popup_box

	def send_command(self, command: str, timeout: float = 0, output: bool = True, to_file: bool = True):
		terminal_lines: list = []
		read_wait: float = 0.2
		t: float = 0
		
		cmd_ready_color: str = '\033[1;32m'
		warn_color: str = '\033[1;33m'
		err_color: str = '\033[1;31m'
		end_color: str = '\033[0m'
		
		if self.connected_to_port():
			self.ser.timeout = timeout
			self.ser.flush()

			try:
				self.ser.write((command + '\r\n').encode())
				read_first_line:bool = False
				
				while True:
					time.sleep(read_wait)
					if t > timeout and timeout != 0:
						break
					
					t += read_wait
					txt:str = self.ser.read_all().decode()

					if txt.find('\n') != -1:
						split_text:list = txt.split('\r\n')
						for i, line in enumerate(split_text):
							line = line.replace('\r', "")
							if read_first_line == False:
								# first line contains the command that was typed
								read_first_line = True

								if to_file:
									write_to_log(line)

								continue
							
							if line == "":
								continue
							
							if line.find(cmd_ready_color) != -1:
								if output:
									# adds any trailing text that may be outputted after a command is done running.
									if len(split_text) > i+1:
										if split_text[i+1].count('\033') == 0:
											terminal_lines.append(split_text[i+1])
									return terminal_lines
							
							if line.count('\033') == 1: # if line contains no closing color bracket add one
								line += end_color

							terminal_lines.append(line)

							if to_file:
								write_to_log(line)
							
							if line.find(err_color) != -1:
								# if an error was given by the 605, print it and quit application
								line = line.replace(err_color, "").replace(end_color, "")
								self.popup_box.critical_message("605 Error", line)
								return
								
							if line.find(warn_color) != -1:
								# if a warning was given, print it and continue
								line = line.replace(err_color, "").replace(end_color, "")
								self.popup_box.critical_message("605 Warning", Fore.YELLOW + Style.BRIGHT + line + Style.RESET_ALL)
								return
					
					if t - int(t) == 0:
						# prevents function from stalling aka able to grab cmd ready text
						# by doing this every second
						self.ser.write(('\r\n').encode())
						self.ser.write(('\r\n').encode())
			except:
				self.popup_box.critical_message("Error", "There was an error reading the command. Please check spelling")
				return

			self.popup_box.critical_message("Error", "Timeout or error when sending command, may need to reset device")
			return

		else:
			self.popup_box.critical_message("Error", "Serial port closed; please make sure the serial port is opened.")
			return
		return

	#### WRITE COMMANDS ####

	def set_to_config_mode(self):
		self.send_command("app configure", timeout=0.2)
		return

	def initialize_cables(self, slot:str = None):
		cmd:str = calibration_cmd_prefix + " get_cables"
		data:list = []

		data = self.send_command(cmd, timeout = 200)
		if data == None:
			self.popup_box.critical_message("605 No Working", "Plug-in or reboot 605 and try again")
			return

		slot:str = 0
		cable_array:list = []

		for i in range(len(data)):
			if len(data) == 1:
				self.popup_box.critical_message("Cables Not Found", "No cables found; the ground and power may be swapped on one of the cables.")
				return

			if data[i].find("slot: ")!= -1:
				slot = data[i][-1]
				i += 1
				
				if i == len(data):
					break

				
				while data[i].find("port: ") != -1 :
					try:
						nums = data[i].replace("port: ", "").replace("serial: ", "").replace("sensors: ", "").replace("eeprom: ", "").split(" ")
						cable_data:dict = {
							"slot": slot,
							"port": nums[0], 
							"generated_serial": nums[1],
							"sensors": nums[2],
							"has_eeprom": True
						}
						if nums[3] == "none":
							cable_data["has_eeprom"] = False

						cable_array.append(cable_data)

						i += 1
						if i == len(data):
							break
					except:
						self.popup_box.critical_message("Unknown Error", "Something went wrong when pulling cable data from 605. Try running application again")
						return

		if len(cable_array) == 0:
			self.popup_box.critical_message("No Cables", "unable to find cables")
			return

		cable_array.sort(key=lambda cable: cable["port"])

		i:int = 0
		while i < len(cable_array):
			
			current_slot = cable_array[i]["slot"]

			print("Cables in slot " + str(current_slot))
			print("port#\t\tserial#\t\tsensors\t\thas eeprom")
			
			while cable_array[i]["slot"] == current_slot:
				print(cable_array[i]["port"] +"\t\t", end="")
				if len(cable_array[i]["generated_serial"]) > 4:
					print("unknown", end="")
				else:
					print(cable_array[i]["generated_serial"], end="")

				print("\t\t"+ cable_array[i]["sensors"] +"\t\t"+ str(cable_array[i]["has_eeprom"]))
				
				i += 1
				if i == len(cable_array):
					break
		
		return cable_array

	def sort_and_write_sensors(self, serial:str, sensor_id:str = None):
		cmd = calibration_cmd_prefix + " sort " + serial

		if sensor_id != None:
			# if we know the first sensor id before calibrating, then heating it can be skipped
			sensor_id = self.reverse_id(sensor_id)
			data = self.send_command(cmd + " " + sensor_id)
		else:
			input("Heat up first sensor for a minuet and press enter: ")
			data = self.send_command(cmd)

		ids: list = []
		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", "").replace('\n', ""))

		self.reverse_ids(ids)
		return ids

	# used for mlink cables only
	# ids are stored in the 605 memory so there is no need to read then write
	def write_ids_to_eeprom(self, serial:str):
		
		data = self.send_command(calibration_cmd_prefix + " write_ids " + serial)
		ids: list = []
		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", "").replace('\n', ""))

		return ids

	def write_spacings(self, serial:str, mm_spacings:list):
		# eeprom now stores spacing between sensors instead of spacings between ids
		spacings_str: str = str(mm_spacings[0])

		for spacing in mm_spacings[1:]:
			spacings_str += '_' + str(spacing)

		# will need to increase zephyr shell buffer size limit
		data = self.send_command(calibration_cmd_prefix + " write_spacings " + serial + " " + spacings_str)

		# return something?
		return

	def write_temps_as_offsets(self, real_temperature:float, serial:str = None, sensor_number:str = None):
		cmd:str = calibration_cmd_prefix + " write_temps " + str(int(real_temperature * 1000))
		data:list = []

		if serial != None:
			data = self.send_command(cmd + " " + serial)
		else:
			data = self.send_command(cmd)

		offsets: list = []
		for line in data:
			if line.find("offset: ") != -1:
				# offsets appear are written and read as whole numbers
				offsets.append(float(line.replace("offset: ", "").replace('\n', "")) / 1000)

		return offsets

	def write_metadata(self, serial:str, key:str, value:str, index:str = None):
		cmd = calibration_cmd_prefix + " write_meta " + serial + " "
		
		if index != None: # optional argument
			self.send_command(cmd + key + " " + value + " " + index)
		else:
			self.send_command(cmd + key + " " + value)

		return

	def set_offsets_to_0(self, serial:str = None):
		cmd = calibration_cmd_prefix + " offsets_0"

		if serial != None:
			self.send_command(cmd + " " + serial)
		else:
			self.send_command(cmd)

	def clear_eeprom_data(self, serial:str, section:str):

		data = self.send_command(calibration_cmd_prefix + " clear " + serial + " " + section)

	#### READ COMMANDS ####

	def find_sensors_on_port(self, slot:int, port:int):
		data = self.send_command(onewire_cmd_prefix + " find_devices " + str(slot) + " " + str(port))

		ids: list = []
		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", "").replace('\n', ""))

		return ids

	def read_ids(self, serial:str):
		data = self.send_command(calibration_cmd_prefix + " ids " + serial)

		ids: list = []
		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", "").replace('\n', ""))

		return ids

	def read_ids_from_eeprom(self, serial:str):
		data = self.send_command(calibration_cmd_prefix + " ids_eeprom " + serial)

		ids: list = []
		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", "").replace('\n', ""))

		return ids

	def read_sensor_temperatures(self, serial:str):

		data = self.send_command(calibration_cmd_prefix + " temps " + serial)

		temps: list = []
		for line in data:
			if line.find("temp: ") != -1:
				temps.append(float(line.replace("temp: ", "").replace('\n', "")))

		return temps

	def read_raw_sensor_temperatures(self, serial:str):

		data = self.send_command(onewire_cmd_prefix + " raw_temps " + serial)

		temps: list = []
		for line in data:
			if line.find("temp: ") != -1:
				temps.append(float(line.replace("temp: ", "").replace('\n', "")))

		return temps

	def read_sensor_offsets(self, serial:str):

		data = self.send_command(calibration_cmd_prefix + " read_offsets " + serial)

		offsets: list = []
		for line in data:
			if line.find("offset: ") != -1:
				offsets.append(round(float(line.replace("offset: ", "").replace('\n', "")), 3))

		return offsets

	def get_ids_from_cable(self, serial:str):
		
		data = self.send_command(calibration_cmd_prefix + " ids " + serial)
		ids: list = []

		for line in data:
			if line.find("id: ") != -1:
				ids.append(line.replace("id: ", ""))

		return ids

	def read_eeprom_id(self, serial:str):

		id:str = ""
		data = self.send_command(calibration_cmd_prefix + " eeprom_id " + serial)

		for line in data:
			if line.find("id: ") != -1:
				if line.find("none") != -1:
					print("Eeprom id for cable not found")
				else:
					id = line.replace("id: ", "").replace('\n', "")

		return id

	def read_metadata(self, serial:str):
		data = self.send_command(calibration_cmd_prefix + " meta " + serial)
		metadata:dict = {}

		for line in data:
			if line.find("meta: ") != -1:
				pair = line.replace("meta: ", "").replace('\n', "").split(" * ")
				metadata.update({pair[0]: pair[1]})

		return metadata

	def read_from_eeprom(self, serial:str, hex_address:str, byte_to_read:str):

		return self.send_command(calibration_cmd_prefix + " read " + serial + " " + hex_address + " " + byte_to_read)

	# changes string so it's in the same format as the ones in the database
	# lists are passed by reference
	def reverse_ids(self, ids:list):

		for index, id in enumerate(ids):
			formatted_id:str = ""

			for i in range(len(id), 0, -2):
				formatted_id += ''.join(id[i-2: i])

			ids[index] = formatted_id

	def is_605_shell(self):
		if self.connected_to_port():
			cmd_ready_color: str = '\033[1;32m'
			
			self.ser.write('\r\n'.encode())
			self.ser.write('\r\n'.encode())
			time.sleep(0.2)
			text:str = self.ser.read_all().decode()

			self.ser.write('\r\n'.encode())
			self.ser.write('\r\n'.encode())
			time.sleep(0.2)
			text += self.ser.read_all().decode()

			if text.count(cmd_ready_color) > 1:
				return True

			return False
		
		print("Couldn't open serial port")
		return False

	def reverse_id(self, id:str):

		if isinstance(id, list):
			id = id[0]

		formatted_id:str = ""

		for i in range(len(id), 0, -2):
			formatted_id += ''.join(id[i-2: i]) # list of chars to str

		return formatted_id

	def set_clock(self):
		utc_seconds = int(datetime.utcnow().timestamp())
		self.send_command("app set_time " + str(utc_seconds))

	def run_sensor_pwr_test(self, serial:str):

		data = self.send_command(calibration_cmd_prefix + " pwr_test " + serial)
		sensor_pwr_results:list = []

		for line in data:
			if line.find("all_pwred: ") != -1:
				return line.replace("all_pwred: ", "").replace('\n', "")

			if line.find("pwred: ") != -1:
				sensor_pwr_results.append(line.replace("pwred: ", "").replace('\n', ""))

		return sensor_pwr_results

if __name__ == "__main__":
	
	shell = serial_605()
	shell.search_for_port()
	# for i in range(1):
	shell.initialize_cables()
	#print(shell.read_eeprom_id("3779"))

	# # set_clock()
	#print(shell.read_metadata("65002"))
	
	# print(sort_and_write_sensors("3660"))

	# print(read_sensor_temperatures("3660"))
	# print(write_temps_as_offsets("3660"))
	# print(initialize_cables())
	# write_serial("1", "1", "3660")
	# print(sort_sensors("3292"))
	# print(get_ids_from_cable("3292"))
	# print(read_cable_offsets("3292"))
	# print(read_eeprom_id("3292"))
	# print(read_metadata("4007"))
	# print(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")[:-7]+"Z") #%S.%f") miliseconds
	# print(datetime.datetime.utcnow().strftime("%m%d%y"))
	# print(API().get_cable_by_serial("3292"))
	# print(len(API().get_cable_build_by_serial("3292")["cables"][-1]["cable"]))
	# print(initialize_cables())
	pass