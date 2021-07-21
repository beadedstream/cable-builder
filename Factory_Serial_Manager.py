import re
import os
import time
import serial
from datetime import date
# import Result_Page_Dialog
import serial.tools.list_ports
from PyQt5 import QtGui
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog,QProgressBar


class SerialManager(QObject):
    """Class that handles the serial connection."""
    data_ready = pyqtSignal(int, str)
    switch_sig = pyqtSignal(bool)
    clean_scan_page = pyqtSignal()
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
        print(serial.__file__)
        self.fluke = serial.Serial(None, 9600, timeout=60, parity=serial.PARITY_NONE, rtscts=False,
                                   xonxoff=False, dsrdtr=False, write_timeout=None)
        self.ser = serial.Serial(None, 115200, timeout=60,
                                 parity=serial.PARITY_NONE, rtscts=False,
                                 xonxoff=False, dsrdtr=False, write_timeout=None)

        self.memory = ''
        self.counter = 0  # this counter is not the same as the views file but it does share the same value by -1
        self.new_Bool = False
        self.scan_flag = True
        self.scan_reactivation_flag = False
        self.program_eeprom_flag = False
        self.page_dialog = QDialog()
        self.check = False
        self.total_number_reached = False
        self.unchanged_ids = list()
        self.hex_list = list()
        self.pwr_ids = list()
        self.hex_id_dict = dict()
        self.pwr_temps = list()
        self.hex_memory = list()
        self.eeprom = str()
        self.total_pcba_num = 0
        self.end = b"\r\n>"

    def resource_path(self, relative_path):
        """Gets the path of the application relative root path to allow us
        to find the logo."""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    #Utility Methods
    def get_date(self, with_dash=False):
        dt = date.today()
        if with_dash:
            return dt.strftime("%m-%d-%y")
        else:
            return dt.strftime("%m%d%y")

    @pyqtSlot()
    def scan_board(self):
        if self.ser.is_open:
            try:
                if self.scan_reactivation_flag:
                    result = QMessageBox.information(self.page_dialog,"Wish to Continue","Wish to clean Sensors?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
                    if result == QMessageBox.Yes:
                        self.reset_scan_page()
                        self.scan_reactivation_flag = False
                    else:
                        self.scan_reactivation_flag = False
                if self.scan_flag == False:
                    self.toggle_scan_flag()
                self.flush_buffers()
                self.call_func.emit()

            except:
                notworking = QMessageBox.critical(self.page_dialog, "Scan Malfunction",
                                                  "The was an error scanning for the pcba")
        else:
            QMessageBox.warning(self.page_dialog, "serial port not Connected"," Please connect the serial port in the tab above")
    @pyqtSlot()
    def pcba_sensor(self):
        if self.ser.is_open:
            try:
                while self.scan_flag:
                    self.ser.write("temps 2\r\n".encode())
                    data = self.ser.read_until(self.end).decode()
                    data_split = data.split("\n")
                    hex_line = data_split[2]
                    sensor_num = hex_line[2:3]

                    if sensor_num == '1' and len(data_split) > 5:
                        pcba_hex = data_split[3]
                        hex_number = pcba_hex[5:23]
                        hex_number = hex_number + " 28"  # family code

                        if str(hex_number) in self.hex_list:  # if the hex is the same as previously scanned pass
                            pass
                        else:
                            self.counter += 1
                            self.hex_list.append(hex_number)
                            self.data_ready.emit(self.counter, hex_number)
                            if self.counter is self.total_pcba_num:
                                self.scan_flag = False
                                return
                    elif "ERROR" in data:
                        time.sleep(1)
                        self.flush_buffers()

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

    def reset_scan_page(self):
        try:
            self.hex_list.clear()
            self.counter = 0
            self.clean_scan_page.emit()
        except:
            QMessageBox.critical(self.page_dialog,"Failed","Failed to clean page")

    def stop_scan(self):
        result = QMessageBox.information(self.page_dialog,"Scan Stopped","Wish to Cancel?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if result == QMessageBox.Yes:
            self.scan_reactivation_flag = True
            self.switch_sig.emit(True)
            self.scan_flag = False

    def toggle_scan_flag(self):
        if self.scan_flag:
            self.scan_flag = False
        else:
            self.scan_flag = True

    def flush_buffers(self):
        """Flushes the serial buffer by writing to the buffer and then reading
        all the available bytes."""
        self.ser.write("\r\n".encode())
        time.sleep(0.5)
        self.ser.read(self.ser.in_waiting)

    # Port Functions
    def wake_up_call(self):
        '''this call keeps the board on and turns off the sleep mode, if desired to sleep either turrn this mode off
         or directly call it to sleep'''
        if self.ser.is_open:
            try:
                self.ser.write("app 0\r\n".encode())
                # read = self.ser.read_until(self.end).decode()
                print("app 0 sent")

            except:
                message = QMessageBox.critical(self.page_dialog, "Wake up not possible",
                                               "The board was not able to remain awake")

    def scan_ports():
        """Scan and return list of connected comm ports."""
        return serial.tools.list_ports.comports()

    def is_connected(self, port):
        """Checks for serial connection."""
        try:
            self.ser.write(b"\r\n")
            time.sleep(0.1)
            self.ser.read(self.ser.in_waiting)
        except serial.serialutil.SerialException:
            return False
        return self.ser.port == port and self.ser.is_open

    def check_port(self):
        if self.ser.is_open:
            return True
        else:
            error = QMessageBox.critical(self.page_dialog, "Port closed",
                                         "Please check Serial port connection in the 'Serial' tab. Port was not opened or connected",
                                         QMessageBox.Ok)
            return False

    def open_port(self, port):
        """Opens serial port."""
        try:
            self.ser.close()
            self.ser.port = port
            self.ser.open()
        except serial.serialutil.SerialException:
            self.port_unavailable_signal.emit()

    def close_port(self):
        """Closes serial port."""
        self.ser.close()

    #closing Fucntion
    def reset_variables(self):
        self.memory = ''
        self.counter = 0
        self.new_Bool = False
        self.program_eeprom_flag = False
        # self.page_dialog = QDialog()
        self.check = False
        self.total_number_reached = False
        self.unchanged_ids.clear()
        self.hex_list.clear()
        self.pwr_ids.clear()
        self.pwr_temps.clear()
        self.hex_memory.clear()
        self.eeprom = str()
        self.total_pcba_num = 0
        self.scan_flag = True
        self.scan_reactivation_flag = False