import re
import time
import serial
import Result_Page_Dialog
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QDialog


class SerialManager(QObject):
    """Class that handles the serial connection."""
    data_ready = pyqtSignal(int, str)
    no_port_sel = pyqtSignal()
    sleep_finished = pyqtSignal()
    port_unavailable_signal = pyqtSignal()
    no_version = pyqtSignal()
    scan_signal = pyqtSignal(bool)
    call_func = pyqtSignal()
    finished = pyqtSignal()
    enable_btn = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(None, 115200, timeout=60,
                                 parity=serial.PARITY_NONE, rtscts=False,
                                 xonxoff=False, dsrdtr=False, write_timeout=None)
        self.memory = ''
        self.counter = 0  # this counter is not the same as the views file but it does share the same value by -1
        self.new_hexNum = False
        self.page_dialog = QDialog()
        self.check = False
        self.total_number_reached = False
        self.hex_list = []
        self.hex_memory = []
        self.total_pcba_num = 0
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
                print("app 0 sent")

            except:
                message = QMessageBox.critical(self.page_dialog, "Wake up not possible",
                                               "The board was not able to remain awake")

    @pyqtSlot()
    def parasidic_test(self):
        self.temps_list = []
        self.error_sensors = {}
        if self.ser.is_open:
            try:
                self.flush_buffers()
                self.ser.write("strong-pu 1\r\n".encode())
                strong = self.ser.read_until(self.end).decode()
                print("this is strong-pu 1: ", strong)

                self.ser.write("5v 0\r\n".encode())
                time.sleep(2)
                five = self.ser.read_until(self.end).decode()
                print("the 5v 0: ", five)

                self.ser.write("sonic-pwr 0\r\n".encode())
                sonic = self.ser.read_until(self.end).decode()
                print("the sonic-pwr 0 is: ", sonic)

                self.ser.write("temps 1\r\n".encode())
                temps = self.ser.read_until(self.end).decode()
                # this checks for the sensors if there are any connected
                connection_check = temps.split("\r\n")
                if connection_check[2][2] == '0':
                    error = QMessageBox.critical(self.page_dialog, "No Temperatures",
                                                 "Parasidic Test Failed \n No temperatures were detected in the cable!")
                    # you need to error handle if the number of sensors detected is less than the total amount actually there,
                    # justt either pass the total number and compare it or do a read of temps with a counter or sizeof operator
                    return False

                t = temps.split("=")
                for i in range(1, len(t)):
                    self.temps_list.append(float(t[i][2:11]))
                counter = 1
                for check in self.temps_list:
                    if check > 40:  # this checks for garbage temps that indicate a high temperature
                        self.error_sensors[counter] = check
                    counter += 1
                print("these are the temps for the parasidic test: ", self.temps_list)

                result_tuple= (self.temps_list,True)
                return result_tuple

            except:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the parasidc test")

    @pyqtSlot()
    def powered_test(self):
        self.powered_temp_list = []
        self.powered_dict = {}
        if self.ser.is_open:
            try:
                self.flush_buffers()
                self.ser.write("strong-pu 0\r\n".encode())
                strong = self.ser.read_until(self.end).decode()
                print("this is strong-pu 0: ", strong)

                self.ser.write("5v 1\r\n".encode())
                five = self.ser.read_until(self.end).decode()
                print("the 5v 1: ", five)

                self.ser.write("sonic-pwr 1\r\n".encode())
                sonic = self.ser.read_until(self.end).decode()
                print("the sonic-pwr 1 is: ", sonic)

                self.ser.write("temps 1\r\n".encode())
                temps = self.ser.read_until(self.end).decode()
                print("temps: ", temps)

                connection_check = temps.split("\r\n")
                if connection_check[2][2] == '0':
                    error = QMessageBox.critical(self.page_dialog, "No Temperatures",
                                                 "Powered Test Failed \n No temperatures were detected in the cable!")
                    return False

                t = temps.split("=")
                for i in range(1, len(t)):
                    self.powered_temp_list.append(float(t[i][2:11]))
                counter = 1
                for check in self.powered_temp_list:
                    if check > 40:  # this checks for garbage temps that indicate a high temperature
                        self.powered_dict[counter] = check
                    counter += 1

                result_tuple = (self.powered_temp_list, True)
                return result_tuple
            except:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the powered test")

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
                wrong = QMessageBox.critical(self.page_dialog, "sensor issue",
                                             "there was an error in handling the sensor please try again or use a different sensor")

    @pyqtSlot()
    def scan_board(self):

        if self.ser.is_open:
            try:
                self.call_func.emit()

            except:
                notworking = QMessageBox.critical(self.page_dialog, "Scan Malfunction",
                                                  "The was an error scanning for the pcba")
                print("failed the scan board")
        else:
            connect = QMessageBox.warning(self.page_dialog, "serial port not Connected",
                                          " Please connect the serial port in the tab above")

    @pyqtSlot()
    def pcba_sensor(self):
        if self.ser.is_open:
            hex_number = ""
            try:
                while self.new_hexNum is False:
                    self.flush_buffers()
                    self.ser.write("temps 2\r\n".encode())
                    # num_bytes = self.ser.in_waiting
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
                        if str(
                                hex_num) in self.hex_list:  # this is activated if the hex is the same as previously scanne
                            pass
                        else:
                            self.counter += 1
                            self.hex_list.append(hex_num)
                            self.data_ready.emit(self.counter, hex_num)
                            if self.counter is self.total_pcba_num:
                                self.new_hexNum = True



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

    @pyqtSlot()
    def board_replace_scan(self):
        if self.ser.is_open:
            self.new_hexNum = False
            hex_number = ""
            try:
                while self.new_hexNum is False:
                    self.flush_buffers()
                    self.ser.write("temps 2\r\n".encode())
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
                        if str(
                                hex_num) in self.hex_list:  # this is activated if the hex is the same as previously scanne
                            pass
                        else:
                            self.hex_list.append(hex_num)
                            return temp
            except:
                print("ahoy maty!")

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
