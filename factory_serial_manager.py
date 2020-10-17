import re
import os
import time
import serial
import Result_Page_Dialog
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog


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
        self.fluke = serial.Serial(None, 9600, timeout=60, parity=serial.PARITY_NONE, rtscts=False,
                                   xonxoff=False, dsrdtr=False, write_timeout=None)
        self.ser = serial.Serial(None, 115200, timeout=60,
                                 parity=serial.PARITY_NONE, rtscts=False,
                                 xonxoff=False, dsrdtr=False, write_timeout=None)

        self.memory = ''
        self.counter = 0  # this counter is not the same as the views file but it does share the same value by -1
        self.new_Bool = False
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
                # read = self.ser.read_until(self.end).decode()
                print("app 0 sent")

            except:
                message = QMessageBox.critical(self.page_dialog, "Wake up not possible",
                                               "The board was not able to remain awake")

    @pyqtSlot()
    def Test_Cable(self, temp_num, pcba_id_dict):

        self.powered_temp_dict = dict()
        self.err_pwr_dict = dict()
        self.wake_up_call()
        self.flush_buffers()


        if self.ser.is_open:
            try:
                # powered test
                self.ser.write("strong-pu 0\r\n".encode())
                pwr_pu = self.ser.read_until(self.end).decode()

                self.ser.write("sonic-pwr 1\r\n".encode())
                pwr_sonic = self.ser.read_until(self.end).decode()

                id_dict = pcba_id_dict.copy()
                # sensor checks
                matching_Sensors = self.verify_pcba(id_dict)

                if isinstance(matching_Sensors, list):
                    return ('Wrong id', matching_Sensors, False)

                elif isinstance(matching_Sensors, bool):
                    if matching_Sensors is False:
                        return ("No sensors Scanned","NULL" , False)

                pwr_ids = self.temps_parser(0,"1")
                pwr_temps = self.temps_parser(1,"1")
                if isinstance(pwr_temps, list):
                    temp = pwr_temps.copy()
                    pwr_temps.clear()
                    for turn in temp:
                        pwr_temps.append(float(turn))

                if len(pwr_ids) != temp_num:
                    self.ser.write("sonic-pwr 1\r\n".encode())
                    self.final_fail_result = (
                    "Power Test fail:", "Powered Test Failed \n No temperatures were detected in the cable!\n"
                                        "only: " + str(len(pwr_ids)) + " / " + str(temp_num), False)
                else:
                    counter = 0
                    for t in pwr_temps:
                        if t > 40:
                            self.err_pwr_dict[pwr_ids[counter]] = t
                        else:
                            self.powered_temp_dict[pwr_ids[counter]] = t
                        counter += 1

                    if len(self.err_pwr_dict) >= 1:
                        self.test_result_tuple = ("Garbage values", self.err_pwr_dict, False)

                    self.test_result_tuple = ("Powered Test Pass", self.powered_temp_dict, True)

                    parasidic_test_results = self.parasidic_Test(temp_num,pcba_id_dict)

                    self.test_result_tuple += parasidic_test_results
                    return self.test_result_tuple

            except Exception:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the powered test\n Please Try again")
            except ValueError:
                value_err = QMessageBox.critical(self.page_dialog, "Parsing Error",
                                                 "There was an Error parsing the information\n please try to re-connect or rescan the sensor")

    @pyqtSlot()
    def parasidic_Test(self, temp_num,pcba_id_dict):
        self.flush_buffers()
        self.para_dict = dict()
        self.para_err_dict = dict()
        if self.ser.is_open:
            try:
                # Parasidic Test
                self.ser.write("strong-pu 0\r\n".encode())
                para_strong_pu = self.ser.read_until(self.end).decode()  # the read_until function stores the response in a stack so you have to assign it to something everytime you make a write call
                self.ser.write("sonic-pwr 0\r\n".encode())
                sonic_read = self.ser.read_until(self.end).decode()

                error_85 = self.temps_parser(1,"1")
                print("error 85 check", error_85)

                self.ser.write("strong-pu 1\r\n".encode())
                para_strong_pu = self.ser.read_until(self.end).decode()

                para_ids = self.temps_parser(0, "1")
                para_temps = self.temps_parser(1,"1")
                if isinstance(para_temps,list):
                    temp = para_temps.copy()
                    para_temps.clear()
                    for t in temp:
                        para_temps.append(float(t))



                counter = 0
                for t in para_temps:
                    if t > 70 and t < 90:
                        self.para_err_dict[para_ids[counter]] = 85
                    elif t > 98 and t < 100:
                        self.para_err_dict[para_ids[counter]] = 99
                    elif t > 110:
                        self.para_err_dict[para_ids[counter]] = 127

                    self.para_dict[para_ids[counter]] = t
                    counter += 1

                if len(para_temps) != temp_num:
                    retry = list()
                    timeout = 0
                    while len(retry) != temp_num or timeout != 5:
                        retry = self.temps_parser(1)
                        timeout += 1
                    if timeout == 5:
                        self.ser.write("sonic-pwr 1\r\n".encode())
                        return ("Missing temps","failed to read temperatures",False)


                if len(self.para_err_dict) > 0:
                    final_temp_reading = dict()
                    bad_sensor = dict()
                    no_power = dict()
                    for id in self.para_err_dict:
                        if id in pcba_id_dict and self.para_err_dict.get(id) > 100:
                            bad_sensor[pcba_id_dict.get(id)] = self.para_err_dict.get(id)#format [physical #] = temp
                        if id in pcba_id_dict and self.para_err_dict.get(id) == 85:
                            no_power[pcba_id_dict.get(id)] = self.para_err_dict.get(id)
                    final_temp_reading = bad_sensor + no_power
                    result_tuple = ("Bad Sensor", final_temp_reading, False)
                else:
                    result_tuple = ("Successful Parasidic Results", self.para_dict, True)

                self.ser.write("sonic-pwr 1\r\n".encode())
                self.ser.write("strong-pu 0 \n\r".encode())

                return result_tuple

            except:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the parasidc test")

    @pyqtSlot()
    def verify_pcba(self, pcba_dict):
        '''This function does a temps call and compares the reading pcbas with the list that is passed returns boolean
        or a list containing the missing id, pcba_dict format is [hex number of board] = [physical placement in cable]'''
        self.flush_buffers()
        if self.ser.is_open:
            try:
                error_pcba = list()
                self.flush_buffers()
                parser = self.temps_parser(0,"1")

                if parser is None or len(parser) != len(pcba_dict) or parser == False:
                    counter = 0
                    tryout = 0  # this var is to keep it from running endlessly
                    while counter != 1:
                        parser = self.temps_parser(0, "1")
                        if parser != None and parser != False and len(parser) == len(pcba_dict) :
                            counter += 1
                        if tryout == 3:
                            return False
                        tryout += 1
                #this checks for same hex #, if wrong or bad return the physical number
                for pcba in parser:
                    if pcba in pcba_dict:
                        pcba_dict.pop(pcba)

                if len(pcba_dict) != 0:
                    for key in pcba_dict:
                        error_pcba.append(pcba_dict.get(key))
                    return error_pcba
                else:
                    return True


            except:
                return False

    @pyqtSlot()
    def temps_parser(self, key, port):
        '''This function grabs either the hex or temps from the cable and returns it as a list'''
        if self.ser.is_open:
            try:
                # if timeout == 3:  # base case for recursive check
                #     return False

                self.ser.write(("temps "+port+" \r\n").encode())
                temps = self.ser.read_until(self.end).decode().split("\r\n")

                if key == 0 and isinstance(temps, list) and temps[2][2] != '0':
                    hex_list = list()
                    for hex in range(3, len(temps)):
                        hex_list.append(temps[hex][4:24].replace(" ", "") + "28")
                    hex_list.pop()
                    hex_list.pop()
                    return hex_list
                elif key == 1 and isinstance(temps, list) and temps[2][2] != '0':
                    temp_list = list()
                    for t in range(3, len(temps)):
                        temp_list.append(temps[t][34:41])
                    temp_list.pop()
                    temp_list.pop()
                    return temp_list
                elif key == 2 and isinstance(temps,list)and temps[2][2] != '0' :
                    hex_list = list()
                    for hex in range(3, len(temps)):
                        hex_list.append(temps[hex][4:24] + "28")
                    hex_list.pop()
                    hex_list.pop()

                    temp_list = list()
                    for t in range(3, len(temps)):
                        temp_list.append(temps[t][34:41])
                    temp_list.pop()
                    temp_list.pop()

                    pcba = (hex_list,temp_list)
                    return pcba




                else:
                    pass
                    # timeout += 1
                    # self.temps_parser(key,port)
            except:
                return False

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
        self.flush_buffers()
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
                while self.new_Bool is False:
                    self.ser.write("temps 2\r\n".encode())
                    data = self.ser.read_until(self.end).decode()
                    data_split = data.split("\n")
                    hex_line = data_split[2]
                    sensor_num = hex_line[2:3]

                    if sensor_num != '0' and len(data_split) > 3:
                        pcba_hex = data_split[3]
                        hex_number = pcba_hex[5:23]
                        hex_number = hex_number + " 28"  # family code
                        print("hex_number: ", hex_number)

                        if str(
                                hex_number) in self.hex_list:  # this is activated if the hex is the same as previously scanned
                            pass
                        else:
                            self.counter += 1
                            self.hex_list.append(hex_number)
                            self.data_ready.emit(self.counter, hex_number)
                            if self.counter is self.total_pcba_num:
                                self.new_Bool = True



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
    # @pyqtSlot()
    # def send_hex_to_display(self,hex):
    #     if str(hex) not in self.hex_list:
    #         self.counter += 1
    #         self.hex_list.append(hex)
    #         self.hex_memory.append(hex)
    #         self.data_ready.emit(self.counter, hex)
    #         if self.counter is self.total_pcba_num:
    #             self.new_Bool = True
    @pyqtSlot()
    def messageBox(self,type,title,description,button):
        call = QDialog()
        message = QMessageBox.critical(call,title,description,button)
        if message == QMessageBox.Ok:
            return message
    @pyqtSlot()
    def board_replace_scan(self):
        self.wake_up_call()
        self.flush_buffers()
        if self.ser.is_open:
            self.new_Bool = False
            hex_number = ""
            try:
                while self.new_Bool is False:
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
                        # new_info = hex_number.replace(" ", "")
                        # temp = int(new_info, 16)
                        # hex_num = hex(temp)
                        if str(
                                hex_number) in self.hex_list:  # this is activated if the hex is the same as previously scanne
                            sensor = QMessageBox.information(self.page_dialog, "board already detected",
                                                             "Please scan a different board \n"
                                                             " board has been previously scanned")
                        else:
                            self.hex_list.append(hex_number)
                            return hex_number
            except:
                board_err = QMessageBox.critical(self.page_dialog, "board not Replaced",
                                                 "There was an error trying to load the board")

    @pyqtSlot()
    def eeprom_program(self):
        if self.ser.is_open:
            try:
                self.flush_buffers()
                self.ser.write("config 1\r\n".encode())
                config = self.ser.read_until(self.end).decode()
                config_list = config.split("\n")

                print(config)


            except:
                print("it didnt work")

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
