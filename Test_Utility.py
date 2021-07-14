from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QLabel,
    QGridLayout, QGroupBox, QHBoxLayout, QProgressBar, QCheckBox,
    QMessageBox, QAction, QActionGroup, QFileDialog, QDialog, QMenu,
    QButtonGroup
)

class test_buildScreen(QMainWindow):#might just need to be empty.
    def __init__(self, Main_Page_Widget,factory_serial):
        super().__init__()

        self.progress_bar_counter = 0

        self.test_central_widget = QWidget(Main_Page_Widget)

        self.sm = factory_serial

        self.mainTest_scrollArea = self.get_ScrollArea(resizable=False,embedded=self.test_central_widget)

        self.tab_window_gridLayout = QtWidgets.QGridLayout(self.test_central_widget)
        self.tab_window = QtWidgets.QTabWidget(self.test_central_widget)

        self.tab_window_gridLayout.addWidget(self.tab_window, 0, 0)
        self.tab_window_gridLayout.addWidget(self.mainTest_scrollArea, 0, 0)
        Main_Page_Widget.setLayout(self.tab_window_gridLayout)

        #test tab
        self.test_tab = QtWidgets.QWidget()

        self.test_gridLayout = QtWidgets.QGridLayout()
        self.test_gridLayout.setVerticalSpacing(0)

        self.test_scrollArea = self.get_ScrollArea()

        cable_data_frame = self.create_square_frame(length=200,height=200)
        self.get_all_cable_data_btn = self.get_Button(embedded=cable_data_frame,b_y=0,b_x=0,length=110,height=35,name="Get All Cable Data",name_ptSize=10,name_wight=10,name_bold=False)
        self.get_all_cable_data_btn.clicked.connect(self.get_all_cable_data)

        self.config_prog_bar = self.create_progress_bar(cable_data_frame,100,length=110)

        strong_pu_frame = QtWidgets.QFrame()
        strong_pu_frame.setFrameStyle(2)
        strong_pu_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        strong_pu_frame.setAutoFillBackground(True)
        strong_pu_lbl = QtWidgets.QLabel(strong_pu_frame)
        strong_pu_lbl.setText("Turn on\n Strong\n pull up?")
        strong_pu_lbl.setFont(self.font(10,10,True))

        temps_frame = self.create_square_frame(length=200,height=200)
        self.temps_btn = self.get_Button(temps_frame,0,0,100,35,"Temps",10,10)
        self.temps_btn.clicked.connect(self.get_temperature_data)

        self.temps_prog_bar = self.create_progress_bar(temps_frame, 100)


        self.strong_pu_checkbox_group = QtWidgets.QButtonGroup()
        self.strong_pu_checkbox_group.setExclusive(True)
        strong_pu_ON_check_box = QtWidgets.QCheckBox("ON", strong_pu_frame)
        strong_pu_OFF_check_box = QtWidgets.QCheckBox("OFF", strong_pu_frame)
        strong_pu_OFF_check_box.toggle()
        strong_pu_ON_check_box.setFont(self.font(10, 10, True))
        strong_pu_OFF_check_box.setFont(self.font(10, 10, True))
        strong_pu_ON_check_box.move(70, 0)
        strong_pu_OFF_check_box.move(70, 30)
        self.strong_pu_checkbox_group.addButton(strong_pu_ON_check_box,1)
        self.strong_pu_checkbox_group.addButton(strong_pu_OFF_check_box,2)
        self.strong_pu_checkbox_group.buttonClicked[int].connect(self.strong_pu_toggle)

        cal_data_frame = self.create_square_frame(length=200,height=200)
        self.get_cal_data = self.get_Button(cal_data_frame,0,0,110,35,"Get Cal Data",10,10,)

        self.get_cal_data_progress_bar = self.create_progress_bar(cal_data_frame,100,length=110)
        # self.get_cal_data.clicked.connect(self.get_temperature_data)

        self.test_gridLayout.addWidget(cable_data_frame, 0, 0, 1, 1)
        self.test_gridLayout.addWidget(temps_frame, 1, 0)
        self.test_gridLayout.addWidget(strong_pu_frame, 2, 0)
        self.test_gridLayout.addWidget(cal_data_frame, 3, 0)

        self.test_gridLayout.addWidget(self.test_scrollArea, 0, 2, 11, 11)
        self.test_tab.setLayout(self.test_gridLayout)

        self.tab_window.addTab(self.test_tab,"Test")
        self.setCentralWidget(self.test_central_widget)

    def get_all_cable_data(self):
        self.clean_scrollArea()
        self.update_progress_bar(reset=True,progress_bar=self.config_prog_bar)
        self.update_progress_bar(amount = 10,progress_bar=self.config_prog_bar)
        configuration_info = self.sm.get_config_call()
        self.update_progress_bar(amount = 50,progress_bar=self.config_prog_bar)
        temps_info = self.sm.get_temps_call()
        self.update_progress_bar(amount = 20,progress_bar=self.config_prog_bar)
        #shove things to the scrollArea
        if configuration_info is None and temps_info is None:
            self.update_progress_bar(set_final_value_max=True,total_amount=100,progress_bar=self.config_prog_bar)
            return

        frame = QtWidgets.QFrame()
        grid = QtWidgets.QGridLayout()
        frame.setLayout(grid)
        self.update_progress_bar(amount = 10,progress_bar=self.config_prog_bar)
        config_lbl = QtWidgets.QLabel()
        temps_lbl = QtWidgets.QLabel()

        grid.addWidget(config_lbl,0,0)
        grid.addWidget(temps_lbl,0,3)

        config_lbl.setText(configuration_info)
        temps_lbl.setText(temps_info)

        config_lbl.setFont(self.font(10,10,True))
        temps_lbl.setFont(self.font(10,10,True))
        self.update_progress_bar(amount = 10,progress_bar=self.config_prog_bar)
        self.test_scrollArea.setWidget(frame)

    def strong_pu_toggle(self,id):
        if self.strong_pu_checkbox_group.button(id) is self.strong_pu_checkbox_group.button(2):
            self.deactivate_strong_pull()
        elif self.strong_pu_checkbox_group.button(id) is self.strong_pu_checkbox_group.button(1):
            self.activate_strong_pull()

    def activate_strong_pull(self):
        self.sm.config_strong_pull_setting(True)

    def deactivate_strong_pull(self):
        self.sm.config_strong_pull_setting()

    def font(self, ptSize, weigth, bold):
        font = QtGui.QFont()
        font.setFamily("System")
        font.setPointSize(ptSize)
        font.setBold(bold)
        font.setWeight(weigth)
        return font

    def get_temperature_data(self):
        self.clean_scrollArea()
        self.update_progress_bar(reset=True,progress_bar=self.temps_prog_bar)
        self.update_progress_bar(amount = 20,progress_bar=self.temps_prog_bar)
        temp_info = self.sm.get_temps_call()
        self.update_progress_bar(amount=50,progress_bar=self.temps_prog_bar)
        if temp_info is None:
            self.update_progress_bar(set_final_value_max=True,total_amount=100,progress_bar=self.temps_prog_bar)
            return
        self.update_progress_bar(amount=20,progress_bar=self.temps_prog_bar)
        frame = QtWidgets.QFrame()
        temp_lbl = QtWidgets.QLabel(frame)
        temp_lbl.setText(temp_info)
        temp_lbl.setFont(self.font(20,20,True))

        self.update_progress_bar(amount=10,progress_bar=self.temps_prog_bar)
        self.test_scrollArea.setWidget(frame)

    def create_progress_bar(self,frame,maximum,length =100,height = 20):
        prog_bar = QtWidgets.QProgressBar(frame)
        prog_bar.setGeometry(0,40,length,height)
        prog_bar.setMinimum(0)
        prog_bar.setMaximum(maximum)
        return prog_bar

    def create_square_frame(self, x=0, y=0, length=200, height=200):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frame.setGeometry(QtCore.QRect(x, y, height, length))
        return frame

    def update_progress_bar(self,amount = 0,progress_bar = None,reset = False,set_final_value_max =False,total_amount =0):
        if reset is True:
            self.progress_bar_counter =0
            progress_bar.setValue(0)
        elif set_final_value_max:
            progress_bar.setValue(total_amount)
        else:
            self.progress_bar_counter += amount
            progress_bar.setValue(self.progress_bar_counter)

    #helper Functions
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


    def clean_scrollArea(self):
        empty_frame = QtWidgets.QFrame()
        empty_lbl = QtWidgets.QLabel(empty_frame)
        empty_lbl.setText("")
        self.test_scrollArea.setWidget(empty_frame)