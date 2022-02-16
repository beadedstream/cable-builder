import csv
from lib.helper import close_application
from serial_605 import serial_605

shell = serial_605()

def main():
	pass

def detect_and_connect_605():
	ports = shell.find_devices()

	if len(ports) == 0:
		close_application("Need a least one device plugged in")

	for port in ports:
		if shell.get_port_name() == None:
			shell.set_port(port)
			if shell.is_605_shell():
				break
			shell.set_port(None)

	if shell.get_port_name() == None:
		close_application("Failed to find 605. May need to wait a couple of seconds if device was just powered on.")

def sort_sensors(hex_ids:list):
	reversed_hex_totals:list = []

	for id in hex_ids:
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
				total = (total << 4) + int(reversed_binary, 2)

		reversed_hex_totals.append(total)
	# combining totals and ids and sorting by totals from lowest to highest
	print(reversed_hex_totals)
	return [x for _, x in sorted(zip(reversed_hex_totals, hex_ids))]

def save_to_csv():
	pass

if __name__ == "__main__":
	# serial = input("Type serial number of cable")
	# shell.set_to_config_mode()
	# cables = shell.initialize_cables()
	
	# ids:list = []
	# ids.append(scan_sensor(cables[0]))
	hex_ids = ["ZZ0030bc21728", "ZZ0030be0c328", "ZZ0030b9d9928", "ZZ0030bf7bc28", "ZZ0030bde3c28"]
	
	hex_ids = sort_sensors(hex_ids)
	print(hex_ids)