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

    @pyqtSlot()
    def scan_board(self):

        if self.ser.is_open:
            try:
                self.flush_buffers()
                self.call_func.emit()

            except:
                notworking = QMessageBox.critical(self.page_dialog, "Scan Malfunction",
                                                  "The was an error scanning for the pcba")
        else:
            connect = QMessageBox.warning(self.page_dialog, "serial port not Connected",

                                          " Please connect the serial port in the tab above")

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
