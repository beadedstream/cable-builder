import time
import serial
import serial.rs485
from serial.serialutil import SerialTimeoutException, SerialException
import serial.tools.list_ports
from lib.helper import close_application
from sys import platform

class usb_serial:

	def __init__(self, baud:int, read_timeout:float, write_timeout:float = 20, device_type ="usb"):

		self.ser = serial.Serial(None, baud, timeout=read_timeout,
								parity=serial.PARITY_NONE, rtscts=False,
								xonxoff=False, dsrdtr=False, write_timeout=write_timeout)

		self.default_timeout = read_timeout
		self.device_type = device_type
		self.port_number:int = -1

	def search_for_port(self, ignore_ports:list = []):
		ports: list = []
		inp = 'r'
		fmt = '{:<10} {:<10}'

		while inp == 'r':
			ports = list(set(self.find_devices()).difference(ignore_ports))

			if len(ports) == 1:
				self.set_port(ports[0])
				return

			elif len(ports) > 1:
				fmt = '{:<10} {:<10}'
				inp = 'r'

				print(fmt.format("Port #", "Port Name"))

				for i, p in enumerate(ports):
					print(fmt.format(str(i+1), p))

				inp = input("Type port # to connect, r to refresh list, or anything else to quit: ").lower()

				while inp.isdigit():
					# TODO: fix this, device number can be greater than the amount plugged in
					if abs(int(inp)) > len(ports):
						close_application("Wrong port # typed")
					else:
						self.set_port(ports[int(inp)-1])
						return

			else:
				print("Unable to find device that works with this application. Closing program...")
				break

		close_application("")

	def send_command(self, command: str, timeout: float = 0, output: bool = True, to_file: bool = True):
		if timeout != 0:
			self.ser.timeout = timeout
		
		if self.connected_to_port():
			self.ser.flush()

			try:
				self.ser.write((command + "\n").encode())
				txt = self.ser.read_until("\n").decode()
				return txt

			except:
				print("There was an error reading the command. Please check spelling")
				return

		else:
			print("Serial port closed; please make sure the serial port is opened.")
		return

	def connected_to_port(self):
		if (not self.ser.is_open):
			try: 
				self.ser.open()
			except:
				return False

		return True

	def find_devices(self):
		# works on both windows and linux
		ports_of_type:list = []
		
		for comport in serial.tools.list_ports.comports():
			if comport.description.upper().find(self.device_type.upper()) != -1:
				ports_of_type.append(comport.device)

		return ports_of_type

	def set_timeout(self, read_timeout):
		self.ser.timeout = read_timeout

	def set_port(self, port_name:str):
		self.ser.close()
		if port_name != None:

			if platform == "linux":# Ex usb device name: USB0
				self.port_number = int(port_name[port_name.rfind("B") + 1 : ])

			if platform == "windows":# Ex usb device name: COM3
				self.port_number = int(port_name[port_name.rfind("M") + 1 : ])

		self.ser.port = port_name

	def set_device_type(self, device_type):
		self.device_type = device_type

	def get_port_name(self):
		return self.ser.name