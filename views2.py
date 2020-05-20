import os
import re
import random as rand
import QuickSort as quick
# import wizard
# import serialmanager
# import model
# import report
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import QEvent, QInputEvent, QKeyEvent, Qt

# import QGraphicsSceneMouseEvent as mB
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QLabel,
    QLineEdit, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
    QMessageBox, QAction, QActionGroup, QFileDialog, QDialog, QMenu, QTextEdit
)

from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QSettings, Qt, QThread

VERSION_NUM = "1.1.4"

WINDOW_WIDTH = 1550
WINDOW_HEIGHT = 900

ABOUT_TEXT = f"""
             PCB assembly test utility. Copyright Beaded Streams, 2019.
             v{VERSION_NUM}
             """


class InvalidMsgType(Exception):
    pass


class MainUtility(QMainWindow):

    def __init__(self):
        super().__init__()

        self.system_font = QApplication.font().family()
        self.label_font = QFont(self.system_font, 12)
        self.config_font = QFont(self.system_font, 12)
        self.config_path_font = QFont(self.system_font, 12)

        self.settings = QSettings()  # to be developed later

        self.config = QAction("Settings", self)
        self.config.setShortcut("Ctrl+E")
        self.config.setStatusTip("Program Settings")
        # self.config.triggered.connect()#(put method)

        self.quit = QAction("Quit", self)
        self.quit.setShortcut("Ctrl+Q")
        self.quit.setStatusTip("Exit Program")
        self.quit.triggered.connect(self.close)

        self.about_tu = QAction("About PCBA Test Utility", self)
        self.about_tu.setShortcut("Ctrl+U")
        self.about_tu.setStatusTip("About Program")
        # self.about_tu.triggered.connect(self.about_program)

        self.aboutqt = QAction("About Qt", self)
        self.aboutqt.setShortcut("Ctrl+I")
        self.aboutqt.setStatusTip("About Qt")
        # self.aboutqt.triggered.connect(self.about_qt)

        # Create menubar
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.config)
        self.file_menu.addAction(self.quit)

        self.serial_menu = self.menubar.addMenu("&Serial")
        self.serial_menu.installEventFilter(self)
        self.ports_menu = QMenu("&Ports", self)
        self.serial_menu.addMenu(self.ports_menu)
        # self.ports_menu.aboutToShow.connect(self.populate_ports)
        self.ports_group = QActionGroup(self)
        # self.ports_group.triggered.connect(self.connect_port)

        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.about_tu)
        self.help_menu.addAction(self.aboutqt)

        self.pcba_imgs = []
        self.pcba_hexDict = {}
        self.pcba_hexList = []
        self.counter = 1
        self.rowCount = 0
        self.colbCount = 0
        self.sensor_num = [False, 0]

        self.pcba_gridlayout = QGridLayout()
        self.pcba_gridlayout.setVerticalSpacing(100)
        self.pcba_gridlayout.setHorizontalSpacing(200)
        self.pcba_gridlayout.setColumnStretch(7,1)
        self.pcba_gridlayout.setRowStretch(22,1)


        self.pcba_groupBox = QGroupBox()
        self.pcba_groupBox.setFlat(True)
        self.pcba_groupBox.setLayout(self.pcba_gridlayout)

        self.initUI()
        # self.center()

    def center(self):
        """Centers the application on the screen the mouse pointer is
                currently on."""
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def resource_path(self, relative_path):
        """Gets the path of the application relative root path to allow us
        to find the logo."""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def initUI(self):
        """"Sets up the main UI."""
        RIGHT_SPACING = 350
        LINE_EDIT_WIDTH = 200

        self.main_central_widget = QWidget()
        # self.main_central_widget.isFullScreen()

        self.gridLayout = QtWidgets.QGridLayout(self.main_central_widget)
        self.gridLayout.setContentsMargins(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.scrollArea = QtWidgets.QScrollArea(self.main_central_widget)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(False)

        self.main_scroll_window = QtWidgets.QWidget()
        self.main_scroll_window.setEnabled(True)
        self.main_scroll_window.setGeometry(QtCore.QRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        self.logo_img = QtWidgets.QLabel(self.main_scroll_window)  # self.main_scroll_window)
        self.logo_img.setGeometry(QtCore.QRect(275, 100, 900, 250))
        self.logo_img.setPixmap(QtGui.QPixmap("h_logo.png"))
        self.logo_img.setScaledContents(True)
        self.logo_img.setObjectName("logo_img")

        self.test_btn = QtWidgets.QPushButton(self.main_scroll_window)  # self.main_scroll_window)
        self.test_btn.setGeometry(QtCore.QRect(895, 400, 180, 160))
        self.test_btn.setText("Test")
        self.test_btn.setFont(self.font(20, 75, True))
        self.test_btn.clicked.connect(self.testScreen)

        self.calibrate_btn = QtWidgets.QPushButton(self.main_scroll_window)  # self.main_scroll_window)
        self.calibrate_btn.setGeometry(QtCore.QRect(655, 400, 180, 160))
        self.calibrate_btn.setText("Calibrated")
        self.calibrate_btn.setFont(self.font(20, 75, True))
        self.calibrate_btn.clicked.connect(self.calibrateScreen)

        self.manufacture_btn = QtWidgets.QPushButton(self.main_scroll_window)  # self.main_scroll_window)
        self.manufacture_btn.setGeometry(QtCore.QRect(400, 400, 180, 160))
        self.manufacture_btn.setText("Manufacture")
        self.manufacture_btn.setFont(self.font(20, 75, True))
        self.manufacture_btn.clicked.connect(self.buildScreen)

        self.scrollArea.setWidget(self.main_scroll_window)
        self.gridLayout.addWidget(self.scrollArea, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setCentralWidget(self.scrollArea)

        # self.central_widget.setLayout(self.gridLayout)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle("BeadedStream Manufacturing App 2")

    def keyPressEvent(self, event):
        print(event.text())
        if event.key() == Qt.Key_Space and self.counter is not self.sensor_num[1]+1:
            self.pcbaImgInfo(self.counter)
            self.counter += 1

    def buildScreen(self):
        self.build_central_widget = QWidget(self.main_central_widget)

        self.mainBuild_scrollArea = QtWidgets.QScrollArea(self.build_central_widget)
        self.mainBuild_scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mainBuild_scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mainBuild_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.mainBuild_scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.mainBuild_scrollArea.setWidgetResizable(False)

        self.tab_window_gridLayout = QtWidgets.QGridLayout(self.build_central_widget)
        self.four_tab_window = QtWidgets.QTabWidget(self.build_central_widget)

        self.tab_window_gridLayout.addWidget(self.four_tab_window, 0, 0)
        self.tab_window_gridLayout.addWidget(self.mainBuild_scrollArea, 0, 0)
        self.main_central_widget.setLayout(self.tab_window_gridLayout)

        # return button
        self.return_btn = QPushButton(self.mainBuild_scrollArea)
        self.return_btn.setGeometry(QtCore.QRect(10, 825, 140, 32))
        self.return_btn.setText("Return")
        self.return_btn.setFont(self.font(20, 75, True))
        self.return_btn.clicked.connect(self.initUI)

        # prep tab
        self.prep_tab = QtWidgets.QWidget()

        self.prep_gridLayout = QtWidgets.QGridLayout()
        self.prep_gridLayout.setSpacing(10)


        self.prep_scrollArea = QtWidgets.QScrollArea()
        self.prep_scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.prep_scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.prep_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.prep_scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.prep_scrollArea.setWidgetResizable(True)



        file_btn = QtWidgets.QPushButton()
        file_btn.setText("Select File")
        file_btn.setGeometry(10, 10, 110, 75)
        file_btn.setFont(self.font(20, 75, True))
        file_btn.clicked.connect(self.prep_information)

        self.prep_gridLayout.addWidget(file_btn, 0, 0)
        self.prep_gridLayout.addWidget(self.prep_scrollArea, 2, 1, 7, 7)
        self.prep_tab.setLayout(self.prep_gridLayout)

        # scan tab window

        self.scan_tab = QtWidgets.QWidget()

        self.scan_gridLayout = QtWidgets.QGridLayout()

        self.scan_scrollArea = QtWidgets.QScrollArea()
        self.scan_scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scan_scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scan_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scan_scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scan_scrollArea.setWidgetResizable(True)

        self.scan_gridLayout.addWidget(self.scan_scrollArea, 1, 1, 11, 11)

        self.sort_btn = QPushButton()
        self.sort_btn.setText("Sort")
        self.sort_btn.setGeometry(10, 10, 110, 75)
        self.sort_btn.setEnabled(self.sensor_num[0])
        self.sort_btn.clicked.connect(self.sort)

        self.scan_gridLayout.addWidget(self.sort_btn, 0, 0)
        self.scan_tab.setLayout(self.scan_gridLayout)

        # build tab
        self.build_tab = QtWidgets.QWidget()
        self.buid_gridLayout = self.scan_gridLayout

        self.build_gridLayout = QtWidgets.QGridLayout(self.build_tab)
        self.build_gridLayout.setContentsMargins(0, 0, -1, 0)

        self.build_scrollArea = QtWidgets.QScrollArea(self.build_tab)
        self.build_scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.build_scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.build_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.build_scrollArea.setWidgetResizable(False)

        self.build_scrollAreaWidgetCont = QtWidgets.QWidget()
        self.build_scrollAreaWidgetCont.setGeometry(QtCore.QRect(0, 0, 1518, 900))

        self.build_scrollArea.setWidget(self.build_scrollAreaWidgetCont)
        self.build_gridLayout.addWidget(self.build_scrollArea, 0, 0, 1, 1)

        # inputting of widgets

        self.four_tab_window.addTab(self.prep_tab, "")
        self.four_tab_window.addTab(self.scan_tab, "")
        self.four_tab_window.addTab(self.build_tab, "")

        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.prep_tab), "Prep")
        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.scan_tab), "Scan")
        self.four_tab_window.setTabText(self.four_tab_window.indexOf(self.build_tab), "Build")

        self.setCentralWidget(self.build_central_widget)

    def calibrateScreen(self):
        central_widget = QWidget()

    def testScreen(self):
        central_widget = QWidget()

    def scan_images(self):
        pass

    def prep_information(self):
        """ Grabs the file path for the Select File"""
        select_file = QFileDialog.getOpenFileName(self, "open file", "C:/",
                                                  "Excel (*.csv *.xlsx *.tsv);;PDF(*.pdf);;text(*.txt);;html(*.html)")
        if (select_file[0] is ''):
            return
        else:
            file = open(select_file[0], "r")

        file_contents = []

        for x in file:
            file_contents.append(x)

        # this loop splits info into individual list
        file_desc = []
        for descript_cont in range(1, 7):
            file_desc.append(file_contents[descript_cont].split(","))

        file_specs = []
        for content in range(7, len(file_contents)):
            file_specs.append(file_contents[content].split(","))

        self.sensor_num[1] = (int(file_desc[2][1]))

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



        desc_lbl[0].setFont(self.font(12, 20, True))
        desc_lbl[2].setFont(self.font(12, 20, True))
        desc_lbl[4].setFont(self.font(12, 20, True))
        desc_lbl[6].setFont(self.font(12, 20, True))
        desc_lbl[8].setFont(self.font(12, 20, True))
        desc_lbl[10].setFont(self.font(12, 20, True))
        desc_lbl[11].setTextFormat(Qt.AutoText)

        comp_lbl = []
        mold_lbl = []
        section_lbl = []
        cable_lbl = []
        addi = 0
        # this for loop makes a label list based on the previous file_spec info
        for lbl in file_specs:
            comp_lbl.append(QLabel(file_specs[addi][0]))
            mold_lbl.append(QLabel(file_specs[addi][1]))
            section_lbl.append(QLabel(file_specs[addi][2]))
            cable_lbl.append(QLabel(file_specs[addi][3]))
            addi += 1

        comp_lbl[0].setFont(self.font(20, 20, True))
        mold_lbl[0].setFont(self.font(20, 20, True))
        section_lbl[0].setFont(self.font(20, 20, True))
        cable_lbl[0].setFont(self.font(20, 20, True))

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


        frame_2_Grid.setRowStretch(35, 1)
        frame_3_Grid.setRowStretch(35, 1)
        frame_4_Grid.setRowStretch(35, 1)

        self.frame_1.setLayout(frame_1_Grid)
        self.frame_2.setLayout(frame_2_Grid)
        self.frame_3.setLayout(frame_3_Grid)
        self.frame_4.setLayout(frame_4_Grid)

        frame_grid.addWidget(self.frame_1,0,0)
        frame_grid.addWidget(self.frame_2,0,2)
        frame_grid.addWidget(self.frame_3,0,4)
        frame_grid.addWidget(self.frame_4,0,6)


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


        desc_group =QGroupBox()
        desc_group.setLayout(desc_layout)

        #content
        detail_layout = QGridLayout()
        ran = 1
        for comp in range(1,len(comp_lbl)):
            if comp < 29:
                frame_1_Grid.addWidget(comp_lbl[comp], ran, 0)
                frame_1_Grid.addWidget(mold_lbl[comp], ran, 2)
                frame_1_Grid.addWidget(section_lbl[comp], ran, 4)
                frame_1_Grid.addWidget(cable_lbl[comp], ran, 6)
                ran += 1
            elif comp >=29 and comp < 62:
                if comp is 29:
                    ran = 1
                frame_2_Grid.addWidget(comp_lbl[comp], ran, 0)
                frame_2_Grid.addWidget(mold_lbl[comp], ran, 2)
                frame_2_Grid.addWidget(section_lbl[comp], ran, 4)
                frame_2_Grid.addWidget(cable_lbl[comp], ran, 6)
                ran += 1
            elif comp >= 62 and comp < 95:
                if comp is 62:
                    ran = 1
                frame_3_Grid.addWidget(comp_lbl[comp], ran, 0)
                frame_3_Grid.addWidget(mold_lbl[comp], ran, 2)
                frame_3_Grid.addWidget(section_lbl[comp], ran, 4)
                frame_3_Grid.addWidget(cable_lbl[comp], ran, 6)
                ran += 1
            elif comp >= 95 and comp < 128:
                if comp is 95:
                    ran = 1
                frame_4_Grid.addWidget(comp_lbl[comp], ran, 0)
                frame_4_Grid.addWidget(mold_lbl[comp], ran, 2)
                frame_4_Grid.addWidget(section_lbl[comp], ran, 4)
                frame_4_Grid.addWidget(cable_lbl[comp], ran, 6)
                ran += 1


        self.prep_gridLayout.addWidget(desc_group,1,1)
        self.prep_scrollArea.setWidget(self.frame_group)

        file.close()

    def grid(self,frame,boxNum):

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
        #frame_grid.setRowStretch(40,1)


        if boxNum is 1:
            line = QtWidgets.QFrame(frame)
            line.setWindowModality(QtCore.Qt.NonModal)
            line.setGeometry(QtCore.QRect(-7, 0, 10, 1250))
            line.setFrameShadow(QtWidgets.QFrame.Plain)
            line.setLineWidth(5)
            line.setFrameShape(QtWidgets.QFrame.VLine)

        return frame_grid

    def font(self, ptSize, weigth, bold):
        font = QtGui.QFont()
        font.setFamily("System")
        font.setPointSize(ptSize)
        font.setBold(bold)
        font.setWeight(weigth)
        return font

    def pcbaImgInfo(self, num):

        pcba_frame =QtWidgets.QFrame()
        pcba_frame.setGeometry(QtCore.QRect(160, 70, 211, 131))
        pcba_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        pcba_frame.setFrameShadow(QtWidgets.QFrame.Plain)
        pcba_frame.setLineWidth(46)

        pcba_image_lbl = QtWidgets.QLabel(pcba_frame)
        pcba_image_lbl.setGeometry(QtCore.QRect(0, 30, 125, 45))
        pcba_image_lbl.setPixmap(QtGui.QPixmap("Sensor_PCBA.jpg"))
        pcba_image_lbl.setScaledContents(True)

        hex_number_lbl = QtWidgets.QLabel(pcba_frame)
        hex_number_lbl.setGeometry(QtCore.QRect(0, 77, 160, 16))
        hex_number_lbl.setFont(self.font(18, 18, True))
        random_hex = rand.randint(0000000000000000, 9999999999999999)
        self.pcba_hexList.append(random_hex)
        self.pcba_hexDict[random_hex] = self.counter
        hex_number = str(hex(random_hex))
        hex_number = hex_number[2:]
        hex_number_lbl.setText(hex_number)

        pcba_right_topCorner_id_lbl = QtWidgets.QLabel(pcba_frame)
        pcba_right_topCorner_id_lbl.setGeometry(QtCore.QRect(0, 10, 45, 16))
        pcba_right_topCorner_id_lbl.setFont(self.font(12, 75, True))
        pcba_right_topCorner_id_lbl.setText("A" + str(num))

        self.pcba_orderNum = QLabel(pcba_frame)
        self.pcba_orderNum.setGeometry(QtCore.QRect(109,10,50,20))
        self.pcba_orderNum.setFont(self.font(9,10,True))

        self.pcba_imgs.append(self.pcba_orderNum)

        self.pcba_print(pcba_frame,self.counter-1)


    def pcba_print(self, box, increment):

        if increment is self.sensor_num[1]-1:
            self.sensor_num[0] = True
            self.sort_btn.setEnabled(self.sensor_num[0])

        if (increment % 6) is 0:
            self.colbCount = 0
            self.rowCount += 1
        self.pcba_gridlayout.addWidget(box, self.rowCount, self.colbCount, 3, 2)
        self.colbCount += 1

        self.scan_scrollArea.setWidget(self.pcba_groupBox)

    def sort(self):
        temp = self.pcba_hexList
        self.QuickSort(temp, 0, len(temp) - 1)
        count = 0
        for hex in temp:
            for index in range(len(temp)):
                if self.pcba_hexList[index] is hex:
                    self.pcba_hexDict[hex] = index

        for add in self.pcba_hexDict:
            self.pcba_hexDict[add] = (self.pcba_hexDict.get(add) + 1)

        for hexNum in self.pcba_hexDict:
            self.pcba_imgs[count].setText(str(self.pcba_hexDict.get(hexNum)))
            count += 1

    def Partition(self, A, p, r):
        x = A[r]
        i = (p - 1)
        j = p
        for run in range(j, r):
            if (A[j] <= x):
                i = i + 1
                A[i], A[j] = A[j], A[i]
            j = j + 1
        A[i + 1], A[r] = A[r], A[i + 1]
        return (i + 1)

    def QuickSort(self, A, p, r):
        if (p < r):
            q = self.Partition(A, p, r)
            self.QuickSort(A, p, q - 1)
            self.QuickSort(A, q + 1, r)


def showscreen():
    app = QApplication([])
    app.setStyle("fusion")
    window = MainUtility()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    showscreen()
