import csv
import os
import re
import sys
import time
import serial
# import Continuation
import Test_Utility
import Calibration_Utility as cal
import Factory_Serial_Manager as fsm
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings, Qt, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QLabel,
    QGridLayout, QGroupBox, QHBoxLayout, QProgressBar,
    QMessageBox, QAction, QActionGroup, QFileDialog, QDialog, QMenu
)
VERSION = "1.0.0"
WINDOW_WIDTH = 1550
WINDOW_HEIGHT = 900

class Main_Utility(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_directory = os.getcwd()
        #font configurations
        self.system_font = QApplication.font().family()
        self.label_font = QFont(self.system_font, 12)
        self.config_font = QFont(self.system_font, 12)
        self.config_path_font = QFont(self.system_font, 12)

        #factory Serial Manager Init
        self.sm = fsm.SerialManager()
        self.serial_thread = QThread()
        self.sm.moveToThread(self.serial_thread)
        self.serial_thread.start()

        #menu bar init
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

        #File
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.config)
        self.file_menu.addAction(self.quit)

        #serial Port
        self.serial_menu = self.menubar.addMenu("&Serial")
        self.serial_menu.installEventFilter(self)
        self.ports_menu = QMenu("&Ports", self)
        self.serial_menu.addMenu(self.ports_menu)
        self.ports_menu.aboutToShow.connect(self.populate_ports)
        self.ports_group = QActionGroup(self)
        self.ports_group.triggered.connect(self.connect_port)

        #Help Menu
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.about_tu)
        self.help_menu.addAction(self.aboutqt)

        #signals form serial manager
        # self.sm.data_ready.connect(self.buffer)
        # self.sm.call_func.connect(self.sm.pcba_sensor)
        self.sm.port_unavailable_signal.connect(self.port_unavailable)

        #variables
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
        # self.main_central_widget.isFullScreen()

        self.gridLayout = QtWidgets.QGridLayout(self.main_central_widget)
        self.gridLayout.setContentsMargins(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.scrollArea = self.get_ScrollArea(False,self.main_central_widget)

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

        self.test_btn = self.get_Button(embedded=self.main_scroll_window,name="Test")
        self.test_btn.clicked.connect(self.testScreen)

        self.calibrate_btn = self.get_Button(embedded=self.main_scroll_window,b_x=655,name="Calibrate",enabled=False)
        # self.calibrate_btn.clicked.connect(self.calibrateScreen)

        self.manufacture_btn = self.get_Button(embedded=self.main_scroll_window,b_x=400,name="Manufacture",name_ptSize=17)
        self.manufacture_btn.clicked.connect(self.buildScreen)

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
        self.mainBuild_scrollArea = self.get_ScrollArea(resizable=False,embedded=self.build_central_widget)

        self.tab_window_gridLayout = QtWidgets.QGridLayout(self.build_central_widget)
        self.four_tab_window = QtWidgets.QTabWidget(self.build_central_widget)

        self.tab_window_gridLayout.addWidget(self.four_tab_window, 0, 0)
        self.tab_window_gridLayout.addWidget(self.mainBuild_scrollArea, 0, 0)
        self.main_central_widget.setLayout(self.tab_window_gridLayout)

        # prep tab
        self.prep_tab = QtWidgets.QWidget()

        self.prep_gridLayout = QtWidgets.QGridLayout()
        self.prep_gridLayout.setSpacing(10)

        self.prep_scrollArea = self.get_ScrollArea()

        #prep btn
        self.file_btn = self.get_Button(b_x=10,b_y=10,length=110,height=75,name="Select File")
        self.file_btn.clicked.connect(self.prep_information)

        self.prep_gridLayout.addWidget(self.file_btn, 0, 0)
        self.prep_gridLayout.addWidget(self.prep_scrollArea, 2, 1, 7, 7)
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

        #scan btn
        self.start_btn_frame = self.create_square_frame()
        self.start_button = self.get_Button(embedded=self.start_btn_frame,b_x=0,b_y=0,length=100,height=100,name="Scan",name_wight=20)
        # self.start_button.clicked.connect(self.start_scan)

        #sort btn
        self.sort_btn_frame = self.create_square_frame()
        self.sort_btn = self.get_Button(embedded=self.sort_btn_frame,b_x=0,b_y=0,length=100,height=100,name="Sort",name_wight=20,enabled=self.sensor_num[0])
        # self.sort_btn.clicked.connect(self.OneWireSort)

        #replace btn
        self.replace_btn_frame = self.create_square_frame()
        self.replace_btn = self.get_Button(enabled=self.replace_btn_frame,b_x=0,b_y=0,length=100,height=100,name="Replace\nSensor\nBoard",name_ptSize=15,name_wight=15)
        # self.replace_btn.clicked.connect(self.boardReplace)

        arrow_frame = QtWidgets.QFrame()
        arrow_grid = QGridLayout()
        arrow_frame.setLayout(arrow_grid)

        left_arrow_icon = QtGui.QIcon()
        left_arrow_icon.addPixmap(QtGui.QPixmap(self.cable_image_list[6]), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        right_arrow_icon = QtGui.QIcon()
        right_arrow_icon.addPixmap(QtGui.QPixmap(self.cable_image_list[7]), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.left_arrow_btn = QtWidgets.QPushButton()
        self.left_arrow_btn.setIcon(left_arrow_icon)
        self.left_arrow_btn.setIconSize(QtCore.QSize(25, 20))
        self.left_arrow_btn.clicked.connect(self.left_check)
        self.left_arrow_btn.setEnabled(False)

        self.right_arrow_btn = QtWidgets.QPushButton()
        self.right_arrow_btn.setIcon(right_arrow_icon)
        self.right_arrow_btn.setIconSize(QtCore.QSize(25, 20))
        self.right_arrow_btn.clicked.connect(self.right_check)
        self.right_arrow_btn.setEnabled(False)

        arrow_grid.addWidget(self.left_arrow_btn, 0, 0)
        arrow_grid.addWidget(self.right_arrow_btn, 0, 1)

        self.scan_gridLayout.addWidget(self.start_btn_frame, 0, 0, 2, 2)
        self.scan_gridLayout.addWidget(self.sort_btn_frame, 2, 0, 2, 2)
        self.scan_gridLayout.addWidget(self.replace_btn_frame, 4, 0, 2, 2)
        self.scan_gridLayout.addWidget(self.current_pcba, 0, 6)
        self.scan_gridLayout.addWidget(self.dtc_serial_lbl, 0, 10)
        self.scan_gridLayout.addWidget(arrow_frame, 6, 0)

        self.scan_tab.setLayout(self.scan_gridLayout)

        # build tab
        self.build_tab = QtWidgets.QWidget()
        self.build_tab.setEnabled(False)
        self.build_gridLayout = QtWidgets.QGridLayout()

        self.build_scrollArea = self.get_ScrollArea()

        self.powered_test_btn_frame = self.create_square_frame()
        self.powered_test_btn = self.get_Button(embedded=self.powered_test_btn_frame,b_x=0,b_y=0,length=100,height=100,name="Test\nCable",name_ptSize=15,name_wight=15)
        self.powered_test_btn.clicked.connect(self.para_pwr_test)

        self.build_error_box = self.get_err_display_box()
        self.build_error_box[0].setVisible(False)

        self.build_dtc_serial_lbl = QtWidgets.QLabel()
        self.build_dtc_serial_lbl.setFont(self.font(20, 20, True))

        progressBar_frame = self.create_square_frame()
        self.progress_bar = self.create_progress_bar(progressBar_frame, 160)
        self.progress_bar_counter = 0

        self.build_gridLayout.addWidget(self.powered_test_btn_frame, 0, 0, 2, 2)
        self.build_gridLayout.addWidget(progressBar_frame, 1, 0, 2, 2)
        self.build_gridLayout.addWidget(self.build_dtc_serial_lbl, 0, 10)
        self.build_gridLayout.addWidget(self.build_scrollArea, 1, 1, 11, 11)
        self.build_gridLayout.addWidget(self.build_error_box[0], 12, 1, 2, 11)

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
        #progress Bar
        verify_prog_bar_frame = self.create_square_frame()
        self.verify_button_prog_bar = self.create_progress_bar(verify_prog_bar_frame, 100)

        #cable Verify
        self.cable_verify_btn_frame = self.create_square_frame()
        self.cable_verify_btn = self.get_Button(embedded=self.cable_verify_btn_frame,b_x=0,b_y=0,length=100,height=100,name="Cable\nVerify",name_wight=15,name_ptSize=15)
        self.cable_verify_btn.clicked.connect(self.verify_Cable_Test)

        #EEPROM progbar
        eeprom_prog_bar_frame = self.create_square_frame()
        self.eeprom_prog_bar = self.create_progress_bar(eeprom_prog_bar_frame, 100)

        #eeprom btn
        self.eeprom_btn_frame = self.create_square_frame()
        self.eeprom_btn = self.get_Button(embedded=self.eeprom_btn_frame,b_y=0,b_x=0,length=100,height=100,name="Program\nEEPROM",name_wight=15,name_ptSize=15,enabled=False)
        self.eeprom_btn.clicked.connect(self.eeprom_call)

        #final test prog bar
        final_test_prog_bar_frame = self.create_square_frame()
        self.final_test_prog_bar = self.create_progress_bar(final_test_prog_bar_frame, 200)

        #final test btn
        self.final_test_btn_frame = self.create_square_frame()
        self.final_test_btn = self.get_Button(embedded=self.final_test_btn_frame,b_x=0,b_y=0,height=100,length=100,name="Final Test",name_wight=15,name_ptSize=15,enabled=False)
        self.final_test_btn.clicked.connect(self.csv)

        self.prog_dtc_serial_lbl = QtWidgets.QLabel()
        self.prog_dtc_serial_lbl.setFont(self.font(20, 20, True))

        self.program_gridLayout.addWidget(self.cable_verify_btn_frame, 0, 0, 2, 2)
        self.program_gridLayout.addWidget(verify_prog_bar_frame, 1, 0, 2, 2)
        self.program_gridLayout.addWidget(self.eeprom_btn_frame, 2, 0, 2, 2)
        self.program_gridLayout.addWidget(eeprom_prog_bar_frame, 3, 0, 2, 2)
        self.program_gridLayout.addWidget(self.final_test_btn_frame, 4, 0, 2, 2)
        self.program_gridLayout.addWidget(final_test_prog_bar_frame, 5, 0, 2, 2)
        self.program_gridLayout.addWidget(self.prog_dtc_serial_lbl, 0, 10)
        self.program_gridLayout.addWidget(self.program_scrollArea, 1, 1, 11, 11)
        self.program_gridLayout.addWidget(self.prog_err_box_contents[0], 12, 1, 2, 11)

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
        test_screen = Test_Utility.test_buildScreen(self.main_central_widget,self.sm)
        self.setCentralWidget(test_screen)

    def calScreen(self):
        # calibrate = cal.SomethingForthekids
        pass

    #BuildScreen Button Methods
    #---prep Tab Methods
    def prep_information(self):
        """ Grabs the file path for the Select File"""
        # if self.sm.check_port() is False:
        #     return

        try:
            select_file = QFileDialog.getOpenFileName(self, "open file", "C:/",
                                                      "Excel (*.csv *.xlsx *.tsv)")
            if (select_file[0] is ''):
                return
            else:
                get_directory_tuple = select_file[0].rindex('/')
                self.report_dir = select_file[0][:get_directory_tuple]
                # self.final_path_lbl.setText(self.report_dir)

                file = open(select_file[0], "r")

            self.file_contents = []

            for x in file:
                self.file_contents.append(x)
            file_desc = list()

            if "Sort" in self.file_contents[0]:
                self.continuation_flag = True
                self.cont = self.continuation_of_previously_scanned()
                file_desc = self.cont.get_description_contents()
            else:
                # this loop splits info into individual list
                for descript_cont in range(1, 7):
                    file_desc.append(self.file_contents[descript_cont].split(","))

            # top labels for each page
            self.dtc_serial_lbl.setText("Serial: DTC" + file_desc[0][1])
            self.build_dtc_serial_lbl.setText("Serial: DTC" + file_desc[1][1])
            self.prog_dtc_serial_lbl.setText("Serial: DTC" + file_desc[1][1])
            self.meta_data_serial = file_desc[0][1]

            if self.continuation_flag:
                self.file_specs = self.cont.get_file_specifications()

            else:
                for content in range(7, len(self.file_contents)):
                    self.file_specs.append(self.file_contents[content].split(","))

            if self.has_protection_board():
                self.sensor_num[1] = int(file_desc[2][1]) - 1
            else:
                self.sensor_num[1] = int(file_desc[2][1])
            # protection/sensor information
            board_option = self.file_specs[3][0].split("/")

            protection_sensor_text = self.file_specs[3][0][-1] + " " + board_option[0] + " & " + str(
                self.sensor_num[1]) + " Sensor Boards "
            pcba_scan_display = QLabel(protection_sensor_text)
            pcba_build_display = QLabel(protection_sensor_text)
            pcba_program_display = QLabel(protection_sensor_text)

            pcba_scan_display.setFont(self.font(20, 45, True))
            pcba_build_display.setFont(self.font(20, 15, True))
            pcba_program_display.setFont(self.font(20, 15, 45))

            self.scan_gridLayout.addWidget(pcba_scan_display, 0, 1)
            self.build_gridLayout.addWidget(pcba_build_display, 0, 1)
            self.program_gridLayout.addWidget(pcba_program_display, 0, 1)

            desc_lbl = []
            desc_lbl.append(QLabel(file_desc[0][0]))
            desc_lbl.append(QLabel(file_desc[0][1]))
            desc_lbl.append(QLabel(file_desc[1][0]))
            desc_lbl.append(QLabel(file_desc[1][1]))
            desc_lbl.append(QLabel(file_desc[2][0]))
            desc_lbl.append(QLabel(file_desc[2][1]))
            desc_lbl.append(QLabel(file_desc[3][0]))
            desc_lbl.append(QLabel(file_desc[3][1]))
            desc_lbl.append(QLabel(file_desc[4][0]))
            desc_lbl.append(QLabel(file_desc[4][1]))
            desc_lbl.append(QLabel(file_desc[5][0]))
            desc_lbl.append(QLabel(file_desc[5][1]))

            for num in range(len(desc_lbl)):
                desc_lbl[num].setFont(self.font(15, 20, False))

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
            for lbl in self.file_specs:
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
                    if comp is 33:
                        ran = 1
                    frame_2_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_2_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_2_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_2_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1
                elif comp >= 65 and comp < 97:
                    if comp is 65:
                        ran = 1
                    frame_3_Grid.addWidget(comp_lbl[comp], ran, 0)
                    frame_3_Grid.addWidget(mold_lbl[comp], ran, 2)
                    frame_3_Grid.addWidget(section_lbl[comp], ran, 4)
                    frame_3_Grid.addWidget(cable_lbl[comp], ran, 6)
                    ran += 1
                elif comp >= 97 and comp < 127:
                    if comp is 97:
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
            error = QMessageBox.critical(self, "Erorr", " Incorrect file. Please insert a .csv extension type",
                                         QMessageBox.Ok)

            if error == QMessageBox.Ok:
                # file.close()
                self.prep_information()

    #Utility Functions
    def font(self, ptSize, weigth, bold):
        font = QtGui.QFont()
        font.setFamily("Times New Roman")  # System
        font.setPointSize(ptSize)
        font.setBold(bold)
        font.setWeight(weigth)
        return font

    def get_ScrollArea(self,resizable = True,embedded =None):
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

    def get_Button(self,embedded = None,b_x=895,b_y=400,length=180,height=160,name="Temp",name_ptSize=20,name_wight=75,name_bold=True,enabled=True):
        if embedded == None:
            button = QtWidgets.QPushButton()
        else:
            button = QtWidgets.QPushButton(embedded)

        button.setGeometry(QtCore.QRect(b_x, b_y, length, height))
        button.setText(name)
        button.setFont(self.font(name_ptSize,name_wight, name_bold))
        button.setEnabled(enabled)
        return button

    def create_square_frame(self,x=0, y=0, length=200, height=200):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frame.setGeometry(QtCore.QRect(x, y, height, length))
        return frame

    def create_label(self,embedded = None,has_pixmap = False, txt="", f_size=0, f_weight=0, f_bold=False, g_x=0, g_y=0, g_length=0,
                     g_height=0, pixmap="", scale_content=False):
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

    def create_progress_bar(self, frame, maximum):
        prog_bar = QtWidgets.QProgressBar(frame)
        prog_bar.setGeometry(0, 40, 100, 20)
        prog_bar.setMinimum(0)
        prog_bar.setMaximum(maximum)
        return prog_bar

    #file setting Modules
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
        if self.path_check is True:
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
        meta_dir = QFileDialog.getOpenFileName(self,caption= "MetaData: choose save location.",directory=self.directory_path,filter= "text(*.txt)")
        self.file_dict[1] = meta_dir[0]

        if meta_dir[0] == "":
            return

        self.meta_data_path_lbl.setText(meta_dir[0])

    def sensor_report_loc(self):
        sensor_dir = QFileDialog.getOpenFileName(self, caption = "Sensor Positions: choose save location.",directory = self.directory_path,filter= "text(*.txt)")
        self.file_dict[2] = sensor_dir[0]
        if sensor_dir[0] == "":
            return

        self.sensor_path_lbl.setText(sensor_dir[0])

    def collect_all(self):
        '''function automates the file browser to pop up consecutively until they cancel or select the files they need.'''
        if self.file_dict is None:
            self.file_dict = dict()
        else:
            self.file_dict.clear()
        cancel_flag = True

        while cancel_flag:
            configuration_file = QFileDialog.getOpenFileName(self, caption="Configuration file: choose save location.",directory="C:/",filter= "text(*.txt)")#create a default directory to the previous one
            cal_file_is_canceled = self.check_if_canceled(configuration_file)
            if cal_file_is_canceled:
                break
            else:
                self.find_directory(configuration_file[0])
                self.file_dict[0] = configuration_file[0]
                self.configuration_path_lbl.setText(configuration_file[0])

            meta_file = QFileDialog.getOpenFileName(self, caption = "MetaData: choose save location.",directory=self.directory_path,filter= "text(*.txt)")#make the default directory in this one the previously selected.
            meta_is_canceled = self.check_if_canceled(meta_file)
            if meta_is_canceled:
                break
            else:
                self.file_dict[1] = meta_file[0]
                self.meta_data_path_lbl.setText(meta_file[0])

            sensor_file = QFileDialog.getOpenFileName(self,caption = "Sensor Positions: choose save location.",directory=self.directory_path,filter = "text(*.txt)")
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

    #port configuration Modules
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

def showscreen():
    app = QApplication([])
    app.setStyle("fusion")
    window = Main_Utility()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    showscreen()