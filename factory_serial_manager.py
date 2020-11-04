import re
import os
import time
import serial
import Result_Page_Dialog
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
    def Test_Cable(self, total_sensor_amount, pcba_id_dict,progBar,startTime,has_protection_board):

        self.powered_temp_dict = dict()
        self.err_pwr_dict = dict()
        err_dict = dict()
        self.wake_up_call()
        self.flush_buffers()
        mid_time = time.time()
        progBar.setValue(mid_time - startTime)

        if has_protection_board is True:
            total_sensor_amount += 1


        if self.ser.is_open:
            try:
                # powered test
                self.ser.write("strong-pu 0\r\n".encode())
                pwr_pu = self.ser.read_until(self.end).decode()

                mid_time = time.time()
                progBar.setValue(mid_time - startTime)

                self.ser.write("sonic-pwr 1\r\n".encode())
                pwr_sonic = self.ser.read_until(self.end).decode()
                id_dict = pcba_id_dict.copy()

                # sensor checks
                matching_Sensors = self.verify_pcba(0,id_dict,total_sensor_amount)

                if isinstance(matching_Sensors, list):
                    mid_time = time.time()
                    progBar.setValue(mid_time - startTime)
                    return ('Wrong id', matching_Sensors, False)#EXIT 1

                elif isinstance(matching_Sensors, tuple):
                    mid_time = time.time()
                    progBar.setValue(mid_time - startTime)
                    return matching_Sensors#EXIT 2 tuple

                pwr_ids = self.hex_or_temps_parser(0,"1")
                pwr_temps = self.hex_or_temps_parser(1,"1")

                mid_time = time.time()
                progBar.setValue(mid_time - startTime)

                if len(pwr_ids) != total_sensor_amount or len(pwr_temps) != total_sensor_amount:
                    self.ser.write("sonic-pwr 1\r\n".encode())
                    self.test_result_tuple = ("Power Test fail:", "Powered Test Failed \n Failed to read All Sensors!\n"
                                         + str(len(pwr_ids)) + " out of " + str(total_sensor_amount)+"\n"
                    +"Temperatures: "+ str(len(pwr_temps))+" out of "+ str(total_sensor_amount), False)
                else:
                    checky = self.check_temperatures(pwr_temps,pwr_ids)
                    if False in checky:
                        checky.pop(False)
                        err_dict = checky
                    else:
                        checky.pop(True)
                        self.powered_temp_dict = checky

                    if len(err_dict) == total_sensor_amount:
                        return ("Test Fail","Cable Power Failure: All the sensors return 85",False)

                    elif len(err_dict) > 0 and len(err_dict) < total_sensor_amount:
                        temp_err_dict = dict()
                        for hex in err_dict:
                            if err_dict.get(hex) == 85:
                                temp_err_dict[pcba_id_dict.get(hex)] = 85# format [phy_num] = temp code
                            elif err_dict.get(hex) == 99:
                                temp_err_dict[pcba_id_dict.get(hex)] = 99
                        if len(temp_err_dict) > 0:
                            return ( "Power Failure",temp_err_dict,False)


                        # self.test_result_tuple = ("Powered Test Fail: Garbage values", err_list, False)
                    else:
                        self.test_result_tuple = ("Powered Test Pass", self.powered_temp_dict, True)

                parasidic_test_results = self.parasidic_Test(total_sensor_amount,pcba_id_dict)

                test_result_dict = dict()
                if self.test_result_tuple[2] is False and isinstance(self.test_result_tuple[1],list) and parasidic_test_results[2] is False and isinstance(parasidic_test_results[1],list):
                    hex = 0
                    for temp in parasidic_test_results[1]:
                        test_result_dict[self.test_result_tuple[1][hex]] = temp
                    return ("Failed Test",test_result_dict,False)

                self.test_result_tuple += parasidic_test_results


                return self.test_result_tuple#EXIT 3

            except Exception:
                write_error = QMessageBox.critical(self.page_dialog, "Write Error",
                                                   "There was an error with the powered test\n Please Try again")
            except ValueError:
                value_err = QMessageBox.critical(self.page_dialog, "Parsing Error",
                                                 "There was an Error parsing the information\n please try to re-connect or rescan the sensor")

    @pyqtSlot()
    def parasidic_Test(self, total_sensor_amount,pcba_id_dict):
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
                error_85 = self.hex_or_temps_parser(1,"1")

                self.ser.write("strong-pu 1\r\n".encode())
                para_strong_pu = self.ser.read_until(self.end).decode()

                para_ids = self.hex_or_temps_parser(0, "1")
                para_temps = self.hex_or_temps_parser(1,"1")

                self.para_dict= self.check_temperatures(para_temps,para_ids)


                if len(para_temps) != total_sensor_amount:
                    retry = list()
                    timeout = 0
                    while len(retry) != total_sensor_amount or timeout != 5:
                        retry = self.hex_or_temps_parser(1,"1")
                        timeout += 1
                    if timeout == 5:
                        self.ser.write("sonic-pwr 1\r\n".encode())
                        self.ser.write("strong-pu 0 \r\n".encode())
                        return ("Missing temps","failed to read temperatures",False)

                #setting it back to normal and checking they all work
                self.ser.write("sonic-pwr 1\r\n".encode())
                garbage= self.ser.read_until(self.end).decode()
                self.ser.write("strong-pu 0\r\n".encode())
                grabage = self.ser.read_until(self.end).decode()

                temp_err = list()
                temps = self.hex_or_temps_parser(1,"1")
                for t in temps:
                    if t > 40:
                        temp_err.append(t)

                if len(temp_err) == total_sensor_amount:
                    result_tuple = ("Temperature Failure","Cable Power Failure: All the sensors return 85",False)
                elif len(temp_err) != 0:
                    self.para_err_dict + temp_err

                elif len(self.para_err_dict) > 0:
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
    def check_temperatures(self,temp_list,id_list):
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
            err_dict[False]=False
            return err_dict
        else:
            pass_dict[True] = True
            return pass_dict
    @pyqtSlot()
    def verify_pcba(self,key,pcba_dict,len_of_dict):# format (int,{hex,physical number},int )
        '''This function does a temps call and compares the reading pcbas with the list that is passed returns boolean
        or a list containing the missing id, pcba_dict format is [hex number of board] = [physical placement in cable]'''
        self.flush_buffers()
        if self.ser.is_open:
            try:
                if key == 0:
                    error_pcba = list()
                    parser = self.hex_or_temps_parser(0,"1")

                    if parser is None or len(parser) != len_of_dict or parser == False:
                        counter = 0
                        tryout = 0  # this var is to keep it from running endlessly
                        while counter != 1:
                            parser = self.hex_or_temps_parser(0, "1")
                            if parser != None and parser != False and len(parser) == len_of_dict :
                                counter += 1
                            if tryout == 3:
                                return ("Failed Reading Hex Id's","Failed to read all sensors\n"+str(len(parser))+" out of "+str(len_of_dict),False)
                            tryout += 1
                    #this checks for same hex #, if wrong or bad return the physical number
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

                if key == 1:
                    temperature_list = self.hex_or_temps_parser(1,"1")
                    hex_list = self.hex_or_temps_parser(0,"1")

                    verify_hex = self.verify_pcba(0, pcba_dict,len_of_dict)
                    concat_multiple_hex = str()

                    if isinstance(verify_hex, list):
                        for hex in verify_hex:
                            concat_multiple_hex = concat_multiple_hex + str(hex) + ", "
                        return ("Cable Verify Failed",
                                "Position: " + concat_multiple_hex + "\n Dont match Previously scanned", False)

                    elif verify_hex is False:
                        return ("Cable Verify Failed", "Failed to read all sensors\n Please try again", False)

                    #Do temperature
                    if temperature_list is None or len(temperature_list) != len_of_dict or temperature_list == False:
                        counter = 0
                        tryout = 0  # this var is to keep it from running endlessly
                        while counter != 1:
                            temperature_list = self.hex_or_temps_parser(1, "1")
                            if temperature_list != None and temperature_list != False and len(temperature_list) == len_of_dict:
                                counter += 1
                            if tryout == 3:
                                return ("Cable Verify Failed","Failed to read all sensors\n only "+str(len(temperature_list))+"/"+str(len_of_dict)
                                        + "sensors found",False)
                            tryout += 1

                    pcba_keys = list()

                    for keys in pcba_dict:
                        pcba_keys.append(keys)
                    key = 0
                    bad_temp_name = str()
                    for temp in temperature_list:
                        if temp > 80 and temp < 90:
                            # return ("Cable Verify Failed","Sensor Number"+pcba_dict.get(pcba_keys[key])+" has no power",False)
                            bad_temp_name = bad_temp_name+ "Sensor: "+str(pcba_dict.get(hex_list[key])) + " has no power\n"
                        elif temp > 91:
                            # return ("Cable Verify Failed","Sensor Number"+pcba_dict.get(pcba_keys[key])+" is a bad sensor",False)
                            bad_temp_name = bad_temp_name + "Sensor: "+str(pcba_dict.get(hex_list[key])) +" bad sensor \n"
                        key += 1

                    if len(bad_temp_name)>= 1:
                        return ("Cable Verify Failed",bad_temp_name,False)
                    else:
                        return ("Cable Verify Successful","All Sensors Passed Test",True)
            except:
                 return ("Cable Verify Failed","There was an error with the test\n Please Try again",False)

    @pyqtSlot()
    def hex_or_temps_parser(self, key, port):
        '''This function grabs either the hex or temps from the cable and returns it as a list'''
        if self.ser.is_open:
            try:
                self.ser.write(("temps "+port+" \r\n").encode())
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

                elif key == 2 and isinstance(temps,list)and temps[2][2] != '0' :
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
