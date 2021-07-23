import csv
import os
import re
import sys

import Factory_Serial_Manager as fsm
# import Continuation
import Test_Utility
import csv_shortcut_loader as continuation
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings, Qt, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QLabel,
    QGridLayout, QGroupBox, QHBoxLayout, QMessageBox, QAction, QActionGroup, QFileDialog, QDialog, QMenu
)

VERSION = "1.0.0"
WINDOW_WIDTH = 1550
WINDOW_HEIGHT = 900


class Main_Utility(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_directory = os.getcwd()

        # self.setFixedSize(WINDOW_WIDTH,WINDOW_HEIGHT)
        print("content margins:",self.getContentsMargins())

        # font configurations
        self.system_font = QApplication.font().family()
        self.label_font = QFont(self.system_font, 12)
        self.config_font = QFont(self.system_font, 12)
        self.config_path_font = QFont(self.system_font, 12)

        # factory Serial Manager Init
        self.sm = fsm.SerialManager()
        self.serial_thread = QThread()
        self.sm.moveToThread(self.serial_thread)
        self.serial_thread.start()

        # menu bar init
        self.settings = QSettings("BeadedStream", "PCBATestUtility")
        self.settings.setValue("configuration_file_path", "/path/to/report/folder/file")
        self.settings.setValue("MetaData_file_path", "/path/to/report/folder/file")
        self.settings.setValue("Sensor_Positions_file_path", "/path/to/report/folder/file")
        self.settings.setValue("Final_Report_Directory", "/path/to/directory")

        self.config = QAction("Settings", self)
        self.config.setShortcut("Ctrl+E")
        self.config.setStatusTip("Program Settings")
        self.config.triggered.connect(self.configuration)

        self.quit = QAction("Quit", self)
        self.quit.setShortcut("Ctrl+Q")
        self.quit.setStatusTip("Exit Program")
        self.quit.triggered.connect(self.close)

        self.about_tu = QAction("About PCBA Test Utility", self)
        self.about_tu.setShortcut("Ctrl+U")
        self.about_tu.setStatusTip("About Program")
        self.about_tu.triggered.connect(self.about_program)

        self.aboutqt = QAction("About Qt", self)
        self.aboutqt.setShortcut("Ctrl+I")
        self.aboutqt.setStatusTip("About Qt")
        self.aboutqt.triggered.connect(self.about_qt)

        # Create menubar
        self.menubar = self.menuBar()
        self.menubar.setFont(self.font(15, 15, True))

        # File
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.config)
        self.file_menu.addAction(self.quit)

        # serial Port
        self.serial_menu = self.menubar.addMenu("&Serial")
        self.serial_menu.installEventFilter(self)
        self.ports_menu = QMenu("&Ports", self)
        self.serial_menu.addMenu(self.ports_menu)
        self.ports_menu.aboutToShow.connect(self.populate_ports)
        self.ports_group = QActionGroup(self)
        self.ports_group.triggered.connect(self.connect_port)

        # Help Menu
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.about_tu)
        self.help_menu.addAction(self.aboutqt)

        # signals form serial manager
        self.sm.data_ready.connect(self.buffer)
        self.sm.call_func.connect(self.sm.pcba_sensor)
        self.sm.switch_sig.connect(self.switch_btn)
        self.sm.clean_scan_page.connect(self.clean_scrollArea)
        self.sm.port_unavailable_signal.connect(self.port_unavailable)

        # variables
        self.cable_image_list = list()
        self.connector_image_type = list()
        self.directory_path = str()

        self.pcba_imgs = list()
        self.pcba_frame_Dict = dict()
        self.continuation_flag = False
        self.pcba_memory = list()
        self.pcba_frame_Highlight = list()
        self.file_specs = list()
        self.report_fail_flag = False
        self.unchanged_hex_ids = list()
        self.hex_number = list()
        self.pcba_hexDict = dict()
        self.pcba_hexList = list()
        self.report_dir = str()
        self.hex_list = list()
        self.hex_lbl_Dict = dict()
        self.hex_lbl_list = list()
        self.total_sensor_ids = list()
        self.file_dict = dict()
        self.file_bool = False
        self.prep_information_flag = False
        self.dtc_serial = str()
        self.counter = 1
        self.pcba_counter = 1
        self.rowCount = 0
        self.colbCount = 0
        self.sensor_num = [False, 0]
        self.check = False
        self.program_eeprom_flag = False
        self.pressed_flag = False
        self.physical_num = 1
        self.lsb = -1
        self.pcba_current_number = 1
        self.order_dict = dict()
        self.before = dict()
        self.success_print = list()
        self.scan_finished = False
        self.build_live_temperature_list = list()
        self.program_live_temperature_list = list()
        self.successfully_programmed_eeprom_flag = False
        self.serial_hex_list = list()
        self.final_order = dict()
        self.final_physical_order = dict()
        self.wrong_sensors_found_list = list()
        self.error_messages = list()
        self.path_check = False
        self.eeprom = str()

        self.image_loader()
        self.initUI()

    def image_loader(self):
        try:
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and senso.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and protection PCBA_rev2.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and protection PCBA with marker_rev2.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and molded sensor.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and molded RA sensor.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\h_logo.png")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\left-arrow.png")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\right-arrow.png")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and molded RA protection.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and molded protection.jpg")
            self.cable_image_list.append(
                self.current_directory + "\\Pictures\\cable and molded protection_with_marker.jpg")
            self.connector_image_type.append(
                self.current_directory + "\\Pictures\\Flying leads.jpg")
            self.connector_image_type.append(
                self.current_directory + "\\Pictures\\XLR connector.jpg")
            # self.connector_type.append("Lemmo connector.jpg") to be created in future name of pic will be different
        except:
            inform = QMessageBox.information(self, "Images Not Found", "There was an error trying to find the images")

    def initUI(self):
        self.main_central_widget = QWidget()
        # self.main_central_widget.setFixedSize(WINDOW_WIDTH,WINDOW_HEIGHT)

        self.gridLayout = QtWidgets.QGridLayout(self.main_central_widget)
        self.gridLayout.setContentsMargins(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.scrollArea = self.get_ScrollArea(False, self.main_central_widget)

        self.main_scroll_window = QtWidgets.QWidget()
        self.main_scroll_window.setEnabled(True)
        self.main_scroll_window.setGeometry(QtCore.QRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        self.logo_img = QtWidgets.QLabel(self.main_scroll_window)  # self.main_scroll_window)
        self.logo_img.setGeometry(QtCore.QRect(175, 100, 1100, 250))
        self.logo_img.setPixmap(QtGui.QPixmap(self.cable_image_list[5]))
        self.logo_img.setScaledContents(True)
        self.logo_img.setObjectName("logo_img")

        self.title_text = QtWidgets.QLabel(self.main_scroll_window)
        self.title_text.setGeometry(QtCore.QRect(580, 50, 600, 600))
        self.title_text.setText("Cable Factory APP II")
        self.title_text.setFont(self.font(45, 20, True))

        # return btn
        self.return_btn = self.get_Button(b_x=0, b_y=780, length=200, height=75, name="Return", name_ptSize=20,
                                          name_wight=75)

        self.manufacture_btn = self.get_Button(embedded=self.main_scroll_window, b_x=400, name="Manufacture",
                                               name_ptSize=17, enabled=True)
        self.manufacture_btn.clicked.connect(self.buildScreen)

        self.calibrate_btn = self.get_Button(embedded=self.main_scroll_window, b_x=655, name="Calibrate", enabled=False)
        # self.calibrate_btn.clicked.connect(self.calibrateScreen)

        self.test_btn = self.get_Button(embedded=self.main_scroll_window, name="Test")
        self.test_btn.clicked.connect(self.testScreen)

        self.scrollArea.setWidget(self.main_scroll_window)
        self.gridLayout.addWidget(self.scrollArea, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setCentralWidget(self.scrollArea)

        # self.central_widget.setLayout(self.gridLayout)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle("BeadedStream Manufacturing App 2")

        self.pcba_gridlayout = QGridLayout()
        self.pcba_gridlayout.setVerticalSpacing(100)
        self.pcba_gridlayout.setHorizontalSpacing(200)
        self.pcba_gridlayout.setColumnStretch(7, 1)
        self.pcba_gridlayout.setRowStretch(22, 1)

        self.pcba_groupBox = QGroupBox()
        self.pcba_groupBox.setFlat(True)
        self.pcba_groupBox.setLayout(self.pcba_gridlayout)

    # Main Screen Button Methods
    def buildScreen(self):
        self.build_central_widget = QWidget(self.main_central_widget)
        self.mainBuild_scrollArea = self.get_ScrollArea(resizable=False, embedded=self.build_central_widget)
        self.mainBuild_scrollArea.setFixedSize(WINDOW_WIDTH,WINDOW_HEIGHT)

        self.tab_window_gridLayout = QtWidgets.QGridLayout(self.build_central_widget)
        self.four_tab_window = QtWidgets.QTabWidget(self.build_central_widget)

        self.tab_window_gridLayout.addWidget(self.four_tab_window, 0, 0, 4, 4)
        self.tab_window_gridLayout.addWidget(self.mainBuild_scrollArea, 0, 0, 4, 4)
        self.main_central_widget.setLayout(self.tab_window_gridLayout)

        # return btn placement
        self.tab_window_gridLayout.addWidget(self.return_btn, 5, 0, 5, 2)
        self.tab_window_gridLayout.setColumnStretch(2, 1)
        self.tab_window_gridLayout.setRowStretch(2, 1)
        self.return_btn.clicked.connect(self.reset_application)  # we might not need to reset it .

        # prep tab
        self.prep_tab = QtWidgets.QWidget()
        self.prep_gridLayout = QtWidgets.QGridLayout()
        self.prep_gridLayout.setSpacing(10)

        self.prep_scrollArea = self.get_ScrollArea()

        # prep btn
        self.file_btn = self.get_Button(b_x=10, b_y=10, length=110, height=75, name="Select File", name_ptSize=20,
                                        name_wight=20, name_bold=True)
        self.file_btn.clicked.connect(self.prep_information)

        self.prep_gridLayout.addWidget(self.file_btn, 0, 0)
        self.prep_gridLayout.addWidget(self.prep_scrollArea, 2, 1, 7, 7)
        self.prep_gridLayout.setRowStretch(8, 0)
        self.prep_gridLayout.setColumnStretch(8, 0)
        self.prep_tab.setLayout(self.prep_gridLayout)

        # scan tab window
        self.scan_tab = QtWidgets.QWidget()
        self.scan_tab.setEnabled(False)
        self.scan_gridLayout = QtWidgets.QGridLayout()
        self.scan_gridLayout.setVerticalSpacing(5)

        self.scan_scrollArea = self.get_ScrollArea()

        self.scan_gridLayout.addWidget(self.scan_scrollArea, 1, 1, 11, 11)

        self.current_pcba = QtWidgets.QLabel()
        self.current_pcba.setFont(self.font(20, 20, True))

        self.dtc_serial_lbl = QtWidgets.QLabel()
        self.dtc_serial_lbl.setFont(self.font(20, 20, True))

        # scan btn
        self.start_button = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="\nScan\n", name_ptSize=20,
                                            name_wight=20)
        self.start_button.clicked.connect(self.start_scan)
        # Stop scan btn
        self.stop_scan_btn = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="\nSTOP\n", name_ptSize=20,
                                             name_wight=20, enabled=False)
        self.stop_scan_btn.setVisible(False)
        self.stop_scan_btn.clicked.connect(self.stop_scan)

        # sort btn
        self.sort_btn = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="\nSort\n", name_ptSize=20,
                                        name_wight=20, enabled=self.sensor_num[0])
        self.sort_btn.clicked.connect(self.OneWireSort)

        # replace btn
        self.replace_btn = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="Replace\nSensor\nBoard",
                                           name_ptSize=20, name_wight=20)
        self.replace_btn.clicked.connect(self.boardReplace)

        arrow_frame = QtWidgets.QFrame()
        arrow_grid = QGridLayout()
        arrow_frame.setLayout(arrow_grid)

        left_arrow_icon = QtGui.QIcon()
        left_arrow_icon.addPixmap(QtGui.QPixmap(self.cable_image_list[6]), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        right_arrow_icon = QtGui.QIcon()
        right_arrow_icon.addPixmap(QtGui.QPixmap(self.cable_image_list[7]), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.left_arrow_btn = QtWidgets.QPushButton()
        self.left_arrow_btn.setIcon(left_arrow_icon)
        self.left_arrow_btn.setIconSize(QtCore.QSize(55, 50))
        self.left_arrow_btn.clicked.connect(self.left_check)
        self.left_arrow_btn.setEnabled(False)

        self.right_arrow_btn = QtWidgets.QPushButton()
        self.right_arrow_btn.setIcon(right_arrow_icon)
        self.right_arrow_btn.setIconSize(QtCore.QSize(55, 50))
        self.right_arrow_btn.clicked.connect(self.right_check)
        self.right_arrow_btn.setEnabled(False)

        arrow_grid.addWidget(self.left_arrow_btn, 0, 0)
        arrow_grid.addWidget(self.right_arrow_btn, 0, 1)

        self.scan_gridLayout.addWidget(self.start_button, 1, 0, 2, 1)
        self.scan_gridLayout.addWidget(self.stop_scan_btn, 1, 0, 2, 1)
        self.scan_gridLayout.addWidget(self.sort_btn, 3, 0, 2, 1)
        self.scan_gridLayout.addWidget(self.replace_btn, 5, 0, 2, 1)
        self.scan_gridLayout.addWidget(self.current_pcba, 0, 6)
        self.scan_gridLayout.addWidget(self.dtc_serial_lbl, 0, 10)
        self.scan_gridLayout.addWidget(arrow_frame, 7, 0)
        self.scan_gridLayout.setColumnStretch(3, 1)
        self.scan_gridLayout.setRowStretch(8, 1)
        self.scan_tab.setLayout(self.scan_gridLayout)

        # build tab
        self.build_tab = QtWidgets.QWidget()
        self.build_tab.setEnabled(False)
        self.build_gridLayout = QtWidgets.QGridLayout()

        self.build_scrollArea = self.get_ScrollArea()

        # Test cable btn
        self.powered_test_btn = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="Test\nCable",
                                                name_ptSize=20, name_wight=20)
        self.powered_test_btn.clicked.connect(self.para_pwr_test)

        self.build_error_box = self.get_err_display_box()
        self.build_error_box[0].setVisible(False)

        self.build_dtc_serial_lbl = QtWidgets.QLabel()
        self.build_dtc_serial_lbl.setFont(self.font(20, 20, True))

        self.build_bar = self.create_progress_bar(maximum=160)
        self.progress_bar_counter = 0

        self.build_gridLayout.addWidget(self.powered_test_btn, 1, 0, 1, 1)
        self.build_gridLayout.addWidget(self.build_bar, 2, 0, 1, 1)
        self.build_gridLayout.addWidget(self.build_dtc_serial_lbl, 0, 10)
        self.build_gridLayout.addWidget(self.build_scrollArea, 1, 1, 11, 11)
        self.build_gridLayout.addWidget(self.build_error_box[0], 12, 1, 2, 11)
        self.build_gridLayout.setColumnStretch(3, 1)
        self.build_tab.setLayout(self.build_gridLayout)

        self.cable_grid = QGridLayout()
        self.cable_group = QGroupBox()
        self.cable_group.setLayout(self.cable_grid)

        # program tab
        self.program_tab = QtWidgets.QWidget()
        self.program_tab.setEnabled(False)

        self.program_gridLayout = QGridLayout()
        self.program_scrollArea = self.get_ScrollArea()

        self.program_tab.setLayout(self.program_gridLayout)
        self.prog_err_box_contents = self.get_err_display_box()
        self.prog_err_box_contents[0].setVisible(False)

        # Program Buttons
        self.cable_verify_btn = self.get_Button(b_x=0, b_y=0, length=100, height=100, name="Cable\nVerify",
                                                name_wight=20, name_ptSize=20)
        self.eeprom_btn = self.get_Button(b_y=0, b_x=0, length=100, height=100, name="Program\nEEPROM", name_wight=20,
                                          name_ptSize=20, enabled=False)
        self.final_test_btn = self.get_Button(b_x=0, b_y=0, height=100, length=100, name="Final Test", name_wight=20,
                                              name_ptSize=20, enabled=False)

        # connections
        self.cable_verify_btn.clicked.connect(self.verify_Cable_Test)
        self.eeprom_btn.clicked.connect(self.eeprom_call)
        # self.final_test_btn.clicked.connect(self.csv)

        # progress Bars
        self.verify_button_prog_bar = self.create_progress_bar(maximum=100)
        self.eeprom_prog_bar = self.create_progress_bar(maximum=100)
        self.final_test_prog_bar = self.create_progress_bar(maximum=200)

        self.prog_dtc_serial_lbl = QtWidgets.QLabel()
        self.prog_dtc_serial_lbl.setFont(self.font(20, 20, True))

        self.program_gridLayout.addWidget(self.cable_verify_btn, 1, 0, 2, 1)
        self.program_gridLayout.addWidget(self.verify_button_prog_bar, 3, 0, 1, 1)
        self.program_gridLayout.addWidget(self.eeprom_btn, 4, 0, 2, 1)
        self.program_gridLayout.addWidget(self.eeprom_prog_bar, 6, 0, 1, 1)
        self.program_gridLayout.addWidget(self.final_test_btn, 7, 0, 2, 1)
        self.program_gridLayout.addWidget(self.final_test_prog_bar, 9, 0, 1, 1)
        self.program_gridLayout.addWidget(self.prog_dtc_serial_lbl, 0, 10)
        self.program_gridLayout.addWidget(self.program_scrollArea, 1, 1, 11, 11)
        self.program_gridLayout.addWidget(self.prog_err_box_contents[0], 12, 1, 2, 11)
        self.program_gridLayout.setRowStretch(10, 1)
        self.program_gridLayout.setColumnStretch(2, 1)
        self.sm.wake_up_call()

        # inputting of widgets
        self.four_tab_window.addTab(self.prep_tab, "")
        self.four_tab_window.addTab(self.scan_tab, "")
        self.four_tab_window.addTab(self.build_tab, "")
        self.four_tab_window.addTab(self.program_tab, "")

        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.prep_tab), "Prep")
        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.scan_tab), "Scan")
        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.build_tab), "Build")
        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.program_tab), "Program")

        self.four_tab_window.setFont(self.font(15, 15, True))

        self.setCentralWidget(self.build_central_widget)

    def testScreen(self):
        self.test_screen = Test_Utility.test_buildScreen(self.main_central_widget, self.sm, self.return_btn)
        self.setCentralWidget(self.test_screen)
        self.test_screen.return_sig.connect(self.close_test)

    def close_test(self):
        self.test_screen.close()
        self.initUI()

    def calScreen(self):
        # calibrate = cal.SomethingForthekids
        pass
    # BuildScreen Button Methods

    # -Prep Tab Methods
    def prep_information(self):
        """ Grabs the file path for the Select File"""
        # if self.sm.check_port() == False:
        #     return
        try:
            if self.prep_information_flag:
                self.reset_prep_info()

            self.file_contents = list()
            file_desc = list()

            select_file = QFileDialog.getOpenFileName(self, "open file", "C:/",
                                                      "Excel (*.csv *.xlsx *.tsv)")
            if (select_file[0] == ''):
                return
            else:
                get_directory_tuple = select_file[0].rindex('/')
                self.report_dir = select_file[0][:get_directory_tuple]
                file = open(select_file[0], "r")

            [self.file_contents.append(x) for x in file]

            if "Sort" in self.file_contents[0]:
                self.continuation_flag = True
                self.cont = self.continuation_of_previously_scanned()
                file_desc = self.cont.get_description_contents()
            else:
                # this loop splits info into individual list
                [file_desc.append(self.file_contents[descript_cont].split(",")) for descript_cont in range(1, 7)]

            # top labels for each page
            self.dtc_serial_lbl.setText("Serial: DTC" + file_desc[0][1])
            self.build_dtc_serial_lbl.setText("Serial: DTC" + file_desc[0][1])
            self.prog_dtc_serial_lbl.setText("Serial: DTC" + file_desc[0][1])
            self.meta_data_serial = file_desc[0][1]

            if self.continuation_flag:
                self.file_specs = self.cont.get_file_specifications()

            else:
                for content in range(7, len(self.file_contents)):
                    self.file_specs.append(self.file_contents[content].split(","))

            # takes off the eeprom from the cable and only includes pcb18b20s
            if self.has_protection_board():
                self.sensor_num[1] = int(file_desc[2][1]) - 1
            else:
                self.sensor_num[1] = int(file_desc[2][1])

            # protection/sensor information
            board_option = self.file_specs[3][0].split("/")

            protection_sensor_text = self.file_specs[3][0][-1] + " " + board_option[0] + " & " + str(
                self.sensor_num[1]) + " Sensor Boards "
            pcba_scan_display = QLabel()
            pcba_build_display = QLabel()
            pcba_program_display = QLabel()
            pcba_scan_display.setText(protection_sensor_text)
            pcba_build_display.setText(protection_sensor_text)
            pcba_program_display.setText(protection_sensor_text)


            pcba_scan_display.setFont(self.font(20, 45, True))
            pcba_build_display.setFont(self.font(20, 15, True))
            pcba_program_display.setFont(self.font(20, 15, 45))

            self.scan_gridLayout.addWidget(pcba_scan_display, 0, 1)
            self.build_gridLayout.addWidget(pcba_build_display, 0, 1)
            self.program_gridLayout.addWidget(pcba_program_display, 0, 1)

            desc_lbl = []
            for desc in range(len(file_desc)):
                desc_lbl.append(QLabel(file_desc[desc][0]))
                desc_lbl.append(QLabel(file_desc[desc][1]))

            [desc_lbl[num].setFont(self.font(15, 20, False)) for num in range(len(desc_lbl))]
            desc_lbl[0].setFont(self.font(20, 20, True))
            desc_lbl[2].setFont(self.font(20, 20, True))
            desc_lbl[4].setFont(self.font(20, 20, True))
            desc_lbl[6].setFont(self.font(20, 20, True))
            desc_lbl[8].setFont(self.font(20, 20, True))
            desc_lbl[10].setFont(self.font(20, 20, True))
            desc_lbl[11].setTextFormat(Qt.AutoText)

            self.file_description = file_desc.copy()
            comp_lbl = list()
            mold_lbl = list()
            section_lbl = list()
            cable_lbl = list()
            addi = 0
            # this for loop makes a label list based on the previous file_spec info
            for _ in self.file_specs:
                comp_lbl.append(QLabel(self.file_specs[addi][0]))
                mold_lbl.append(QLabel(self.file_specs[addi][1]))
                section_lbl.append(QLabel(self.file_specs[addi][2]))
                cable_lbl.append(QLabel(self.file_specs[addi][3]))
                addi += 1
            for amount in range(len(comp_lbl)):
                if amount == 0:  # titles
                    comp_lbl[amount].setFont(self.font(20, 20, True))
                    mold_lbl[amount].setFont(self.font(20, 20, True))
                    section_lbl[amount].setFont(self.font(20, 20, True))
                    cable_lbl[amount].setFont(self.font(20, 20, True))
                else:
                    comp_lbl[amount].setFont(self.font(15, 10, True))
                    mold_lbl[amount].setFont(self.font(15, 10, True))
                    section_lbl[amount].setFont(self.font(15, 10, True))
                    cable_lbl[amount].setFont(self.font(15, 10, True))

            self.frame_group = QGroupBox()
            frame_grid = QGridLayout()

            self.frame_group.setLayout(frame_grid)

            self.frame_1 = QtWidgets.QFrame()
            self.frame_2 = QtWidgets.QFrame()
            self.frame_3 = QtWidgets.QFrame()
            self.frame_4 = QtWidgets.QFrame()

            frame_1_Grid = self.grid(self.frame_1, 0)
            frame_2_Grid = self.grid(self.frame_2, 1)
            frame_3_Grid = self.grid(self.frame_3, 1)
            frame_4_Grid = self.grid(self.frame_4, 1)

            self.frame_1.setLayout(frame_1_Grid)
            self.frame_2.setLayout(frame_2_Grid)
            self.frame_3.setLayout(frame_3_Grid)
            self.frame_4.setLayout(frame_4_Grid)

            frame_grid.addWidget(self.frame_1, 0, 0)
            frame_grid.addWidget(self.frame_2, 0, 2)
            frame_grid.addWidget(self.frame_3, 0, 4)
            frame_grid.addWidget(self.frame_4, 0, 6)

            desc_layout = QGridLayout()
            desc_layout.addWidget(desc_lbl[0], 0, 0)
            desc_layout.addWidget(desc_lbl[1], 0, 1)
            desc_layout.addWidget(desc_lbl[2], 1, 0)
            desc_layout.addWidget(desc_lbl[3], 1, 1)
            desc_layout.addWidget(desc_lbl[4], 2, 0)
            desc_layout.addWidget(desc_lbl[5], 2, 1)
            desc_layout.addWidget(desc_lbl[6], 3, 0)
            desc_layout.addWidget(desc_lbl[7], 3, 1)
            desc_layout.addWidget(desc_lbl[8], 4, 0)
            desc_layout.addWidget(desc_lbl[9], 4, 1)
            desc_layout.addWidget(desc_lbl[10], 5, 0)
            desc_layout.addWidget(desc_lbl[11], 5, 1)

            self.desc_group = QGroupBox()
            self.desc_group.setLayout(desc_layout)

            # content
            ran = 1
            for comp in range(1, len(comp_lbl)):
                if comp < 33:
                    frame_1_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_1_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_1_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_1_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1
                elif comp >= 33 and comp < 65:
                    if comp == 33:
                        ran = 1
                    frame_2_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_2_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_2_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_2_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1
                elif comp >= 65 and comp < 97:
                    if comp == 65:
                        ran = 1
                    frame_3_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_3_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_3_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_3_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1
                elif comp >= 97:  # if a cable has more than 125 this might need to be changed to a while loop
                    if comp == 97:
                        ran = 1
                    frame_4_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_4_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_4_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_4_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1

            self.prep_gridLayout.addWidget(self.desc_group, 1, 1)
            self.prep_scrollArea.setWidget(self.frame_group)

            self.scan_tab.setEnabled(True)
            file.close()

            self.get_connector_type()
            self.get_RA_mold()
            self.get_length_of_sensors()
            self.prep_information_flag = True

            if self.continuation_flag:
                # self.scan_tab.setEnabled(False)
                self.sort_btn.setEnabled(False)
                self.start_button.setEnabled(False)
                # self.pcba_hexList = self.cont.get_hex_list()
                self.build_tab.setEnabled(True)
                hex_list = self.cont.get_hex_list(with_whitespace=True, with_family_code=True)
                num = 1
                for hex in hex_list:
                    self.buffer(num, hex)
                    num += 1
                self.OneWireSort()
                self.program_tab.setEnabled(True)

        except:
            error = QMessageBox.critical(self, "Error", " Incorrect file. Please insert a .csv extension type",
                                         QMessageBox.Ok)

            if error == QMessageBox.Ok:
                # file.close()
                self.prep_information()

    def reset_prep_info(self):
        self.dtc_serial_lbl.setText("")
        self.build_dtc_serial_lbl.setText("")
        self.prog_dtc_serial_lbl.setText("")
        self.file_specs.clear()
        self.file_description.clear()
        self.file_contents.clear()
        empty_grid = QGridLayout()
        self.desc_group.setLayout(empty_grid)
        empty = QLabel(" ")
        self.scan_gridLayout.addWidget(empty, 0, 1)
        self.build_gridLayout.addWidget(empty, 0, 1)
        self.program_gridLayout.addWidget(empty, 0, 1)

    # -Scan Tab Methods
    def start_scan(self):
        try:
            self.switch_btn(False)
            self.sm.total_pcba_num = self.sensor_num[1]
            result = self.sm.scan_board()
            if isinstance(result,bool):
                self.switch_btn(True)
                return
            self.start_button.setVisible(False)
        except:
            self.switch_btn(True)

    def switch_btn(self, reset):
        if reset:
            self.return_btn.setEnabled(True)
            self.start_button.setVisible(True)
            self.stop_scan_btn.setVisible(False)
            self.start_button.setVisible(True)

        elif reset == False:
            self.return_btn.setEnabled(False)
            self.start_button.setVisible(False)
            self.stop_scan_btn.setVisible(True)
            self.stop_scan_btn.setEnabled(True)
        else:
            self.start_button.setVisible(True)
            self.scan_gridLayout.addWidget(self.start_button, 0, 0, 2, 2)

    def stop_scan(self):
        self.sm.stop_scan()

    def buffer(self, number, hexadecimal):
        self.hex_number.append(hexadecimal)
        self.pcbaImgInfo(number, hexadecimal)

    def pcbaImgInfo(self, num, hexD):
        stripped_hex = hexD.strip()
        pcba_frame = QtWidgets.QFrame()
        pcba_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        pcba_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        pcba_frame.setLineWidth(46)
        pcba_frame.setGeometry(QtCore.QRect(0,0,200,100))#x,y,width,height
        pcba_frame.setFixedSize(200,100)

        pcba_image_lbl = QtWidgets.QLabel(pcba_frame)
        pcba_image_lbl.setGeometry(QtCore.QRect(35, 30, 125, 45))
        pcba_image_lbl.setPixmap(QtGui.QPixmap(self.current_directory + "\\Pictures\\Sensor_PCBA.jpg"))
        pcba_image_lbl.setScaledContents(True)
        
        self.hex_number_lbl = QtWidgets.QLabel(pcba_frame)
        self.hex_number_lbl.setGeometry(QtCore.QRect(0, 77, 200, 16))#15,77,300,16
        self.hex_number_lbl.setFont(self.font(14, 14, True))
        self.hex_number_lbl.setFixedSize(200,20)

        without_family_code_id = stripped_hex[:-3]
        self.unchanged_hex_ids.append(without_family_code_id)

        new_info = stripped_hex.replace(" ", "")
        temp = int(new_info, 16)
        self.hex_list.append(new_info)
        self.pcba_hexList.append(temp)

        self.pcba_frame_Highlight.append(stripped_hex)
        self.pcba_hexDict[stripped_hex] = self.counter
        self.hex_lbl_Dict[self.hex_number_lbl] = self.counter
        self.hex_lbl_list.append(self.hex_number_lbl)

        self.hex_number_lbl.setText(self.hex_number[num - 1])

        pcba_right_topCorner_id_lbl = QtWidgets.QLabel(pcba_frame)
        pcba_right_topCorner_id_lbl.setGeometry(QtCore.QRect(35, 10, 45, 21))
        pcba_right_topCorner_id_lbl.setFont(self.font(20, 75, True))

        if self.pcba_counter == 31:
            self.pcba_counter = 1
        if num < 31:
            pcba_right_topCorner_id_lbl.setText("A" + str(num))
        elif num >= 31 and num < 61:
            pcba_right_topCorner_id_lbl.setText("B" + str(self.pcba_counter))
            self.pcba_counter += 1
        elif num >= 61 and num < 91:
            pcba_right_topCorner_id_lbl.setText("C" + str(self.pcba_counter))
            self.pcba_counter += 1
        elif num >= 91 and num < 121:
            pcba_right_topCorner_id_lbl.setText("D" + str(self.pcba_counter))
            self.pcba_counter += 1
        elif num >= 121 and num < 151:
            pcba_right_topCorner_id_lbl.setText("E" + str(self.pcba_counter))
            self.pcba_counter += 1

        self.pcba_orderNum = QLabel(pcba_frame)
        self.pcba_orderNum.setGeometry(QtCore.QRect(130, 9, 50, 25))#144
        self.pcba_orderNum.setFont(self.font(20, 20, True))

        self.pcba_imgs.append(self.pcba_orderNum)
        self.pcba_frame_Dict[pcba_frame] = self.counter

        self.pcba_print(pcba_frame, self.counter - 1)

    def pcba_print(self, box, increment):

        if increment == self.sensor_num[1] - 1:
            self.sensor_num[0] = True
            self.sort_btn.setEnabled(self.sensor_num[0])

        if (increment % 6) == 0:
            self.colbCount = 0
            self.rowCount += 1
        if (self.counter % 30 == 0):
            line = self.line()
            self.pcba_gridlayout.addWidget(line, self.rowCount - 2, 0, 7, 7)
        self.pcba_gridlayout.addWidget(box, self.rowCount, self.colbCount, 2, 2)
        self.colbCount += 1

        self.scan_scrollArea.setWidget(self.pcba_groupBox)

        self.counter += 1

        if self.counter == self.sensor_num[1] + 1:
            if self.continuation_flag == False:
                self.switch_btn(True)
                self.start_button.setEnabled(False)
                QMessageBox.information(self, "Done", "Done!")
                self.temporary_csv()
        else:
            if self.continuation_flag == False:
                self.sm.scan_board()

    def OneWireSort(self):
        if self.report_fail_flag and self.continuation_flag == False:
            inform = QMessageBox.warning(self, "failed save temp",
                                         "Sensors failed to save into a temporary file\n Would you like to re-try?",
                                         QMessageBox.Yes | QMessageBox.No)
            if inform == QMessageBox.Yes:
                self.temporary_csv()
                self.OneWireSort()
            else:
                self.report_fail_flag = False
                self.OneWireSort()
        else:
            if self.continuation_flag == False:
                if self.pressed_flag == True:
                    call = QMessageBox.information(self, "Sort Button",
                                                   "Are you sure that you want to re-sort all the boards one more time? (Y/N) ",
                                                   QMessageBox.Yes | QMessageBox.No)

                    if call == QMessageBox.Yes:
                        self.yesButton()
                        self.lsb = -1
                        self.final_order.clear()
                        self.order_dict.clear()
                        self.physical_num = 1

            self.pressed_flag = True

        zero_list = []
        one_list = []
        bin_hex_list = []

        for hex in self.pcba_hexList:
            bin_hex_list.append(bin(hex))

        # split hex list into zeros and ones
        for binary in bin_hex_list:
            if binary[self.lsb] == "0":
                zero_list.append(binary)
            else:
                one_list.append(binary)

        zList = len(zero_list)
        self.Halfsies(zero_list, 1, len(zero_list))
        self.Halfsies(one_list, zList + 1, len(one_list))

        count = 0
        # this for loop creates a dictionary with binary as key and number as value
        for b in bin_hex_list:
            self.final_order[b] = str(count)
            count += 1

        key_count = 0

        for order in self.final_order:  # order grabs the binary string
            for place in self.order_dict:  # place grabs the physical location
                if order == self.order_dict[place]:# searches throught the binary strings in order dict and puts them in final order
                    self.final_order[order] = place
                    self.hex_lbl_Dict[self.hex_lbl_list[key_count]] = place
                    key_count += 1

        run = 0
        next = 0
        # this nested loop updates the pcba frame with its physical order
        for key in self.final_order:
            for frame in self.pcba_frame_Dict:
                if run == next:
                    self.pcba_frame_Dict[frame] = self.final_order[key]
                run += 1
            run = 0
            next += 1

        c = 0
        for phys_num in self.final_order:  # this loop puts that number as a label to the frame box of pcba's
            self.pcba_imgs[c].setText(str(self.final_order[phys_num]))
            c += 1

        # this bottom loop puts the final order according to its hex so that I may use it for error checking during the parasidic and pwr test
        count = 0
        for run in self.final_order:
            self.final_physical_order[self.hex_list[count]] = self.final_order[run]
            count += 1

        for key in self.final_physical_order:
            self.total_sensor_ids.append(key)

        self.file_btn.setEnabled(False)
        self.right_arrow_btn.setEnabled(True)
        self.highlight(self.physical_num, True)
        self.sort_btn.setEnabled(False)
        self.buildDisplay()
        self.final_order.clear()
        self.build_tab.setEnabled(True)

    def Halfsies(self, list, key, size):
        '''This method sorts and puts the given list into the self.order_dict dictionary'''
        count = 1
        last = -2
        k = key

        for run in range(size):
            hold = list[0]
            while count < len(list):
                if hold[last] < list[count][last]:
                    count += 1
                    last = -2

                elif hold[last] == list[count][last]:
                    last -= 1

                elif hold[last] > list[count][last]:
                    first_index = list.index(hold)
                    hold = list[count]
                    list[first_index], list[count] = list[count], list[first_index]
                    last = -2
                    count = 1
            self.order_dict[k] = hold  # this will put the least on top
            k += 1
            count = 1
            list.remove(hold)

    def left_check(self):
        self.pcba_current_number -= 1
        if self.physical_num < self.sensor_num[1] + 2:
            self.right_arrow_btn.setEnabled(True)

        if self.physical_num == 3:
            self.left_arrow_btn.setEnabled(False)

        if self.physical_num != 1:
            self.highlight(self.physical_num, False)

    def right_check(self):
        self.pcba_current_number += 1
        if self.physical_num > 1:
            self.left_arrow_btn.setEnabled(True)
            # locks button if it reaches the end
        if self.physical_num == self.sensor_num[1]:
            self.right_arrow_btn.setEnabled(False)

        if self.physical_num != self.sensor_num[1] + 1:
            self.highlight(self.physical_num, True)

    def highlight(self, nextNum, rightClick):

        self.current_pcba.setText(str(self.pcba_current_number) + " out of " + str(self.sensor_num[1]))

        if (rightClick):

            for key in self.pcba_frame_Dict:
                if nextNum == self.pcba_frame_Dict.get(key):
                    key.setAutoFillBackground(True)
                    key.setPalette(self.palette(255, 139, 119))
                    if key != self.pcba_memory:
                        self.pcba_memory.append(key)

            if nextNum > 1:
                self.pcba_memory[nextNum - 2].setAutoFillBackground(False)

            self.physical_num += 1
        else:  # left click
            self.pcba_memory[nextNum - 2].setAutoFillBackground(False)
            self.pcba_memory[nextNum - 3].setAutoFillBackground(True)
            self.pcba_memory.pop()
            self.physical_num -= 1

    def boardReplace(self):
        self.message = QDialog()
        self.message.resize(650, 150)
        self.message.setSizeGripEnabled(True)
        self.message.setWindowTitle("Board Replace")

        msg_grid = QGridLayout()
        self.message.setLayout(msg_grid)

        self.msg_lineEdit = QtWidgets.QLineEdit(self.message)
        self.msg_lineEdit.setGeometry(QtCore.QRect(350, 10, 270, 22))
        self.msg_lineEdit.setPlaceholderText("ex: 5")
        self.msg_lineEdit.setEnabled(True)

        replace_label = QtWidgets.QLabel(self.message)
        replace_label.setGeometry(QtCore.QRect(10, 10, 550, 20))
        replace_label.setText("Enter the Board you would like to Replace:")
        replace_label.setFont(self.font(15, 20, True))

        self.msg_lineEdit.returnPressed.connect(self.sortButtonWarning)

        x = self.message.exec_()

    def sortButtonWarning(self):
        try:
            num = int(self.msg_lineEdit.text())
            # these two if statements are an error check!
            if num > self.sensor_num[1] or num < 1:
                error = QMessageBox.critical(self.message, "Error", "Physical number not found please enter again",
                                             QMessageBox.Ok)
                if error == QMessageBox.Ok:
                    self.message.close()
                    self.boardReplace()
            else:
                self.newScan(self.msg_lineEdit.text())
                QMessageBox.information(self.message, "Done","Done ")
                # self.sort_btn.setEnabled(True)
                self.noButton()

        except:
            warning = QMessageBox.critical(self.message, "Error", "Please Type in a number with in the boards!",
                                           QMessageBox.Ok)
            if warning == QMessageBox.Ok:
                self.message.close()
                self.boardReplace()

    def newScan(self, phy_num,update_hex = None):
        if update_hex is None:
            scan_new = QMessageBox.information(self.message, "Scan New pcba", "Please Scan New PCBA Board", QMessageBox.Ok)
            if scan_new == QMessageBox.Ok:
                new_scanned_hex = self.sm.board_replace_scan()
        else:
            new_scanned_hex = update_hex
        # this loop updates self.pcba_hexList
        for oldHex in self.pcba_hexDict:
            if self.pcba_hexDict[oldHex] is int(phy_num):
                old_hex_stripped = oldHex.replace(" ", "")
                new_hex = new_scanned_hex.replace(" ","")

                self.unchanged_hex_ids.insert(self.unchanged_hex_ids.index(oldHex[:-3]),new_scanned_hex)
                self.unchanged_hex_ids.remove(oldHex[:-3])
                self.final_physical_order[new_hex] = self.final_physical_order.get(old_hex_stripped)
                self.update_list_of_sensor_ids(new_id=old_hex_stripped, remove_id=True)#then add the new hex
                self.update_list_of_sensor_ids(new_id=new_hex)
                del self.final_physical_order[old_hex_stripped]
                temp = int(old_hex_stripped, 16)
                index = self.pcba_hexList.index(temp)#this is updated so that we can re-sort
                self.pcba_hexList.remove(temp)
                self.pcba_hexList.insert(index, temp)
                break

        for key in self.hex_lbl_Dict:
            if self.hex_lbl_Dict.get(key) is int(phy_num):
                key.setText(new_scanned_hex)
                break

    def update_list_of_sensor_ids(self, new_list=None, new_id=None, remove_id=False, replace_id=False, index=None,
                                  insert_id=False):
        if remove_id:
            try:
                self.total_sensor_ids.remove(new_id)
            except:
                return
        elif new_list != None:
            self.total_sensor_ids += new_list
        elif replace_id:
            self.total_sensor_ids.insert(index, new_id)
            self.total_sensor_ids.pop(index + 1)
        elif insert_id:
            self.total_sensor_ids.insert(index, new_id)
        else:
            self.total_sensor_ids.append(new_id)
    def noButton(self):
        self.message.close()

    # -Build Tab Methods
    def para_pwr_test(self):
        self.parasidic_and_power_test(build_test = True,progress_bar=self.build_bar)

    def parasidic_and_power_test(self, build_test=True, final_test=False, progress_bar=None):
        self.update_progress_bar(reset=True, progress_bar=progress_bar)
        self.power_end = tuple()
        protection_board = self.has_protection_board()
        self.error_messages.clear()
        err_box = self.get_err_display_box()
        self.pass_flag = False
        if build_test == True:
            self.build_error_box[0].setVisible(False)
            self.build_error_box[1].addWidget(err_box[0])
            self.update_progress_bar(10, progress_bar)

        else:
            self.prog_err_box_contents[0].setVisible(False)
            self.prog_err_box_contents[1].addWidget(err_box[0])
            self.verify_error_tuple = tuple()

        self.power_end = self.sm.Test_Cable(self.sensor_num[1], self.final_physical_order, progress_bar,
                                            self.progress_bar_counter, protection_board,
                                            build_test=build_test)  # you might need to create a signal that sends the value of the progress bar counter back

        if self.power_end == -1:
            return

        # power test result
        if self.power_end == None:
            self.update_progress_bar(140, progress_bar)
            self.print_pwr_para_test_result(("Failed Test!", " Test Failed: Please Try Again", False), err_box,
                                            build_test)
            return
        self.progress_bar_counter = self.power_end[-1]
        if self.power_end[2] == False:
            if isinstance(self.power_end[1], str):  # Exit 2
                self.update_progress_bar(45, progress_bar)
                self.print_pwr_para_test_result(self.power_end, err_box, build_test)

            elif len(self.power_end[1]) >= 1:  # EXIT 1
                self.update_progress_bar(45, progress_bar)
                self.print_pwr_para_test_result(self.power_end, err_box, build_test)

        elif build_test == False and self.power_end[
            2] == True:  # Both program and final test enter here if they pass power test
            self.update_progress_bar(45, progress_bar)
            self.pass_flag = True
            self.print_pwr_para_test_result(self.power_end, err_box, build_test)
            if final_test == False and self.successfully_programmed_eeprom_flag == False:
                self.eeprom_btn.setEnabled(True)
        # para test result for build test
        elif isinstance(self.power_end[4], str) and self.power_end[-2] == False:
            self.update_progress_bar(150, progress_bar)
            self.print_pwr_para_test_result(self.power_end, err_box, build_test)

        elif self.power_end[2] == True and self.power_end[5] == True:  # Both pass Test
            self.pass_flag = True
            self.update_progress_bar(10, progress_bar)
            self.print_pwr_para_test_result(self.power_end, err_box, build_test)
            if build_test == False and final_test == False and self.successfully_programmed_eeprom_flag == False:
                self.eeprom_btn.setEnabled(True)

        else:
            self.update_progress_bar(10, progress_bar)
            self.final_powr_tuple = self.power_end

        self.update_progress_bar(10, progress_bar)
        if self.pass_flag == True and final_test == False:
            self.program_tab.setEnabled(True)

        # temperature display
        if self.power_end[2] == True and self.power_end[-2] == True:
            self.update_progress_bar(10, progress_bar)
            temps = self.sm.get_temps()
            hex = self.sm.get_hex_ids()
            self.update_temperatures(temps, hex, build_test, self.sensor_num[1] + 1)
        else:
            self.update_progress_bar(10, progress_bar)
            temps = self.sm.get_temps()  # check if
            hex = self.sm.get_hex_ids()
            self.update_temperatures(temps, hex, build_test, self.sensor_num[1] + 1)
            self.update_progress_bar(10, progress_bar)
        if build_test:
            progress_bar.setValue(160)  # default will allways make it end at 100%
        elif final_test == True:
            print("final_test counter value: ", self.progress_bar_counter)
            progress_bar.setValue(100)
        else:
            progress_bar.setValue(100)

    def buildDisplay(self):
        cable_grid = QGridLayout()
        cable_grid.setVerticalSpacing(100)
        cable_grid.setHorizontalSpacing(160)
        cable_grid.setRowStretch(2, 1)
        cable_grid.setColumnStretch(10, 1)
        cable_group = QGroupBox()
        cable_group.setLayout(cable_grid)

        program_grid = QGridLayout()
        program_grid.setVerticalSpacing(100)
        program_grid.setHorizontalSpacing(160)
        program_grid.setRowStretch(2, 1)
        program_grid.setColumnStretch(10, 1)
        program_group = QGroupBox()
        program_group.setLayout(program_grid)

        z = 0
        row = 0
        column = 0
        total = self.sensor_num[1]+2

        for qt in range(0, total):
            if column % 9 == 0:
                row += 1
                column = 0
            build_box = self.build_img(z, False)
            prog_Box = self.build_img( z, True)
            cable_grid.addWidget(build_box, row, column, 2, 2)
            program_grid.addWidget(prog_Box, row, column, 2, 2)
            column += 1
            z += 1

        self.build_scrollArea.setWidget(cable_group)
        self.program_scrollArea.setWidget(program_group)

    def build_img(self,orderNum, program):
        cable_frame = QtWidgets.QFrame()
        cable_frame.setGeometry(QtCore.QRect(170, 60, 161, 51))#170,60,161,51
        # cable_frame.setFixedSize(0,0)
        cable_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        cable_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        cable_frame.setLineWidth(46)

        cable_img = QtWidgets.QLabel(cable_frame)
        cable_img.setGeometry(QtCore.QRect(0, 20, 161, 31))

        if orderNum >= 1:
            cable_temperature = QtWidgets.QLabel(cable_frame)
            cable_temperature.setGeometry(QtCore.QRect(110,50,50,23))#x,y,height,width
            cable_temperature.setText("--.-C"+chr(176))#THIS WAS COMMENTED OUT
            cable_temperature.setFont(self.font(15,15,True))
            if program:
                self.program_live_temperature_list.append(cable_temperature)
            else:
                self.build_live_temperature_list.append(cable_temperature)
        # build display
        if program == False:
            if orderNum == 0:#connector
                cable_img.setPixmap(QtGui.QPixmap(self.connector_image_type[0]))
                length = ""
            elif orderNum == 1 and self.has_Marker() is True and self.has_protection_board() is True:  # build page
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[2]))
            elif orderNum == 1 and self.has_Marker() is False and self.has_protection_board() is True:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[1]))
            elif orderNum == 1 and self.has_Marker() is False and self.has_protection_board() is False:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[0]))
            else:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[0]))
        # program page display
        else:
            if orderNum == 0:
                cable_img.setPixmap(QtGui.QPixmap(self.connector_image_type[1]))
            elif self.ra_mold.get(str(orderNum)) is True:
                if orderNum == '1':
                    cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[8]))
                else:
                    cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[4]))
            elif orderNum == 1 and self.has_Marker() is True and self.has_protection_board() is True:  # build page
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[10]))
            elif orderNum == 1 and self.has_Marker() is False and self.has_protection_board() is True:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[9]))
            elif orderNum == 1 and self.has_Marker() is False and self.has_protection_board() is False:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[3]))
            else:
                cable_img.setPixmap(QtGui.QPixmap(self.cable_image_list[3]))

        cable_img.setScaledContents(True)

        length_lbl = QtWidgets.QLabel(cable_frame)
        if self.sensor_length[orderNum-1] == 'N/A' or self.sensor_length[orderNum-1] == '-' or orderNum == 0 :
            length_lbl.setText("")
        else:
            length_lbl.setText(self.sensor_length[orderNum-1])

        if orderNum >= 1:
            if orderNum == 1:#protection board
                if self.has_Marker():
                    marker_lbl = QtWidgets.QLabel(cable_frame)
                    marker_lbl.setText(self.sensor_length[orderNum])
                    marker_lbl.setGeometry(QtCore.QRect(75,0,41,21))#65
                    marker_lbl.setFont(self.font(14,14,True))
                    length_lbl.setGeometry(QtCore.QRect(0,0,70,21))
                    length_lbl.setFont(self.font(15,15,True))
                else:
                    length_lbl.setGeometry(QtCore.QRect(0,0,70,21))
                    length_lbl.setFont(self.font(15,15,True))
                physical_num_lbl = QtWidgets.QLabel(cable_frame)
                physical_num_lbl.setText(str(orderNum))
                physical_num_lbl.setGeometry(QtCore.QRect(130, 0, 41, 20))
                physical_num_lbl.setFont(self.font(16, 16, True))

            else:#The rest of the cables
                if self.sensor_length[orderNum-1] != 'N/A' or self.sensor_length[orderNum-1] != '-':
                    length_lbl.setText(self.sensor_length[orderNum])
                length_lbl.setGeometry(QtCore.QRect(20, 0, 90, 21))
                length_lbl.setFont(self.font(16,16, True))
                physical_num_lbl = QtWidgets.QLabel(cable_frame)
                physical_num_lbl.setText(str(orderNum))
                physical_num_lbl.setGeometry(QtCore.QRect(130, 0, 41, 20))
                physical_num_lbl.setFont(self.font(17,17, True))

        return cable_frame

    def print_pwr_para_test_result(self, result, err_box, build_test=True):
        # pwr Failed test
        if result[2] is False and len(result) >= 3:
            err_box[0].setPalette(self.palette(255, 139, 119))

            if isinstance(result[1], list):
                for physical_num in result[1]:
                    lbl = self.create_label(txt ="Position " + str(physical_num) + " Wrong ID: Unexpected id returned",
                                            f_size= 0,f_weight=30,f_bold= True,g_x= 100,g_y= 100,g_length= 150,g_height= 50)
                    self.error_messages.append(lbl)
                if build_test is True:
                    change = QMessageBox.critical(self, "Wrong Sensor Found",
                                                  "Would you like to update or ignore the new board?",
                                                  QMessageBox.Apply | QMessageBox.Ignore)
                    if change == QMessageBox.Ignore:
                        pass
                    elif change == QMessageBox.Apply:
                        recent_hex_list = self.sm.hex_or_temps_parser(3, "1", optional=True)
                        check = self.sm.get_hex_ids()
                        protection_board = self.get_protection_board_id(1)
                        recent_hex_list.remove(protection_board)
                        for hex in self.unchanged_hex_ids:
                            if hex in recent_hex_list:
                                recent_hex_list.remove(hex)

                        self.newScan(self.power_end[1][0], update_hex=recent_hex_list[0])

            elif isinstance(result[1], str):
                lbl = self.create_label(txt= result[1],f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)
                self.error_messages.append(lbl)

            elif isinstance(result[1], tuple):
                lbl = self.create_label(txt= result[1],f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)
                self.error_messages.append(lbl)

            elif isinstance(result[1], dict):
                for phy_num in result[1]:
                    if result[1].get(phy_num) == 85:
                        lbl = self.create_label(txt = "Position " + str(phy_num + 1) + " Power Failure: Sensor returns 85",
                                                f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)

                    elif result[1].get(phy_num) > 90:
                        lbl = self.create_label(txt= "Position " + str(phy_num + 1) + " Failed: Sensor returns temperature higher than 90 ",
                                                f_size= 30,f_weight=30,f_bold=True, g_x=0, g_y=0,g_length=150, g_height=50)
                    else:
                        lbl = self.create_label(txt= "Position " + str(phy_num + 1) + " Failed: Sensor returned nothing",
                                                f_size= 30,f_weight=30,f_bold=True, g_x=0, g_y=0,g_length=150, g_height=50)
                    self.error_messages.append(lbl)

        # para test
        elif len(result) == 6 and result[2] is False and result[5] is False:
            if isinstance(result[4], str):
                lbl = self.create_label(txt= result[3] + "\n" + result[4],f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)
                self.error_messages.append(lbl)

            if isinstance(result[1], list) and isinstance(result[4], list):
                for physical_num in self.final_physical_order:
                    lbl = self.create_label(txt= "Position: " + str(physical_num) + " Failed id",f_size= 30,f_weight= 30,f_bold= True,g_x= 0,
                                            g_y= 0,g_length= 150,g_height= 50)
                    self.error_messages.append(lbl)

        # PASSED TEST
        elif build_test is False and result[2] is True:
            err_box[0].setPalette(self.palette(50, 205, 50))
            lbl = self.create_label(txt= "Test Succesful!",f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)
            self.error_messages.append(lbl)

        elif result[2] is True and result[5] is True:
            err_box[0].setPalette(self.palette(50, 205, 50))
            lbl = self.create_label(txt= "Test Succesful!",f_size= 30,f_weight= 30,f_bold= True,g_x= 0,g_y= 0,g_length= 150,g_height= 50)
            self.error_messages.append(lbl)

        self.print_to_err_box(err_box, 0, build_test)

    def print_to_err_box(self, box, key, build_test=True):
        if key == 0:
            if build_test is True:
                self.build_error_box[0].setVisible(True)
            else:
                self.prog_err_box_contents[0].setVisible(True)

            self.current_display_error_box = box.copy()

            if len(self.error_messages) == 1:
                box[1].addWidget(self.error_messages[0], 0, 0, 11, 11)

            elif len(self.error_messages) > 1:
                box[0].setPalette(self.palette(255, 139, 119))
                x = 0
                for lbl in self.error_messages:
                    box[1].addWidget(lbl, x, 0, 11, 11)
                    x += 4

            if build_test is True:
                self.build_error_box[1].addWidget(box[0], 11, 1, 2, 11)
            else:
                self.prog_err_box_contents[1].addWidget(box[0], 11, 1, 2, 11)
        elif key == 1:
            self.build_error_box[0].setVisible(True)
            self.prog_err_box_contents[0].setVisible(True)
            box[0].setVisible(True)
            box[0].setPalette(self.palette(50, 205, 50))
            eeprom_message = QLabel()
            eeprom_message.setText(self.programmed_success_message)
            eeprom_message.setFont(self.font(30, 30, True))
            box[1].addWidget(eeprom_message, 0, 0, 11, 11)

            # self.program_gridLayout.addWidget(box[0],12,1,2,11)
            self.prog_err_box_contents[1].addWidget(box[0], 11, 1, 2, 11)
            print("length of Qgridlaout: ", len(self.prog_err_box_contents[1]))
        elif key == 2:
            self.prog_err_box_contents[0].setVisible(True)
            box[0].setVisible(True)
            box[0].setPalette(self.palette(255, 139, 119))
            fail_message = QLabel()
            fail_message.setText(self.fail_message)
            fail_message.setFont(self.font(10, 10, True))
            box[1].addWidget(fail_message, 0, 0, 11, 11)

            self.prog_err_box_contents[1].addWidget(box[0], 11, 1, 2, 11)
            self.program_gridLayout.addWidget(box[0], 12, 1, 2, 11)

    def update_temperatures(self,temps_list,hex_list,build_test,total_sensors):
        try:
            has_protection_board = self.sm.check_eeprom()
            index = 0
            if isinstance(has_protection_board,bool):
                for id in hex_list:
                    if id not in self.total_sensor_ids:
                        self.update_list_of_sensor_ids(index = 0,insert_id=True,new_id=id)

            if build_test:
                if total_sensors == len(temps_list):
                    for lbl in self.build_live_temperature_list:
                        lbl.setText(str(temps_list[index])[:4]+"C"+chr(176))
                        index += 1
                else:
                    if isinstance(has_protection_board, tuple):
                        self.build_live_temperature_list[index].setText("--C" + chr(176))
                        index +=1

                    for key in self.total_sensor_ids:
                        if key in hex_list:
                            self.build_live_temperature_list[index].setText(str(temps_list[hex_list.index(key)])[:4]+"C"+chr(176))
                        else:
                            self.build_live_temperature_list[index].setText("--C" + chr(176))
                        index += 1
            #program test and passed
            else:
                if total_sensors == len(temps_list):
                    for lbl in self.program_live_temperature_list:
                        lbl.setText(str(temps_list[index])[:4]+"C"+chr(176))
                        index += 1
                else:
                    if isinstance(has_protection_board, tuple):
                        self.program_live_temperature_list[index].setText("--C" + chr(176))
                        index +=1

                    for key in self.total_sensor_ids:
                        if key in hex_list:
                            self.program_live_temperature_list[index].setText(str(temps_list[hex_list.index(key)])[:4]+"C"+chr(176))
                        else:
                            self.program_live_temperature_list[index].setText("--C"+ chr(176))
                        index += 1
        except:
            inform = QMessageBox.warning(self,"No sensors Detected","There was an error, No sensors detected")
            return


    # Program Tab Methods
    def verify_Cable_Test(self):
        self.prog_err_box_contents[0].setVisible(False)
        self.parasidic_and_power_test(build_test = False,progress_bar=self.verify_button_prog_bar)
        self.update_progress_bar(amount=10, progress_bar=self.verify_button_prog_bar)

    def eeprom_call(self):
        self.update_progress_bar(reset = True,progress_bar = self.eeprom_prog_bar)
        self.prog_err_box_contents[0].setVisible(False)
        self.update_progress_bar(amount=10,progress_bar=self.eeprom_prog_bar)
        eeprom_box = self.get_err_display_box()
        eeprom_box[0].setVisible(False)
        self.prog_err_box_contents[1].addWidget(eeprom_box[0])

        metaData_info_list = list()
        lead = self.file_description[4][1][:-1]
        metaData_info_list.append("serial @ "+self.meta_data_serial)
        metaData_info_list.append("lead @ "+lead)
        sensor_positions_list = self.get_sensor_positions()
        self.update_progress_bar(amount=10, progress_bar=self.eeprom_prog_bar)

        if self.continuation_flag:
            self.update_progress_bar(amount=10, progress_bar=self.eeprom_prog_bar)
            self.unchanged_hex_ids = self.cont.get_hex_list(with_whitespace = True)
            protection_board= self.get_protection_board_id(1)
            self.unchanged_hex_ids.insert(0,protection_board)

        else:
            self.update_progress_bar(amount=10, progress_bar=self.eeprom_prog_bar)
            protection_board = self.get_protection_board_id(1)
            self.unchanged_hex_ids.insert(0,protection_board)
            #grab serial num info and lead info
        self.sm.eeprom_program(metaData_info_list,sensor_positions_list,self.unchanged_hex_ids)
        self.update_progress_bar(amount=20, progress_bar=self.eeprom_prog_bar)

        self.programmed_success_message = "EEProm Program Successful!"
        self.final_test_btn.setEnabled(True)
        self.eeprom_btn.setEnabled(False)
        self.update_progress_bar(amount=20, progress_bar=self.eeprom_prog_bar)
        self.print_to_err_box(eeprom_box, 1)
        self.update_progress_bar(amount=30, progress_bar=self.eeprom_prog_bar)
        self.successfully_programmed_eeprom_flag = True
        # self.print_to_err_box(self.prog_err_box_contents[1],1)

    def get_sensor_positions(self):
        sensor_positions = list()
        specs = self.file_specs.copy()
        specs.pop(0)
        specs.pop(0)
        specs.pop(0)

        sensor_positions.append("0.0")
        for position in specs:
            sensor_positions.append(position[2][:-1])
        sensor_positions.pop()
        return sensor_positions

    def get_protection_board_id(self, key):
        '''cycle through all ids and remove them if they are in the previous list, then return the remaining one.'''
        if key is 0:
            ids = self.sm.get_hex_ids()
            for id in self.final_physical_order:
                if id in ids:
                    ids.remove(id)
            return ids[0]
        else:
            id_list = self.sm.get_unchanged_ids()
            for id in self.unchanged_hex_ids:
                if id in id_list:
                    id_list.remove(id)
                # elif id in self.unchanged_hex_ids:
            return id_list[0]









    # Utility Functions
    def font(self, ptSize, weigth, bold):
        font = QtGui.QFont()
        font.setFamily("Times New Roman")  # System
        font.setPointSize(ptSize)
        font.setBold(bold)
        font.setWeight(weigth)
        return font

    def palette(self, red, green, blue):
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(red, green, blue))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        return palette

    def line(self):
        line = QtWidgets.QFrame()
        line.setGeometry(QtCore.QRect(10, 350, 781, 16))

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Mid, brush)

        line.setPalette(palette)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setMidLineWidth(20)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        return line

    def get_ScrollArea(self, resizable=True, embedded=None):
        if embedded == None:
            scrollArea = QtWidgets.QScrollArea()
        else:
            scrollArea = QtWidgets.QScrollArea(embedded)

        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        scrollArea.setWidgetResizable(resizable)
        return scrollArea

    def clean_scrollArea(self, ):
        self.pcba_gridlayout = QGridLayout()
        self.pcba_gridlayout.setVerticalSpacing(100)
        self.pcba_gridlayout.setHorizontalSpacing(200)
        self.pcba_gridlayout.setColumnStretch(7, 1)
        self.pcba_gridlayout.setRowStretch(22, 1)

        self.pcba_groupBox = QGroupBox()
        self.pcba_groupBox.setFlat(True)
        self.pcba_groupBox.setLayout(self.pcba_gridlayout)

        self.reset_scan_variables()
        self.scan_scrollArea.setWidget(self.pcba_groupBox)

    def reset_scan_variables(self):
        self.hex_number.clear()
        self.hex_list.clear()
        self.unchanged_hex_ids.clear()
        self.pcba_hexList.clear()
        self.pcba_frame_Highlight.clear()
        self.pcba_hexDict.clear()
        self.hex_lbl_Dict.clear()
        self.hex_lbl_list.clear()
        self.pcba_imgs.clear()
        self.pcba_frame_Dict.clear()
        self.pcba_counter = 1
        self.counter = 1
        self.sensor_num[0] = False
        self.rowCount = 0
        self.colbCount = 0

    def get_Button(self, embedded=None, b_x=895, b_y=400, length=180, height=160, name="Temp", name_ptSize=20,
                   name_wight=75, name_bold=True, enabled=True):
        if embedded == None:
            button = QtWidgets.QPushButton()
        else:
            button = QtWidgets.QPushButton(embedded)

        button.setGeometry(QtCore.QRect(b_x, b_y, length, height))
        button.setText(name)
        button.setFont(self.font(name_ptSize, name_wight, name_bold))
        button.setEnabled(enabled)
        return button

    def grid(self, frame, boxNum):

        component = QLabel("Component")
        mold = QLabel("Mold")
        section = QLabel("Section")
        cable = QLabel("Cable Type")

        component.setFont(self.font(20, 20, True))
        mold.setFont(self.font(20, 20, True))
        section.setFont(self.font(20, 20, True))
        cable.setFont(self.font(20, 20, True))

        frame_grid = QGridLayout()
        frame_grid.setVerticalSpacing(0)
        frame_grid.setHorizontalSpacing(1)
        frame_grid.addWidget(component, 0, 0)
        frame_grid.addWidget(mold, 0, 2)
        frame_grid.addWidget(section, 0, 4)
        frame_grid.addWidget(cable, 0, 6)
        frame_grid.setRowStretch(35, 1)

        if boxNum == 1:
            line = QtWidgets.QFrame(frame)
            line.setWindowModality(QtCore.Qt.NonModal)
            line.setGeometry(QtCore.QRect(-7, 0, 10, 1250))
            line.setFrameShadow(QtWidgets.QFrame.Plain)
            line.setLineWidth(5)
            line.setFrameShape(QtWidgets.QFrame.VLine)

        return frame_grid

    def create_square_frame(self, embedded=None, x=0, y=0, length=200, height=200):
        if embedded == None:
            frame = QtWidgets.QFrame()
        else:
            frame = QtWidgets.QFrame(embedded)

        frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frame.setGeometry(QtCore.QRect(x, y, height, length))
        return frame

    def create_label(self, embedded=None, has_pixmap=False, txt="", f_size=0, f_weight=0, f_bold=False, g_x=0, g_y=0,
                     g_length=0,g_height=0, pixmap="", scale_content=False):
        ''' go back and adjust all of the label calls to call to this function, do this during the refactoring phase.'''
        if embedded == None:
            lbl = QtWidgets.QLabel()
        else:
            lbl = QtWidgets.QLabel(embedded)

        if has_pixmap:
            lbl.setPixmap(QtGui.QPixmap(pixmap))
            lbl.setScaleContents(scale_content)

        lbl.setText(txt)
        lbl.setFont(self.font(f_size, f_weight, f_bold))
        lbl.setGeometry(QtCore.QRect(g_x, g_y, g_length, g_height))
        return lbl

    def create_progress_bar(self, frame=None, maximum=100):
        if frame == None:
            prog_bar = QtWidgets.QProgressBar()
        else:
            prog_bar = QtWidgets.QProgressBar(frame)

        prog_bar.setGeometry(0, 40, 100, 20)
        prog_bar.setMinimum(0)
        prog_bar.setMaximum(maximum)
        return prog_bar

    def update_progress_bar(self, amount=0, progress_bar=None, reset=False):
        if reset == True:
            self.progress_bar_counter = 0
            progress_bar.setValue(0)
        else:
            self.progress_bar_counter += amount
            progress_bar.setValue(self.progress_bar_counter)

    def has_protection_board(self):
        protection_board = self.file_specs[3][0]
        pb = protection_board[:10]
        if pb == 'Protection':
            return True
        else:
            return False

    def has_Marker(self):
        marker_list = self.file_specs[2]
        counter = 0
        for detail in marker_list:
            if detail != "N/A":
                counter += 1

        if counter >= 3:
            return True
        else:
            return False

    def get_file_specifications(self):
        return self.contents_list[7:]

    def get_err_display_box(self):
        display_box_contents = list()

        internal_box_frame = self.create_square_frame(x=0, y=0, length=600, height=600)  # make box highlight red
        internal_box_frame.setAutoFillBackground(True)
        internal_frame_grid = QGridLayout()
        internal_box_frame.setLayout(internal_frame_grid)

        scroll_grid = QGridLayout()
        scroll_grid.setSpacing(20)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setLayout(scroll_grid)

        internal_frame_grid.addWidget(scroll_area, 0, 0)

        display_box_contents.append(internal_box_frame)
        display_box_contents.append(scroll_grid)
        display_box_contents.append(scroll_area)
        display_box_contents.append(internal_frame_grid)

        return display_box_contents

    def get_description_contents(self):
        return self.contents_list[1:7]

    def continuation_of_previously_scanned(self):
        cont = continuation.Continuation(self.file_contents)
        return cont

    def temporary_csv(self):
        try:
            hexlist = self.unchanged_hex_ids.copy()
            date = self.sm.get_date(True)

            if self.report_dir == "":
                pathway = QMessageBox.warning(self, "Select Path",
                                              "Please select a directory to load your temporary csv document",
                                              QMessageBox.Ok)
                if pathway == QMessageBox.Ok:
                    self.set_report_location()
            n = 0
            for detail in self.file_specs:
                self.file_specs[n][-1] = detail[-1].replace("\n", "")
                n += 1

            final_list = self.file_description + self.file_specs
            x = 0
            h = 0
            with open(self.report_dir + "/DTC-" + final_list[0][1] + "_Sort_" + date + ".csv", 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Description", "Sort", date])
                for _ in final_list:
                    if x == 0:
                        writer.writerow(
                            [final_list[x][0], final_list[x][1], final_list[x][2]])
                    elif x == 6:
                        writer.writerow(
                            [final_list[x][0], final_list[x][1], final_list[x][2], final_list[x][3], "sensor id"])
                    elif x > 9:
                        if h >= len(hexlist):
                            hexlist.append(" ")
                        writer.writerow(
                            [final_list[x][0], final_list[x][1], final_list[x][2], final_list[x][3], hexlist[h]])
                        h += 1
                    else:
                        writer.writerow([final_list[x][0], final_list[x][1], final_list[x][2], final_list[x][3], "-"])
                    x += 1
            self.report_fail_flag = False

        except:
            QMessageBox.information(self, "failed to Save Temp file", "There was an error trying to save the temp file")
            self.report_fail_flag = True

    # file setting Modules
    def configuration(self):

        FILE_BTN_WIDTH = 30
        self.path_check = True

        self.settings_widget = QDialog(self)

        self.configuration_btn = QPushButton("[...]")
        self.configuration_btn.setFixedWidth(FILE_BTN_WIDTH)
        self.configuration_lbl = QLabel("Set Configuration save location: ")
        self.configuration_lbl.setFont(self.config_font)
        self.configuration_path_lbl = QLabel(self.settings.value("configuration_file_path"))
        self.configuration_path_lbl.setFont(self.config_path_font)
        self.configuration_path_lbl.setStyleSheet("QLabel {color: blue}")
        self.configuration_btn.clicked.connect(self.cal_report_loc)

        self.meta_data_btn = QPushButton("[...]")
        self.meta_data_btn.setEnabled(True)
        self.meta_data_btn.setFixedWidth(FILE_BTN_WIDTH)
        self.meta_data_lbl = QLabel("Set MetaData save location: ")
        self.meta_data_lbl.setFont(self.config_font)
        self.meta_data_path_lbl = QLabel(self.settings.value("MetaData_file_path"))
        self.meta_data_path_lbl.setFont(self.config_path_font)
        self.meta_data_path_lbl.setStyleSheet("QLabel {color: blue}")
        self.meta_data_btn.clicked.connect(self.meta_report_loc)

        self.sensor_btn = QPushButton("[...]")
        self.sensor_btn.setEnabled(True)
        self.sensor_btn.setFixedWidth(FILE_BTN_WIDTH)
        self.sensor_lbl = QLabel("Set Sensor Location save location: ")
        self.sensor_lbl.setFont(self.config_font)
        self.sensor_path_lbl = QLabel(self.settings.value("Sensor_Positions_file_path"))
        self.sensor_path_lbl.setFont(self.config_path_font)
        self.sensor_path_lbl.setStyleSheet("QLabel {color: blue}")
        self.sensor_btn.clicked.connect(self.sensor_report_loc)

        self.final_btn = QPushButton("[...]")
        self.final_btn.setFixedWidth(FILE_BTN_WIDTH)
        self.final_lbl = QLabel("Set the location for the final report:")
        self.final_lbl.setFont(self.config_font)
        self.final_path_lbl = QLabel(self.settings.value("Final_Report_Directory"))
        self.final_path_lbl.setFont(self.config_path_font)
        self.final_path_lbl.setStyleSheet("QLabel {color: blue}")
        self.final_btn.clicked.connect(self.set_report_location)

        self.get_all_btn = QPushButton("[Get All Files]")
        self.get_all_btn.clicked.connect(self.collect_all)

        save_loc_layout = QGridLayout()
        save_loc_layout.addWidget(self.configuration_lbl, 0, 0)
        save_loc_layout.addWidget(self.configuration_btn, 0, 1)
        save_loc_layout.addWidget(self.configuration_path_lbl, 1, 0)

        save_loc_layout.addWidget(self.meta_data_lbl, 2, 0)
        save_loc_layout.addWidget(self.meta_data_btn, 2, 1)
        save_loc_layout.addWidget(self.meta_data_path_lbl, 3, 0)

        save_loc_layout.addWidget(self.sensor_lbl, 4, 0)
        save_loc_layout.addWidget(self.sensor_btn, 4, 1)
        save_loc_layout.addWidget(self.sensor_path_lbl, 5, 0)

        save_loc_layout.addWidget(self.final_lbl, 6, 0)
        save_loc_layout.addWidget(self.final_btn, 6, 1)
        save_loc_layout.addWidget(self.final_path_lbl, 7, 0)

        save_loc_group = QGroupBox("Save Locations")
        save_loc_group.setLayout(save_loc_layout)

        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_settings)

        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.get_all_btn)
        button_layout.addWidget(apply_btn)

        hbox_bottom = QHBoxLayout()
        hbox_bottom.addStretch()
        hbox_bottom.addWidget(save_loc_group)
        hbox_bottom.addStretch()

        grid = QGridLayout()
        grid.addLayout(hbox_bottom, 0, 0)
        grid.addLayout(button_layout, 1, 0)
        grid.setHorizontalSpacing(100)

        self.settings_widget.setLayout(grid)
        self.settings_widget.setWindowTitle("Cable Manufacturing App 2")
        self.settings_widget.show()

    def apply_settings(self):
        """Read user inputs and apply settings."""
        self.get_all_btn.setEnabled(True)
        self.settings.setValue("configuration_file_path", self.configuration_path_lbl.text())
        self.settings.setValue("MetaData_file_path", self.meta_data_path_lbl.text())
        self.settings.setValue("Sensor_Positions_file_path", self.sensor_path_lbl.text())
        self.settings.setValue("Final_Report_Directory", self.final_path_lbl.text())

        QMessageBox.information(self.settings_widget, "Information",
                                "Settings applied!")

        self.settings_widget.close()

    def set_report_location(self):
        """Opens file dialog for setting the save location for the report."""
        self.report_dir = QFileDialog.getExistingDirectory(
            self, "Select report save location.")
        if self.path_check == True:
            self.final_path_lbl.setText(self.report_dir)

    def find_directory(self, path):
        # takes out the file, this is assuming the path is of a file and we are trying to grab its directory
        temp_dir_string_list = path.split("/")
        temp_dir_string_list.pop()
        initial_counter = 0
        for path in temp_dir_string_list:
            if initial_counter > 0:
                self.directory_path = self.directory_path + "/" + path
            else:
                self.directory_path = self.directory_path + path
                initial_counter += 1

    def cal_report_loc(self):
        cal_dir = QFileDialog.getOpenFileName(self, "Configuration file: choose save location.", "C:/", "text(*.txt)")
        self.find_directory(cal_dir[0])

        self.file_dict[0] = cal_dir[0]
        if cal_dir[0] == "":
            return

        self.configuration_path_lbl.setText(cal_dir[0])

    def meta_report_loc(self):
        meta_dir = QFileDialog.getOpenFileName(self, caption="MetaData: choose save location.",
                                               directory=self.directory_path, filter="text(*.txt)")
        self.file_dict[1] = meta_dir[0]

        if meta_dir[0] == "":
            return

        self.meta_data_path_lbl.setText(meta_dir[0])

    def sensor_report_loc(self):
        sensor_dir = QFileDialog.getOpenFileName(self, caption="Sensor Positions: choose save location.",
                                                 directory=self.directory_path, filter="text(*.txt)")
        self.file_dict[2] = sensor_dir[0]
        if sensor_dir[0] == "":
            return

        self.sensor_path_lbl.setText(sensor_dir[0])

    def collect_all(self):
        '''function automates the file browser to pop up consecutively until they cancel or select the files they need.'''
        if self.file_dict == None:
            self.file_dict = dict()
        else:
            self.file_dict.clear()
        cancel_flag = True

        while cancel_flag:
            configuration_file = QFileDialog.getOpenFileName(self, caption="Configuration file: choose save location.",
                                                             directory="C:/",
                                                             filter="text(*.txt)")  # create a default directory to the previous one
            cal_file_is_canceled = self.check_if_canceled(configuration_file)
            if cal_file_is_canceled:
                break
            else:
                self.find_directory(configuration_file[0])
                self.file_dict[0] = configuration_file[0]
                self.configuration_path_lbl.setText(configuration_file[0])

            meta_file = QFileDialog.getOpenFileName(self, caption="MetaData: choose save location.",
                                                    directory=self.directory_path,
                                                    filter="text(*.txt)")  # make the default directory in this one the previously selected.
            meta_is_canceled = self.check_if_canceled(meta_file)
            if meta_is_canceled:
                break
            else:
                self.file_dict[1] = meta_file[0]
                self.meta_data_path_lbl.setText(meta_file[0])

            sensor_file = QFileDialog.getOpenFileName(self, caption="Sensor Positions: choose save location.",
                                                      directory=self.directory_path, filter="text(*.txt)")
            sensor_is_canceled = self.check_if_canceled(sensor_file)
            if sensor_is_canceled:
                break
            else:
                self.file_dict[2] = sensor_file[0]
                self.sensor_path_lbl.setText(sensor_file[0])

            final_report_dir = QFileDialog.getExistingDirectory(self, "Final Report: Choose a save location")
            final_report_is_canceled = self.check_if_canceled(final_report_dir)
            if final_report_is_canceled:
                break
            else:
                self.final_path_lbl.setText(final_report_dir)

            cancel_flag = False

    def check_if_canceled(self, result):
        if result[0] == "":
            return True
        else:
            return False

    def cancel_settings(self):
        """Close the settings widget without applying changes."""
        self.settings_widget.close()

    def get_connector_type(self):
        connector = self.file_specs[1][0]
        type = connector[6:]
        if type == "Bare Leads":
            self.connector_type = self.connector_image_type[0]
        elif type == "XLR":
            self.connector_type = self.connector_image_type[1]
        elif type == "Lemo Connector":
            self.connector_type = self.connector_image_type[2]

    def has_RA_mold(self):
        for mold in self.file_specs:
            if mold[1] == "RA mold":
                return True
        return False

    def get_length_of_sensors(self):
        self.sensor_length = list()
        for length in range(1, len(self.file_specs)):
            self.sensor_length.append(self.file_specs[length][2])

    def get_RA_mold(self):
        self.ra_mold = dict()
        counter = 0
        for mold in self.file_specs:
            if mold[1] == "RA mold" and counter >= 3:
                self.ra_mold[mold[0][-1]] = True
            elif counter >= 3:
                self.ra_mold[mold[0][-1]] = False
            counter += 1

    # port configuration Modules
    def populate_ports(self):
        """Doc string goes here."""
        ports = fsm.SerialManager.scan_ports()
        self.ports_menu.clear()

        if not ports:
            self.ports_menu.addAction("None")
            self.sm.close_port()

        for port in ports:
            port_description = port.description
            action = self.ports_menu.addAction(port_description)
            port_name = port.device
            if self.sm.is_connected(port_name):
                action.setCheckable(True)
                action.setChecked(True)
            self.ports_group.addAction(action)

    def connect_port(self, action: QAction):
        """Connects to a COM port by parsing the text from a clicked QAction
        menu object."""

        p = "COM[0-9]+"
        m = re.search(p, action.text())
        if m:
            port_name = m.group()
            if (self.sm.is_connected(port_name)):
                action.setChecked
                self.sm.scan_board()
            self.sm.open_port(port_name)
        else:
            QMessageBox.warning(self, "Warning", "Invalid port selection!")
        self.sm.wake_up_call()

    def port_unavailable(self):
        """Displays warning message about unavailable port."""
        QMessageBox.warning(self, "Warning", "Port unavailable!")

    def about_qt(self):
        """Displays information about Qt."""
        QMessageBox.aboutQt(self, "About Qt")

    def about_program(self):
        ABOUT_TEXT = f"""
             Manufacturing App 2. Copyright beadedstream, 2021.
             v{VERSION}
             """
        """Displays information about the program."""
        QMessageBox.about(self, "About PCBA Test Utility", ABOUT_TEXT)

    # pyinstaller path function
    def resource_path(self, relative_path):
        """Gets the path of the application relative root path to allow us
        to find the logo."""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def reset_application(self):
        """Resetting variables from the init func"""
        self.update_progress_bar(amount=20, progress_bar=self.final_test_prog_bar)
        self.file_btn.setEnabled(True)
        # self.hex_number_lbl.clear()
        self.pcba_hexList.clear()
        self.hex_list.clear()
        self.pcba_frame_Highlight.clear()
        self.hex_lbl_Dict.clear()
        self.pcba_hexDict.clear()
        self.hex_lbl_list.clear()
        self.pcba_counter = 1
        # self.file_contents.clear()
        self.file_specs.clear()
        self.sensor_num = [False, 0]
        # self.file_description.clear()
        self.colbCount = 0
        self.rowCount = 0
        self.pcba_frame_Dict.clear()
        self.unchanged_hex_ids.clear()
        self.pcba_memory.clear()
        self.sensor_length.clear()
        self.physical_num = 1
        # self.lsb = -1
        self.counter = 1
        self.final_order.clear()
        self.order_dict.clear()
        self.pcba_imgs.clear()
        self.file_dict.clear()
        self.prep_information_flag = False
        self.file_bool = False
        self.pressed_flag = False
        # self.desc_group.deleteLater()
        self.pcba_groupBox.deleteLater()
        # self.frame_group.deleteLater()
        self.scan_tab.setEnabled(False)
        self.build_tab.setEnabled(False)
        # self.total_sensor_ids.clear()
        self.program_tab.setEnabled(False)
        self.report_dir = ""
        self.hex_number.clear()
        self.pcba_current_number = 1
        self.error_num = 0
        self.path_check = False
        self.program_eeprom_flag = False
        self.scan_finished = False
        self.success_print.clear()
        self.build_live_temperature_list.clear()
        self.final_physical_order.clear()
        self.program_live_temperature_list.clear()
        self.before.clear()
        self.error_messages.clear()
        self.wrong_sensors_found_list.clear()
        self.successfully_programmed_eeprom_flag = False
        # self.settings.setValue("report_file_path", "/path/to/report/folder")
        ee = list(self.eeprom)
        ee.clear()
        self.eeprom = tuple(ee)
        self.sm.reset_variables()
        self.update_progress_bar(reset=True, progress_bar=self.final_test_prog_bar)
        self.sm.close_port()
        self.settings.setValue("configuration_file_path", "/path/to/report/folder/file")
        self.settings.setValue("MetaData_file_path", "/path/to/report/folder/file")
        self.settings.setValue("Sensor_Positions_file_path", "/path/to/report/folder/file")
        self.settings.setValue("Final_Report_Directory", "/path/to/directory")
        self.initUI()


def showscreen():
    app = QApplication([])
    app.setStyle("fusion")
    window = Main_Utility()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    showscreen()
