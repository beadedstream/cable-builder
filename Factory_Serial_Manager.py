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

    def flush_buffers(self):
        """Flushes the serial buffer by writing to the buffer and then reading
        all the available bytes."""
        self.ser.write("\r\n".encode())
        time.sleep(0.5)
        self.ser.read(self.ser.in_waiting)

    def update_prog_bar(self, counter, prog_bar):
        counter += 10
        prog_bar.setValue(counter)
        return counter

    #scan page methods
    @pyqtSlot()
    def scan_board(self):
        if self.ser.is_open:
            try:
                if self.scan_reactivation_flag:
                    result = QMessageBox.information(self.page_dialog,"Wish to Continue","Continue?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
                    if result == QMessageBox.No:
                        self.reset_scan_page()
                        self.scan_reactivation_flag = False
                        return False
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
            QMessageBox.critical(self.page_dialog, "Port not found",
                                         "Please check Serial port connection in the 'Serial' tab. Port was not opened or connected",
                                         QMessageBox.Ok)
            # self.page_dialog.show()
            # if error == QMessageBox.Ok:
            #     self.page_dialog.close()
            return

    def reset_scan_page(self):
        try:
            self.hex_list.clear()
            self.counter = 0
            self.clean_scan_page.emit()
        except:
            QMessageBox.critical(self.page_dialog,"Failed","Failed to clean page")

    def stop_scan(self):
        self.scan_reactivation_flag = True
        self.switch_sig.emit(True)
        self.scan_flag = False

    def toggle_scan_flag(self):
        if self.scan_flag:
            self.scan_flag = False
        else:
            self.scan_flag = True

    @pyqtSlot()
    def board_replace_scan(self):
        self.wake_up_call()
        self.flush_buffers()
        if self.ser.is_open:
            self.new_Bool = False
            hex_number = ""
            try:
                while self.new_Bool == False:
                    self.flush_buffers()
                    self.ser.write("temps 2\r\n".encode())
                    data = self.ser.read_until(self.end).decode()
                    data_split = data.split("\n")
                    hex_line = data_split[2]
                    sensor_num = hex_line[2:3]

                    if sensor_num == "1" and len(data_split) > 3:
                        pcba_hex = data_split[3]
                        hex_number = pcba_hex[5:23]
                        hex_number = hex_number + " 28"  # family code
                        if str(
                                hex_number) in self.hex_list:  # this is activated if the hex is the same as previously scanne
                            QMessageBox.information(self.page_dialog, "board already detected",
                                                    "Please scan a different board \n"
                                                    " board has been previously scanned")
                        else:
                            self.hex_list.append(hex_number)
                            return hex_number
            except:
                board_err = QMessageBox.critical(self.page_dialog, "board not Replaced",
                                                 "There was an error trying to load the board")

    #Build page methods
    @pyqtSlot()
    def Test_Cable(self, total_sensor_amount, pcba_id_dict, progBar, progress_bar_counter, has_protection_board,
                   build_test=True):

        self.powered_temp_dict = dict()
        self.err_pwr_dict = dict()
        err_dict = dict()
        self.wake_up_call()
        self.flush_buffers()

        progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

        if has_protection_board is True:
            total_sensor_amount += 1

        if self.ser.is_open:
            try:
                if build_test is True:
                    self.ser.write("tac-ee-load-ids 1 \r\n".encode())
                    self.ser.write(" \r\n".encode())

                    self.ser.write("tac-ee-load-spacings 1 \r\n".encode())
                    self.ser.write(" \r\n".encode())
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)
                else:
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                self.flush_buffers()

                # powered test
                self.ser.write("strong-pu 0\r\n".encode())
                self.ser.read_until(self.end).decode()

                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                self.ser.write("sonic-pwr 1\r\n".encode())
                self.ser.read_until(self.end).decode()
                id_dict = pcba_id_dict.copy()
                self.hex_id_dict = pcba_id_dict.copy()

                self.pwr_ids, self.pwr_temps = self.hex_or_temps_parser(2, "1")
                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                # sensor checks
                matching_Sensors = self.verify_pcba(id_dict, total_sensor_amount)
                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                if isinstance(matching_Sensors, list):
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                    return ('Wrong id', matching_Sensors, False, progress_bar_counter)  # EXIT 1

                if isinstance(matching_Sensors, tuple):
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                    return matching_Sensors  # EXIT 2 tuple add counter

                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                if len(self.pwr_ids) != total_sensor_amount or len(self.pwr_temps) != total_sensor_amount:
                    self.test_result_tuple = ("Power Test fail:", "Powered Test Failed \n Failed to read All Sensors!\n"
                                              + str(len(self.pwr_ids)) + " out of " + str(total_sensor_amount) + "\n"
                                              + "Temperatures: " + str(len(self.pwr_temps)) + " out of " + str(
                        total_sensor_amount), False)
                else:
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                    sensor_information_dict = self.check_temperatures(self.pwr_temps, self.pwr_ids)
                    if False in sensor_information_dict:
                        sensor_information_dict.pop(False)
                        err_dict = sensor_information_dict
                    else:
                        sensor_information_dict.pop(True)
                        self.powered_temp_dict = sensor_information_dict
                    progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                    if len(err_dict) == total_sensor_amount:
                        return (
                            "Test Fail", "Cable Power Failure: All the sensors return 85", False, progress_bar_counter)

                    elif len(err_dict) > 0 and len(err_dict) < total_sensor_amount:
                        temp_err_dict = dict()
                        for hex in err_dict:
                            if err_dict.get(hex) == 85:
                                temp_err_dict[pcba_id_dict.get(hex)] = 85  # format [phy_num] = temp code
                            elif err_dict.get(hex) == 99:
                                temp_err_dict[pcba_id_dict.get(hex)] = 99
                        if len(temp_err_dict) > 0:
                            return ("Power Failure", temp_err_dict, False, progress_bar_counter)

                    else:
                        self.test_result_tuple = ("Powered Test Pass", self.powered_temp_dict, True)

                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)
                if build_test is False:
                    return self.test_result_tuple + (progress_bar_counter,)


                # TODO: below is only for the build test
                parasidic_test_results = self.parasidic_Test(total_sensor_amount, pcba_id_dict)
                progress_bar_counter = self.update_prog_bar(progress_bar_counter, progBar)

                test_result_dict = dict()
                if self.test_result_tuple[2] is False and isinstance(self.test_result_tuple[1], list) and \
                        parasidic_test_results[2] is False and isinstance(parasidic_test_results[1], list):
                    hex = 0
                    for temp in parasidic_test_results[1]:
                        test_result_dict[self.test_result_tuple[1][hex]] = temp
                    return ("Failed Test", test_result_dict, False, progress_bar_counter)
                self.test_result_tuple += parasidic_test_results

                result = self.test_result_tuple + (progress_bar_counter,)
                return result  # EXIT 3

            except Exception:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the powered test\n Please Try again")

            except ValueError:
                value_err = QMessageBox.critical(self.page_dialog, "Parsing Error",
                                                 "There was an Error parsing the information\n please try to re-connect or rescan the sensor")
        else:
            error = QMessageBox.critical(self.page_dialog, "Port not found",
                                         "Please check Serial port connection in the 'Serial' tab. Port was not opened or connected",
                                         QMessageBox.Ok)
            self.page_dialog.show()
            if error == QMessageBox.Ok:
                self.page_dialog.close()
            return -1

    def hex_or_temps_parser(self, key, port, optional=False):
        '''This function grabs either the hex or temps from the cable and returns it as a list'''
        if self.ser.is_open:
            try:
                self.ser.write(("temps " + port + " \r\n").encode())
                temps = self.ser.read_until(self.end).decode().split("\r\n")
                temp_list = list()
                hex_list = list()

                if key == 0 and isinstance(temps, list) and temps[2][2] != '0':
                    for hex in range(3, len(temps)):
                        hex_list.append(temps[hex][4:24].replace(" ", "") + "28")
                    hex_list.pop()
                    hex_list.pop()

                    return hex_list

                elif key == 1 and isinstance(temps, list) and temps[2][2] != '0':
                    for t in range(3, len(temps)):
                        temp_list.append(temps[t][34:41])

                    temp_list.pop()
                    temp_list.pop()

                    t_list = temp_list.copy()
                    temp_list.clear()

                    for t in t_list:
                        temp_list.append(float(t))
                    return temp_list

                elif key == 2 and isinstance(temps, list) and temps[2][2] != '0':
                    counter = 0
                    protection_board_temperature = list()
                    protection_board_hex = list()
                    for t in range(3, len(temps)):
                        hex_list.append(temps[t][4:24].replace(" ", "") + "28")
                        if hex_list[counter] in self.hex_id_dict:
                            temp_list.append(temps[t][34:41])
                        else:
                            protection_board_temperature.append(temps[t][34:41])
                            protection_board_hex.append(temps[t][4:24].replace(" ", "") + "28")
                        counter += 1

                    hex_list.remove(protection_board_hex[0])
                    protection_board_temperature.pop()
                    protection_board_temperature.pop()
                    protection_board_hex.pop()
                    protection_board_hex.pop()

                    hex_list.pop()
                    hex_list.pop()
                    if len(protection_board_hex) > 0 or len(protection_board_temperature) > 0:
                        temp_list.insert(0, protection_board_temperature[0])
                        hex_list.insert(0, protection_board_hex[0])

                    t_list = temp_list.copy()
                    temp_list.clear()

                    for t in t_list:
                        temp_list.append(float(t))

                    pcba = (hex_list, temp_list)
                    return pcba

                elif key == 3:
                    if optional:
                        for hex in range(3, len(temps)):
                            hex_list.append(temps[hex][6:24].strip())
                        hex_list.pop()
                        hex_list.pop()
                        return hex_list
                    else:
                        for hex in range(3, len(temps)):
                            self.unchanged_ids.append(temps[hex][6:24].strip())
                        self.unchanged_ids.pop()
                        self.unchanged_ids.pop()
                else:
                    return False,False
            except:
                return False

    def get_hex_ids(self):
        return self.pwr_ids

    def get_temps(self):
        return self.pwr_temps

    def verify_pcba(self, pcba_dict, len_of_dict):  # format (int,{hex,physical number},int )
        '''This function does a temps call and compares the reading pcbas with the list that is passed returns boolean
        or a list containing the missing id, pcba_dict format is [hex number of board] = [physical placement in cable]'''
        self.flush_buffers()
        if self.ser.is_open:
            try:
                error_pcba = list()

                parser = self.pwr_ids.copy()
                pcba_dictionary_copy = pcba_dict.copy()
                if parser is None or len(parser) != len_of_dict or parser == False:
                    parser = self.hex_or_temps_parser(0, "1")

                    if len(parser) != len_of_dict:
                        for id in pcba_dictionary_copy:
                            if id not in parser:
                                return ("Missing Sensor",
                                        "Position: " + str(pcba_dictionary_copy.get(id) + 1) + " Missing Sensor ",
                                        False)
                        return ("Fail", "Missing Protection Board", False)
                        # return ("Missing Protection Board","Missing Protection Board!",False)
                    else:
                        return ("Failed Test", "Failed to read sensors, Please try again", False)
                # this checks for same hex #, if wrong or bad return the physical number
                pcba_replica = pcba_dict.copy()
                for pcba in parser:
                    if pcba in pcba_replica:
                        pcba_replica.pop(pcba)

                if len(pcba_replica) != 0:
                    for key in pcba_replica:
                        error_pcba.append(pcba_replica.get(key))
                    return error_pcba
                else:
                    return True
            except:
                return ("Cable Verify Failed\n", "There was an error with the test\n Please Try again", False)

    def check_temperatures(self, temp_list, id_list):
        counter = 0
        err_dict = dict()
        pass_dict = dict()
        for t in temp_list:
            if t > 70 and t < 90:
                err_dict[id_list[counter]] = 85
            elif t > 98 and t < 100:
                err_dict[id_list[counter]] = 99
            elif t > 110:
                err_dict[id_list[counter]] = 127
            else:
                pass_dict[id_list[counter]] = t
            counter += 1

        if len(err_dict) > 0:
            err_dict[False] = False
            return err_dict
        else:
            pass_dict[True] = True
            return pass_dict

    def parasidic_Test(self, total_sensor_amount, pcba_id_dict):
        # global result_tuple
        self.flush_buffers()
        self.para_dict = dict()
        self.para_err_dict = dict()
        if self.ser.is_open:
            try:
                self.para_dict = self.check_temperatures(self.pwr_temps, self.pwr_ids)

                if len(self.pwr_temps) != total_sensor_amount:
                    self.ser.write("sonic-pwr 1\r\n".encode())
                    self.ser.write("strong-pu 0 \r\n".encode())
                    return ("Missing temps", "failed to read temperatures", False)

                # setting it back to normal and checking they all work
                self.ser.write("sonic-pwr 0\r\n".encode())
                self.ser.write("strong-pu 0\r\n".encode())
                self.flush_buffers()

                dead_temps = self.hex_or_temps_parser(1, "1")
                dead_temps_list = list()
                for t in dead_temps:
                    if t == 99:
                        dead_temps_list.append(t)

                self.ser.write("sonic-pwr 1\r\n".encode())
                self.ser.write("strong-pu 0\r\n".encode())
                self.flush_buffers()

                if len(dead_temps_list) > 0:
                    return ("Temperature Failure", "There is a dead Sensor", False)

                temp_err = list()
                temps = self.hex_or_temps_parser(1, "1")
                for t in temps:
                    if t > 40:
                        temp_err.append(t)

                if len(temp_err) == total_sensor_amount:
                    result_tuple = ("Temperature Failure", "Cable Power Failure: All the sensors return 85", False)
                elif len(temp_err) != 0:
                    self.para_err_dict + temp_err

                elif len(self.para_err_dict) > 0:
                    bad_sensor = dict()
                    no_power = dict()
                    for id in self.para_err_dict:
                        if id in pcba_id_dict and self.para_err_dict.get(id) > 100:
                            bad_sensor[pcba_id_dict.get(id)] = self.para_err_dict.get(id)  # format [physical #] = temp
                        if id in pcba_id_dict and self.para_err_dict.get(id) == 85:
                            no_power[pcba_id_dict.get(id)] = self.para_err_dict.get(id)
                    final_temp_reading = bad_sensor + no_power
                    result_tuple = ("Bad Sensor", final_temp_reading, False)
                else:
                    result_tuple = ("Successful Parasidic Results", self.para_dict, True)

                return result_tuple

            except:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the parasidc test")




    #Program Methods

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