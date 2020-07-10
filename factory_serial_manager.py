import re
import time
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QDialog


class SerialManager(QObject):
    """Class that handles the serial connection."""
    data_ready = pyqtSignal(int,str)
    no_port_sel = pyqtSignal()
    sleep_finished = pyqtSignal()
    port_unavailable_signal = pyqtSignal()
    no_version = pyqtSignal()
    scan_signal = pyqtSignal(bool)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(None, 115200, timeout=60,
                                 parity=serial.PARITY_NONE, rtscts=False,
                                 xonxoff=False, dsrdtr=False, write_timeout=None)
        self.memory = ''
        self.counter = 0#this counter is not the same as the views file but it does share the same value
        self.new_hexNum = False
        self.page_dialog = QDialog()
        self.hex_memory = []
        self.end = b"\r\n>"

    def scan_ports():
        """Scan and return list of connected comm ports."""
        return serial.tools.list_ports.comports()

    @pyqtSlot(str)
    def sc(self, command):
        """Checks connection to the serial port and sends a command."""
        if self.ser.is_open:
            try:
                # Debug items pt.1
                # then = time.time()
                # print(command)
                self.flush_buffers()

                command = (command + "\r\n").encode()
                self.ser.write(command)
                data = self.ser.read_until(self.end).decode()

                # Debug items pt.2
                # now = time.time()
                # print(now - then)
                # print(data)

                self.data_ready.emit(data)
            except serial.serialutil.SerialException:
                self.no_port_sel.emit()
        else:
            self.no_port_sel.emit()

    @pyqtSlot()
    def wake_up_call(self):
        '''this call keeps the board on and turns off the sleep mode, if desired to sleep either turrn this mode off
         or directly call it to sleep'''
        if self.ser.is_open:
            try:
                self.ser.write("app 0\r\n".encode())
                self.finished.emit()

            except:
                message = QMessageBox.critical(self.page_dialog, "Wake up not possible",
                                               "The board was not able to remain awake")
        else:
            connection_error = QMessageBox.critical(self.page_dialog,"Failed to Connect","there was a "
                                                                                         "")
    @pyqtSlot()
    def scan_again(self,complete_hex_list,total):
        if self.ser.is_open:
            try:
                while self.counter is not total:
                    self.pcba_sensor(complete_hex_list)
            except:
                message = QMessageBox.critical(self.page_dialog,"Could not Scan","There was an error with the scan")

    @pyqtSlot()
    def check_if_sensor_true(self):
        if self.ser.is_open:
            try:
                self.flush_buffers()
                self.ser.write("temps 2\r\n".encode())
                data = self.ser.read_until(self.end).decode()
                data_split = data.split("\n")
                hex_line = data_split[2]
                sensor_num = hex_line[2:3]

                if sensor_num is not "0" and len(data_split) > 3:
                    return True
                else:
                    return False
            except:
                wrong = QMessageBox.critical(self.page_dialog,"sensor issue","there was an error in handling the sensor please try again or use a different sensor")

    @pyqtSlot()
    def pcba_sensor(self, hex_list):

        result = {}
        if self.ser.is_open:
            hex_number = ""
            try:
                while self.new_hexNum is False:
                    self.flush_buffers()
                    self.ser.write("temps 2\r\n".encode())
                    #num_bytes = self.ser.in_waiting
                    data = self.ser.read_until(self.end).decode()
                    data_split = data.split("\n")
                    hex_line = data_split[2]
                    sensor_num = hex_line[2:3]

                    if sensor_num is not "0" and len(data_split) > 3:
                        pcba_hex = data_split[3]
                        hex_number = pcba_hex[5:23]
                        hex_number = hex_number + " 28"  # family code
                        new_info = hex_number.replace(" ", "")
                        temp = int(new_info, 16)
                        hex_num = hex(temp)
                        if str(hex_num) in hex_list:  # this is activated if the hex is the same as previously scanne
                            pass
                        else:
                            self.counter += 1
                            self.data_ready.emit(self.counter,hex_num)
                            return hex_num

            except serial.serialutil.SerialException:
                self.no_port_sel.emit()

        else:
            error = QMessageBox.critical(self.page_dialog, "Port not found",
                                         "Please check Serial port connection in the 'Serial' tab. Port was not opened or connected",
                                         QMessageBox.Ok)
            self.page_dialog.show()
            if error == QMessageBox.Ok:
                self.page_dialog.close()
            return -1

    @pyqtSlot(int)
    def sleep(self, interval):
        """Wait for a specified time period."""
        time.sleep(interval)
        self.sleep_finished.emit()

    def is_connected(self, port):
        """Checks for serial connection."""
        try:
            self.ser.write(b"\r\n")
            time.sleep(0.1)
            self.ser.read(self.ser.in_waiting)
        except serial.serialutil.SerialException:
            return False
        return self.ser.port == port and self.ser.is_open

    def open_port(self, port):
        """Opens serial port."""
        try:
            self.ser.close()
            self.ser.port = port
            self.ser.open()
        except serial.serialutil.SerialException:
            self.port_unavailable_signal.emit()

    def flush_buffers(self):
        """Flushes the serial buffer by writing to the buffer and then reading
        all the available bytes."""
        self.ser.write("\r\n".encode())
        time.sleep(0.5)
        self.ser.read(self.ser.in_waiting)

    def close_port(self):
        """Closes serial port."""
        self.ser.close()
