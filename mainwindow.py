# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import time
import fabio
import numpy as np
import pyFAI
import tifffile
import tomli
import tomli_w
from time import perf_counter
import gc
#import traceback
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.colors import SymLogNorm
from pyFAI import azimuthalIntegrator
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QInputDialog, QMainWindow, QMenu, QWidget, QProgressDialog
#from PyQt5.QtCore import pyqtSlot

from utils import (
    AngleAnnotation,
    append_name,
    combine_masks,
    Data_1d,
    Data_1d_az,
    Data_2d,
    Data_2d_az,
    Data_2d_rot,
    export_data,
    import_data,
    integrate_data,
    make_reject_mask,
    make_saturated_mask,
    mask_pix_zero,
    remove_outliers,
    subtract_2d,
    subtract_1d,
    Worker
)

class Window(QMainWindow):

    cancel_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        #self.threadpool = QtCore.QThreadPool()
        self.auto_mask_saturated_pixels = False
        self.monitor_002 = False
        self.mask = None
        self.bit_depth = None
        self.ai = None
        self.batch_mode = False
        self.BL23A_mode = True
        self.sample_data = {}
        self.background_data = {}
        self.subtracted_data = {}
        #####################################
        self.setup_ui()
        #####################################
        if self.BL23A_mode:
            self.set_bl23a_mode()
        self.tabWidget.setCurrentIndex(2)
        self.set_enable_data_operations(False)

        if not self.BL23A_mode:
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("Use FIT2d mode?")
            dlg.setText(
                "FIT2d uses flipped images, \
                        select Yes to set FIT2d mode and directly \
                        enter calibration values outputted from FIT2d. \
                        Otherwise select No and input a .poni file."
            )
            dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            dlg.setIcon(QtWidgets.QMessageBox.Question)
            button = dlg.exec()
            if button == QtWidgets.QMessageBox.Yes:
                self.fit2d_mode = True
            else:
                self.fit2d_mode = False

    def setup_ui(self):
        self.setObjectName("MainWindow")
        self.resize(1000, 900)
        self.setMinimumSize(1000, 900)
        #####################################################################
        # not needed on linux etc
        # myappid = u'LFP_reduction'
        # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        #####################################################################
        self.setWindowIcon(QtGui.QIcon("../images/icon.png"))
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralWidget)
        self.grpBx_TM = QtWidgets.QGroupBox(self.centralWidget)
        self.grpBx_TM.setGeometry(QtCore.QRect(20, 20, 541, 71))
        self.grpBx_TM.setMaximumSize(QtCore.QSize(541, 71))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.grpBx_TM.setFont(font)
        self.grpBx_TM.setObjectName("grpBx_TM")
        self.gridLayout_2.addWidget(self.grpBx_TM, 0, 0, 1, 1)
        self.gridLayoutWidget = QtWidgets.QWidget(self.grpBx_TM)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 30, 541, 33))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(6, 0, 6, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_bkg_TM = QtWidgets.QLineEdit(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_bkg_TM.setFont(font)
        self.lineEdit_bkg_TM.setObjectName("lineEdit_bkg_TM")
        self.gridLayout.addWidget(self.lineEdit_bkg_TM, 0, 3, 1, 1)
        self.lbl_bkg_TM = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lbl_bkg_TM.setFont(font)
        self.lbl_bkg_TM.setObjectName("lbl_bkg_TM")
        self.gridLayout.addWidget(self.lbl_bkg_TM, 0, 2, 1, 1)
        self.lineEdit_smp_TM = QtWidgets.QLineEdit(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_smp_TM.setFont(font)
        self.lineEdit_smp_TM.setObjectName("lineEdit_smp_TM")
        self.gridLayout.addWidget(self.lineEdit_smp_TM, 0, 1, 1, 1)
        self.lbl_smp_TM = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lbl_smp_TM.setFont(font)
        self.lbl_smp_TM.setObjectName("lbl_smp_TM")
        self.gridLayout.addWidget(self.lbl_smp_TM, 0, 0, 1, 1)

        self.lbl_pbar = QtWidgets.QLabel(self.centralWidget)
        self.lbl_pbar.setFont(font)
        self.lbl_pbar.setObjectName("lbl_pbar")
        self.lbl_pbar.setGeometry(QtCore.QRect(600, 50, 300, 23))
        self.lbl_pbar.setVisible(False)
        self.pbar = QtWidgets.QProgressBar(self.centralWidget)
        self.pbar.setGeometry(QtCore.QRect(600, 70, 300, 23))
        self.pbar.setVisible(False)

        self.groupBox = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox.setGeometry(QtCore.QRect(20, 100, 951, 771))
        self.groupBox.setMinimumSize(QtCore.QSize(951, 771))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2.addWidget(self.groupBox, 1, 0, 1, 1)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.groupBox)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 20, 951, 171))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_2 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        # smaller vertical layout widget
        self.verticalLayoutWidget = QtWidgets.QWidget(self.groupBox_2)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(-1, 19, 311, 141))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setObjectName("verticalLayout")
        # horizontal layout for buttons
        self.horizontal_btn_Layout = QtWidgets.QHBoxLayout()
        self.horizontal_btn_Layout.setObjectName("horizontal_btn_Layout")
        # import button
        self.btn_import_smp = QtWidgets.QPushButton(
            self.verticalLayoutWidget, clicked=lambda: self.click_import_data("smp")
        )
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_smp.setFont(font)
        self.btn_import_smp.setObjectName("btn_import_smp")
        # select all /clear all button
        self.btn_sel_clr_smp = QtWidgets.QPushButton(
            self.verticalLayoutWidget,
            clicked=lambda: self.click_select_deselect_all("smp"),
        )
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_sel_clr_smp.setFont(font)
        self.btn_sel_clr_smp.setObjectName("btn_sel_clr__smp")
        # line edit for sample filter
        self.lineEdit_smp_filter = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.lineEdit_smp_filter.setEnabled(True)
        self.lineEdit_smp_filter.setObjectName("lineEdit")
        # add buttons and lineEdit to horizontal layout
        self.horizontal_btn_Layout.addWidget(self.btn_import_smp)
        self.horizontal_btn_Layout.addWidget(self.btn_sel_clr_smp)
        self.horizontal_btn_Layout.addWidget(self.lineEdit_smp_filter)
        # list widget
        self.listWidget_smp = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.listWidget_smp.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listWidget_smp.setObjectName("listWidget_smp")
        self.verticalLayout.addLayout(self.horizontal_btn_Layout)
        self.verticalLayout.addWidget(self.listWidget_smp)
        self.horizontalLayout.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        # smaller vertical layout widget
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.groupBox_3)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(0, 20, 311, 144))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        # horizona layout for buttons
        self.horizontal_btn_Layout_2 = QtWidgets.QHBoxLayout()
        self.horizontal_btn_Layout_2.setObjectName("horizontal_btn_Layout_2")
        # import button
        self.btn_import_bkg = QtWidgets.QPushButton(
            self.verticalLayoutWidget_2, clicked=lambda: self.click_import_data("bkg")
        )
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_bkg.setFont(font)
        self.btn_import_bkg.setObjectName("btn_import_bkg")
        # select all /clear all button
        self.btn_sel_clr_bkg = QtWidgets.QPushButton(
            self.verticalLayoutWidget,
            clicked=lambda: self.click_select_deselect_all("bkg"),
        )
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_sel_clr_bkg.setFont(font)
        self.btn_sel_clr_bkg.setObjectName("btn_sel_clr__bkg")
        # line edit for sample filter
        self.lineEdit_bkg_filter = QtWidgets.QLineEdit(self.verticalLayoutWidget_2)
        self.lineEdit_bkg_filter.setEnabled(True)
        self.lineEdit_bkg_filter.setObjectName("lineEdit_bkg_filter")
        # add buttons and lineEdit to horizontal layout
        self.horizontal_btn_Layout_2.addWidget(self.btn_import_bkg)
        self.horizontal_btn_Layout_2.addWidget(self.btn_sel_clr_bkg)
        self.horizontal_btn_Layout_2.addWidget(self.lineEdit_bkg_filter)
        # self.verticalLayout_2.addWidget(self.btn_import_bkg)
        # list widget
        self.listWidget_bkg = QtWidgets.QListWidget(self.verticalLayoutWidget_2)
        self.listWidget_bkg.setObjectName("listWidget_bkg")
        self.listWidget_bkg.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # add horizontal layout to vertical layout
        self.verticalLayout_2.addLayout(self.horizontal_btn_Layout_2)
        self.verticalLayout_2.addWidget(self.listWidget_bkg)
        self.horizontalLayout.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_4.setFont(font)
        self.groupBox_4.setObjectName("groupBox_4")
        # smaller vertical layout widget
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.groupBox_4)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(0, 20, 311, 141))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        # horizonal layout for buttons
        self.horizontal_btn_Layout_3 = QtWidgets.QHBoxLayout()
        self.horizontal_btn_Layout.setObjectName("horizontal_btn_Layout_3")
        # import button
        self.btn_import_subd = QtWidgets.QPushButton(
            self.verticalLayoutWidget_3, clicked=lambda: self.click_import_data("sub")
        )
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_subd.setFont(font)
        self.btn_import_subd.setObjectName("btn_import_subd")
        # select all /clear all button
        self.btn_sel_clr_sub = QtWidgets.QPushButton(
            self.verticalLayoutWidget_3,
            clicked=lambda: self.click_select_deselect_all("sub"),
        )
        self.btn_sel_clr_sub.setFont(font)
        self.btn_sel_clr_sub.setObjectName("btn_sel_clr_sub")
        # line edit for subtracted filter
        self.lineEdit_sub_filter = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.lineEdit_sub_filter.setEnabled(True)
        self.lineEdit_sub_filter.setObjectName("lineEdit_sub_filter")
        # add buttons and lineEdit to horizontal layout
        self.horizontal_btn_Layout_3.addWidget(self.btn_import_subd)
        self.horizontal_btn_Layout_3.addWidget(self.btn_sel_clr_sub)
        self.horizontal_btn_Layout_3.addWidget(self.lineEdit_sub_filter)
        # list widget
        self.listWidget_sub = QtWidgets.QListWidget(self.verticalLayoutWidget_3)
        self.listWidget_sub.setObjectName("listWidget_sub")
        self.listWidget_sub.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # add horizontal layout to vertical layout
        self.verticalLayout_3.addLayout(self.horizontal_btn_Layout_3)
        self.verticalLayout_3.addWidget(self.listWidget_sub)
        self.horizontalLayout.addWidget(self.groupBox_4)
        self.tabWidget = QtWidgets.QTabWidget(self.groupBox)
        self.tabWidget.setGeometry(QtCore.QRect(10, 230, 931, 531))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.tabWidget.setFont(font)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.btn_show = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_show_data()
        )
        self.btn_show.setGeometry(QtCore.QRect(356, 190, 101, 25))
        self.btn_show.setObjectName("btn_show")
        self.btn_show.setFont(font)
        self.btn_sum = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_sum_data()
        )
        self.btn_sum.setGeometry(QtCore.QRect(471, 190, 101, 25))
        self.btn_sum.setObjectName("btn_sum")
        self.btn_sum.setFont(font)

        self.btn_average = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_average_data()
        )
        self.btn_average.setGeometry(QtCore.QRect(586, 190, 101, 25))
        self.btn_average.setObjectName("btn_average")
        self.btn_average.setFont(font)

        self.btn_subtract = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_subtract()
        )
        self.btn_subtract.setGeometry(QtCore.QRect(701, 190, 101, 25))
        self.btn_subtract.setObjectName("btn_subtract")
        self.btn_subtract.setFont(font)

        self.btn_batch = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_batch_process()
        )
        self.btn_batch.setGeometry(QtCore.QRect(816, 190, 96, 25))
        self.btn_batch.setObjectName("btn_batch")
        self.btn_batch.setFont(font)

        self.groupBox_5 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_5.setGeometry(QtCore.QRect(739, 0, 181, 161))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_5.setFont(font)
        self.groupBox_5.setObjectName("groupBox_5")
        self.groupBox_rot_img = QtWidgets.QGroupBox(self.tab)
        self.groupBox_rot_img.setGeometry(QtCore.QRect(739, 211, 181, 101))
        self.groupBox_rot_img.setObjectName("groupBox_rot_img")
        self.groupBox_rot_img.setFont(font)
        self.lbl_rot_ang = QtWidgets.QLabel(self.groupBox_rot_img)
        self.lbl_rot_ang.setGeometry(QtCore.QRect(15, 30, 67, 17))
        self.dsb_rot_ang = QtWidgets.QDoubleSpinBox(self.groupBox_rot_img)
        self.dsb_rot_ang.setGeometry(QtCore.QRect(15, 57, 67, 26))
        self.dsb_rot_ang.setMinimum(-360.0)
        self.dsb_rot_ang.setMaximum(360.0)
        self.dsb_rot_ang.setValue(0.0)
        self.btn_rot_img = QtWidgets.QPushButton(
            self.groupBox_rot_img, clicked=lambda: self.click_rot_img()
        )
        self.btn_rot_img.setGeometry(QtCore.QRect(95, 57, 75, 25))
        self.btn_rot_img.setObjectName("btn_rot_img")

        self.label = QtWidgets.QLabel(self.groupBox_5)
        self.label.setGeometry(QtCore.QRect(10, 30, 67, 17))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName("label")
        # self.lineEdit_radius = QtWidgets.QLineEdit(self.groupBox_5)
        # self.lineEdit_radius.setGeometry(QtCore.QRect(10, 50, 113, 25))
        # self.lineEdit_radius.setObjectName("lineEdit_radius")
        self.comboBox_size = QtWidgets.QComboBox(self.groupBox_5)
        self.comboBox_size.setGeometry(QtCore.QRect(10, 50, 113, 25))
        self.comboBox_size.setObjectName("comboBox_size")
        self.comboBox_size.addItem("3")
        self.comboBox_size.addItem("5")
        self.comboBox_size.setCurrentIndex(1)
        self.lineEdit_threshold = QtWidgets.QLineEdit(self.groupBox_5)
        self.lineEdit_threshold.setGeometry(QtCore.QRect(10, 100, 113, 25))
        self.lineEdit_threshold.setObjectName("lineEdit_threshold")
        self.label_2 = QtWidgets.QLabel(self.groupBox_5)
        self.label_2.setGeometry(QtCore.QRect(10, 80, 91, 17))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.btn_remove_outliers = QtWidgets.QPushButton(
            self.groupBox_5, clicked=lambda: self.click_remove_outliers()
        )
        self.btn_remove_outliers.setGeometry(QtCore.QRect(10, 130, 151, 25))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setBold(False)
        font.setWeight(50)
        self.btn_remove_outliers.setFont(font)
        self.btn_remove_outliers.setObjectName("btn_remove_outliers")
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_2d_integrate = QtWidgets.QPushButton(
            self.tab, clicked=lambda: self.click_integrate_2d()
        )
        self.btn_2d_integrate.setGeometry(QtCore.QRect(788, 404, 121, 41))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_2d_integrate.setFont(font)
        self.btn_2d_integrate.setObjectName("btn_2d_integrate")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_settings = QtWidgets.QWidget()
        self.tab_settings.setObjectName("tab_settings")
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab_settings)
        self.groupBox_6.setGeometry(QtCore.QRect(10, 10, 351, 481))
        self.groupBox_6.setObjectName("groupBox_6")
        self.lineEdit_X = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_X.setGeometry(QtCore.QRect(10, 30, 113, 25))
        self.lineEdit_X.setObjectName("lineEdit_X")
        self.lineEdit_Y = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_Y.setGeometry(QtCore.QRect(10, 60, 113, 25))
        self.lineEdit_Y.setObjectName("lineEdit_Y")
        self.lineEdit_SD = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_SD.setGeometry(QtCore.QRect(10, 90, 113, 25))
        self.lineEdit_SD.setObjectName("lineEdit_SD")
        self.lineEdit_wavelength = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_wavelength.setGeometry(QtCore.QRect(10, 120, 113, 25))
        self.lineEdit_wavelength.setObjectName("lineEdit_wavelength")
        self.lineEdit_X_dir = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_X_dir.setGeometry(QtCore.QRect(10, 150, 113, 25))
        self.lineEdit_X_dir.setObjectName("lineEdit_X_dir")
        self.lineEdit_Y_dir = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_Y_dir.setGeometry(QtCore.QRect(10, 180, 113, 25))
        self.lineEdit_Y_dir.setObjectName("lineEdit_Y_dir")
        self.lineEdit_rotAngTiltPlane = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_rotAngTiltPlane.setGeometry(QtCore.QRect(10, 210, 113, 25))
        self.lineEdit_rotAngTiltPlane.setObjectName("lineEdit_rotAngTiltPlane")
        self.lineEdit_angDetTilt = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_angDetTilt.setGeometry(QtCore.QRect(10, 240, 113, 25))
        self.lineEdit_angDetTilt.setObjectName("lineEdit_angDetTilt")
        self.dsb_scale_factor = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.dsb_scale_factor.setGeometry(QtCore.QRect(10, 400, 113, 25))
        self.dsb_scale_factor.setObjectName("dsb_scale_factor")
        self.dsb_scale_factor.setMinimum(0)
        self.dsb_scale_factor.setMaximum(10000000000)
        self.dsb_scale_factor.setDecimals(8)
        self.dsb_scale_factor.setValue(1.0)
        self.dsb_scale_factor.setVisible(False)
        self.label_3 = QtWidgets.QLabel(self.groupBox_6)
        self.label_3.setGeometry(QtCore.QRect(130, 34, 151, 17))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.groupBox_6)
        self.label_4.setGeometry(QtCore.QRect(130, 64, 151, 17))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.groupBox_6)
        self.label_5.setGeometry(QtCore.QRect(130, 94, 121, 17))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.groupBox_6)
        self.label_6.setGeometry(QtCore.QRect(130, 124, 141, 17))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.groupBox_6)
        self.label_7.setGeometry(QtCore.QRect(130, 154, 121, 17))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.groupBox_6)
        self.label_8.setGeometry(QtCore.QRect(130, 184, 121, 17))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.groupBox_6)
        self.label_9.setGeometry(QtCore.QRect(130, 214, 181, 17))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(self.groupBox_6)
        self.label_10.setGeometry(QtCore.QRect(130, 244, 241, 17))
        self.label_10.setObjectName("label_10")
        self.label_11 = QtWidgets.QLabel(self.groupBox_6)
        self.label_11.setGeometry(QtCore.QRect(130, 404, 241, 17))
        self.label_11.setObjectName("label_10")
        self.label_11.setVisible(False)
        self.btn_load_PONI = QtWidgets.QPushButton(
            self.groupBox_6, clicked=lambda: self.click_load_poni()
        )
        self.btn_load_PONI.setGeometry(QtCore.QRect(10, 280, 91, 25))
        self.btn_load_PONI.setObjectName("btn_load_PONI")
        self.btn_save_PONI = QtWidgets.QPushButton(
            self.groupBox_6, clicked=lambda: self.click_save_poni()
        )
        self.btn_save_PONI.setGeometry(QtCore.QRect(110, 280, 89, 25))
        self.btn_save_PONI.setObjectName("btn_save_PONI")
        self.btn_load_PSAXS = QtWidgets.QPushButton(
            self.groupBox_6, clicked=lambda: self.click_load_psaxs()
        )
        self.btn_load_PSAXS.setGeometry(QtCore.QRect(10, 310, 121, 25))
        self.btn_load_PSAXS.setObjectName("btn_load_PSAXS")
        self.btn_load_mask = QtWidgets.QPushButton(
            self.groupBox_6, clicked=lambda: self.click_load_mask()
        )
        self.btn_load_mask.setGeometry(QtCore.QRect(10, 340, 89, 25))
        self.btn_load_mask.setObjectName("btn_load_mask")
        self.btn_load_reject = QtWidgets.QPushButton(
            self.groupBox_6, clicked=lambda: self.click_load_reject()
        )
        self.btn_load_reject.setGeometry(QtCore.QRect(10, 370, 89, 25))
        self.btn_load_reject.setObjectName("btn_load_reject")
        self.cb_002 = QtWidgets.QCheckBox(self.groupBox_6)
        self.cb_002.setGeometry(QtCore.QRect(141, 310, 141, 25))
        self.cb_002.stateChanged.connect(self.check002)
        self.saturated_pix_mask = False
        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.addTab(self.tab_settings, "")
        self.btn_remove = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.remove_selected()
        )
        self.btn_remove.setGeometry(QtCore.QRect(10, 190, 101, 25))
        font = QtGui.QFont()
        font.setStyleName("Microsoft Sans Serif")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_remove.setFont(font)
        self.btn_remove.setObjectName("btn_remove")
        self.btn_export = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_export()
        )
        self.btn_export.setGeometry(QtCore.QRect(125, 190, 101, 25))
        font = QtGui.QFont()
        font.setStyleName("Helvetica")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_export.setFont(font)
        self.btn_export.setObjectName("btn_export")
        self.btn_rename = QtWidgets.QPushButton(
            self.groupBox, clicked=lambda: self.click_rename()
        )
        self.btn_rename.setGeometry(QtCore.QRect(240, 190, 101, 25))
        self.btn_rename.setFont(font)
        self.btn_rename.setObjectName("btn_rename")
        self.groupBox_az_integration = QtWidgets.QGroupBox(self.tab)
        self.groupBox_az_integration.setGeometry(QtCore.QRect(739, 160, 181, 161))
        self.groupBox_az_integration.setObjectName("groupBox_az_integration")
        self.dsb_chi_start = QtWidgets.QDoubleSpinBox(self.groupBox_az_integration)
        self.dsb_chi_start.setGeometry(QtCore.QRect(10, 50, 81, 26))
        self.dsb_chi_start.setMinimum(-180.0)
        self.dsb_chi_start.setMaximum(180.0)
        self.dsb_chi_start.setProperty("value", -180.0)
        self.dsb_chi_start.setObjectName("dsb_chi_start")
        self.dsb_chi_end = QtWidgets.QDoubleSpinBox(self.groupBox_az_integration)
        self.dsb_chi_end.setGeometry(QtCore.QRect(100, 50, 69, 26))
        self.dsb_chi_end.setMinimum(-180.0)
        self.dsb_chi_end.setMaximum(180.0)
        self.dsb_chi_end.setProperty("value", 180.0)
        self.dsb_chi_end.setObjectName("dsb_chi_end")
        self.sb_q_bins = QtWidgets.QSpinBox(self.groupBox_az_integration)
        self.sb_q_bins.setGeometry(QtCore.QRect(50, 100, 71, 26))
        self.sb_q_bins.setMaximum(10000)
        self.sb_q_bins.setProperty("value", 1000)
        self.sb_q_bins.setObjectName("sb_q_bins")
        self.lbl_chi_range = QtWidgets.QLabel(self.groupBox_az_integration)
        self.lbl_chi_range.setGeometry(QtCore.QRect(10, 30, 141, 17))
        self.lbl_chi_range.setObjectName("lbl_chi_range")
        self.lbl_q_bins = QtWidgets.QLabel(self.groupBox_az_integration)
        self.lbl_q_bins.setGeometry(QtCore.QRect(30, 80, 121, 17))
        self.lbl_q_bins.setObjectName("lbl_q_bins")
        self.btn_az_integrate = QtWidgets.QPushButton(
            self.groupBox_az_integration, clicked=lambda: self.click_integrate()
        )
        self.btn_az_integrate.setGeometry(QtCore.QRect(40, 130, 89, 25))
        self.btn_az_integrate.setObjectName("btn_az_integrate")
        self.groupBox_rad_integration = QtWidgets.QGroupBox(self.tab)
        self.groupBox_rad_integration.setGeometry(QtCore.QRect(739, 320, 181, 171))
        self.groupBox_rad_integration.setObjectName("groupBox")
        self.dsb_start_q = QtWidgets.QDoubleSpinBox(self.groupBox_rad_integration)
        self.dsb_start_q.setGeometry(QtCore.QRect(10, 50, 81, 26))
        self.dsb_start_q.setObjectName("dsb_start_q")
        self.dsb_start_q.setProperty("value", 0)
        self.dsb_start_q.setDecimals(6)
        self.lbl_radial_range = QtWidgets.QLabel(self.groupBox_rad_integration)
        self.lbl_radial_range.setGeometry(QtCore.QRect(10, 30, 161, 17))
        self.lbl_radial_range.setObjectName("lbl_radial_range")
        self.dsb_end_q = QtWidgets.QDoubleSpinBox(self.groupBox_rad_integration)
        self.dsb_end_q.setGeometry(QtCore.QRect(100, 50, 81, 26))
        self.dsb_end_q.setObjectName("dsb_end_q")
        self.dsb_end_q.setProperty("value", 20)
        self.dsb_end_q.setDecimals(6)
        self.sb_chi_points = QtWidgets.QSpinBox(self.groupBox_rad_integration)
        self.sb_chi_points.setGeometry(QtCore.QRect(50, 100, 71, 26))
        self.sb_chi_points.setMaximum(10000)
        self.sb_chi_points.setProperty("value", 100)
        self.sb_chi_points.setObjectName("sb_chi_points")
        self.btn_rad_integrate = QtWidgets.QPushButton(
            self.groupBox_rad_integration, clicked=lambda: self.click_integrate_radial()
        )
        self.btn_rad_integrate.setGeometry(QtCore.QRect(40, 130, 89, 25))
        self.btn_rad_integrate.setObjectName("btn_rad_integrate")
        self.lbl_chi_points = QtWidgets.QLabel(self.groupBox_rad_integration)
        self.lbl_chi_points.setGeometry(QtCore.QRect(30, 80, 131, 17))
        self.lbl_chi_points.setObjectName("lbl_chi_points")
        self.layout = QtWidgets.QWidget(self.tab)
        self.layout.setGeometry(QtCore.QRect(0, 0, 730, 490))
        self.layout.setObjectName("layout")
        self.layout = QtWidgets.QVBoxLayout(self.layout)
        self.figure = pyplot.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.tab)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.cid = self.canvas.mpl_connect("button_press_event", self.onclick)
        self.layout2 = QtWidgets.QWidget(self.tab_2)
        self.layout2.setGeometry(QtCore.QRect(0, 0, 730, 490))
        self.layout2.setObjectName("layout2")
        self.layout2 = QtWidgets.QVBoxLayout(self.layout2)
        self.figure2 = pyplot.figure()
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self.tab_2)
        self.layout2.addWidget(self.toolbar2)
        self.layout2.addWidget(self.canvas2)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 22))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        ####################################################
        # flags
        ####################################################
        
        

        
        self.retranslate_ui()
        

        # self.thread_manager = QtCore.QThreadPool()

        
        
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "LFP reduction"))
        self.grpBx_TM.setTitle(_translate("MainWindow", "TM (applied on subtraction)"))
        self.lineEdit_bkg_TM.setText(_translate("MainWindow", "1.0"))
        self.lbl_bkg_TM.setText(_translate("MainWindow", "Background TM:"))
        self.lineEdit_smp_TM.setText(_translate("MainWindow", "1.0"))
        self.lbl_smp_TM.setText(_translate("MainWindow", "Sample TM:"))
        self.groupBox.setTitle(_translate("MainWindow", "WAXS"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Sample"))
        self.btn_import_smp.setText(_translate("MainWindow", "Import"))
        self.btn_sel_clr_smp.setText(_translate("MainWindow", "Select all"))
        self.btn_sel_clr_bkg.setText(_translate("MainWindow", "Select all"))
        self.btn_sel_clr_sub.setText(_translate("MainWindow", "Select all"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Background"))
        self.btn_import_bkg.setText(_translate("MainWindow", "Import"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Subtracted"))
        self.btn_import_subd.setText(_translate("MainWindow", "Import"))
        self.btn_show.setText(_translate("MainWindow", "Show"))
        self.btn_sum.setText(_translate("MainWindow", "Sum"))
        self.btn_average.setText(_translate("MainWindow", "Average"))
        self.btn_subtract.setText(_translate("MainWindow", "Subtract"))
        self.btn_batch.setText(_translate("MainWindow", "Batch proc."))
        self.groupBox_5.setTitle(_translate("MainWindow", "Remove outliers:"))
        self.groupBox_rot_img.setTitle(_translate("MainWindow", "Rotate image:"))
        self.lbl_rot_ang.setText(_translate("MainWindow", "Angle:"))
        self.lbl_pbar.setText(_translate("MainWindow", "Progress:"))
        self.btn_rot_img.setText(_translate("MainWindow", "Apply"))
        self.label.setText(_translate("MainWindow", "Size (pix):"))
        self.lineEdit_threshold.setText(_translate("MainWindow", "50"))
        self.label_2.setText(_translate("MainWindow", "Threshold:"))
        self.btn_remove_outliers.setText(_translate("MainWindow", "Apply to selected"))
        self.btn_2d_integrate.setText(_translate("MainWindow", "2D integrate"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab), _translate("MainWindow", "2D Tools")
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "1D Tools")
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab), _translate("MainWindow", "2D Tools")
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "1D Tools")
        )
        self.groupBox_6.setTitle(
            _translate("MainWindow", "Integration (fit 2D format)  ")
        )
        self.label_3.setText(_translate("MainWindow", "X pix. size [Microns]"))
        self.label_4.setText(_translate("MainWindow", "Y pix. size [Microns]"))
        self.label_5.setText(_translate("MainWindow", "S-D dist. [mm]"))
        self.label_6.setText(_translate("MainWindow", "Wavelength [Ang.]"))
        self.label_7.setText(_translate("MainWindow", "X dir. Beam [Pix.]"))
        self.label_8.setText(_translate("MainWindow", "Y dir. Beam [Pix.]"))
        self.label_9.setText(_translate("MainWindow", "Rot. ang. tilt plane [deg.]"))
        self.label_10.setText(
            _translate("MainWindow", "Ang of det. tilt in plane [deg.]")
        )
        self.label_11.setText(_translate("MainWindow", "Scale factor (1d data)"))
        self.btn_load_PONI.setText(_translate("MainWindow", "Load PONI"))
        self.btn_load_mask.setText(_translate("MainWindow", "Load mask"))
        self.btn_load_reject.setText(_translate("MainWindow", "Load reject"))
        self.btn_save_PONI.setText(_translate("MainWindow", "Save PONI"))
        self.btn_load_PSAXS.setText(_translate("MainWindow", "Load PSAXS.txt"))
        self.cb_002.setText(_translate("MainWindow", "monitor 002.txt"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_settings),
            _translate("MainWindow", "Settings"),
        )
        self.btn_remove.setText(_translate("MainWindow", "Remove"))
        self.btn_export.setText(_translate("MainWindow", "Export"))
        self.btn_rename.setText(_translate("MainWindow", "Rename"))
        self.groupBox_az_integration.setTitle(
            _translate("MainWindow", "Azimuthal int. (I vs q)")
        )
        self.lbl_chi_range.setText(_translate("MainWindow", "chi range (degrees): "))
        self.lbl_q_bins.setText(_translate("MainWindow", "Number of bins: "))
        self.btn_az_integrate.setText(_translate("MainWindow", "Get I vs. q"))
        self.groupBox_rad_integration.setTitle(
            _translate("MainWindow", "Radial int. (I vs chi)  ")
        )
        self.lbl_radial_range.setText(
            _translate("MainWindow", "Radial range (q [A^-1]):  ")
        )
        self.btn_rad_integrate.setText(_translate("MainWindow", "Get I vs. chi"))
        self.lbl_chi_points.setText(_translate("MainWindow", "Number of points: "))

    def set_enable_data_operations(self, state):
        self.tab.setEnabled(state)
        self.tab_2.setEnabled(state)
        self.groupBox_2.setEnabled(state)
        self.groupBox_3.setEnabled(state)
        self.groupBox_4.setEnabled(state)
        self.btn_remove.setEnabled(state)
        self.btn_export.setEnabled(state)
        self.btn_rename.setEnabled(state)
        self.btn_show.setEnabled(state)
        self.btn_sum.setEnabled(state)
        self.btn_average.setEnabled(state)
        self.btn_subtract.setEnabled(state)
        self.btn_batch.setEnabled(state)
        self.btn_load_mask.setEnabled(state)
        self.btn_load_reject.setEnabled(state)
        self.dsb_scale_factor.setEnabled(state)

    def set_bl23a_mode(self):
        self.btn_load_PSAXS.setVisible(True)
        self.fit2d_mode = True
        self.cb_002.setVisible(False)
        self.btn_load_PONI.setText("Load params")
        self.btn_save_PONI.setText("Save params")
        self.btn_2d_integrate.setVisible(False)
        self.btn_load_PSAXS.setVisible(False)
        self.groupBox_rot_img.setVisible(False)

    def check_batch_input(self):
        if len(self.listWidget_bkg.selectedIndexes()) > 1:
            self.show_warning_messagebox(
                "More than one background selected, only one can be \
                    selected to subtract off."
            )
            return False
        
    
    def click_batch_process(self):
        '''
        This does the batch processing of the data.

        '''
        try:
            if self.check_batch_input() is False:
                self.show_warning_messagebox("Batch processing cancelled")
                return
                
            self.batch_smp_1d = []
            self.batch_smp_2d = []
            self.batch_bkg_1d = []
            self.batch_bkg_2d = []
            self.batch_sub_1d = []
            self.batch_sub_2d = []

            
            
            expected_smps = len(self.get_all_selected("smp"))
            expected_bkgs = len(self.get_all_selected("bkg"))
            if expected_smps < 1:
                self.show_warning_messagebox("No samples selected for batch processing")
                return

            self.batch_mode = True
            self.groupBox.setEnabled(False)
            
            QApplication.processEvents()
            self.click_remove_outliers()  # now appends to batch_XXX_2d list
            while self.worker.isRunning():
                QApplication.processEvents()
                time.sleep(0.001)
            
            while (len(self.batch_smp_2d) < expected_smps):
                QApplication.processEvents()
                time.sleep(0.01)

            while (len(self.batch_bkg_2d) < expected_bkgs):
                QApplication.processEvents()
                time.sleep(0.01)

            # clear all list widgets
            self.clear_lists()

            for item in self.batch_smp_2d:
                self.toggle_select_by_string(item, "smp", True)

            for item in self.batch_bkg_2d:
                self.toggle_select_by_string(item, "bkg", True)

            self.click_integrate() 
            while self.worker.isRunning():
                QApplication.processEvents()
                time.sleep(0.01)  

            while len(self.batch_smp_1d) < expected_smps:
                QApplication.processEvents()
                time.sleep(0.01)

            while len(self.batch_bkg_1d) < expected_bkgs:
                QApplication.processEvents()
                time.sleep(0.01)

            self.clear_lists()
            QApplication.processEvents()
            if len(self.batch_bkg_2d) > 0:
                self.toggle_select_by_string(self.batch_bkg_2d[0], "bkg", True)
                for item in self.batch_smp_2d:
                    self.toggle_select_by_string(item, "smp", True)
                # 2D subtraction
                self.click_subtract()
                while self.worker.isRunning():
                    QApplication.processEvents()
                    time.sleep(0.001)
            
                while (len(self.batch_sub_2d) < expected_smps):
                    QApplication.processEvents()
                    time.sleep(0.01)
                    
                self.clear_lists()
                
                if len(self.batch_bkg_1d) > 0:
                    self.toggle_select_by_string(self.batch_bkg_1d[0], "bkg", True)
                else:
                    return
                
                time.sleep(1)
                for item in self.batch_smp_1d:
                    self.toggle_select_by_string(item, "smp", True)
                self.click_subtract()

                while (len(self.batch_sub_1d) < expected_smps):
                    QApplication.processEvents()
                    time.sleep(0.01)
                self.clear_lists()
            
            for item in self.batch_smp_2d:
                self.toggle_select_by_string(item, "smp", True)
            for item in self.batch_smp_1d:
                self.toggle_select_by_string(item, "smp", True)
            for item in self.batch_bkg_2d:
                self.toggle_select_by_string(item, "bkg", True)
            for item in self.batch_bkg_1d:
                self.toggle_select_by_string(item, "bkg", True)
            for item in self.batch_sub_2d:
                self.toggle_select_by_string(item, "sub", True)
            for item in self.batch_sub_1d:
                self.toggle_select_by_string(item, "sub", True)

            self.click_export()
            while self.worker.isRunning():
                QApplication.processEvents()
                time.sleep(0.001)

            self.batch_mode = False
            self.groupBox.setEnabled(True)
            self.clear_lists()

        except Exception as e:
           print(e)
           self.batch_mode = False
           self.groupBox.setEnabled(True)
    
    
    def toggle_select_by_string(self, string, name, state):
        if name == "smp":
            items = [
                self.listWidget_smp.item(x) for x in range(self.listWidget_smp.count())
            ]
            for item in items:
                if string == item.text():
                    item.setSelected(state)
        elif name == "bkg":
            items = [
                self.listWidget_bkg.item(x) for x in range(self.listWidget_bkg.count())
            ]
            for item in items:
                if string == item.text():
                    item.setSelected(state)
        elif name == "sub":
            items = [
                self.listWidget_sub.item(x) for x in range(self.listWidget_sub.count())
            ]
            for item in items:
                if string == item.text():
                    item.setSelected(state)

    def select_by_filter(self, string, name):
        if name == "smp":
            if string == "":
                self.listWidget_smp.selectAll()
                if not self.batch_mode:
                    self.btn_sel_clr_smp.setText("Clear selection")
            else:
                items = [
                    self.listWidget_smp.item(x)
                    for x in range(self.listWidget_smp.count())
                ]
                for item in items:  # range(self.listWidget_smp.count()):
                    if self.str_contains(item.text(), string):
                        item.setSelected(True)
                if not self.batch_mode:
                    self.btn_sel_clr_smp.setText("Clear selection")
        elif name == "bkg":
            if string == "":
                self.listWidget_bkg.selectAll()
                if not self.batch_mode:
                    self.btn_sel_clr_bkg.setText("Clear selection")
            else:
                items = [
                    self.listWidget_bkg.item(x)
                    for x in range(self.listWidget_bkg.count())
                ]
                for item in items:
                    if self.str_contains(item.text(), string):
                        item.setSelected(True)
                if not self.batch_mode:
                    self.btn_sel_clr_bkg.setText("Clear selection")
        elif name == "sub":
            if string == "":
                self.listWidget_sub.selectAll()
                if not self.batch_mode:
                    self.btn_sel_clr_sub.setText("Clear selection")
            else:
                items = [
                    self.listWidget_sub.item(x)
                    for x in range(self.listWidget_sub.count())
                ]
                for item in items:
                    if self.str_contains(item.text(), string):
                        item.setSelected(True)
                if not self.batch_mode:
                    self.btn_sel_clr_sub.setText("Clear selection")

    def deselect_by_filter(self, string, name):
        if name == "smp":
            if string == "":
                self.listWidget_smp.clearSelection()
                self.btn_sel_clr_smp.setText("Select all")
            else:
                items = [
                    self.listWidget_smp.item(x)
                    for x in range(self.listWidget_smp.count())
                ]
                for item in items:  # range(self.listWidget_smp.count()):
                    if self.str_contains(item.text(), string):
                        item.setSelected(False)
                self.btn_sel_clr_smp.setText("Select all")
        elif name == "bkg":
            if string == "":
                self.listWidget_bkg.clearSelection()
                self.btn_sel_clr_bkg.setText("Select all")
            else:
                items = [
                    self.listWidget_bkg.item(x)
                    for x in range(self.listWidget_bkg.count())
                ]
                for item in items:
                    if self.str_contains(item.text(), string):
                        item.setSelected(False)
                self.btn_sel_clr_bkg.setText("Select all")
        elif name == "sub":
            if string == "":
                self.listWidget_sub.clearSelection()
                self.btn_sel_clr_sub.setText("Select all")
            else:
                items = [
                    self.listWidget_sub.item(x)
                    for x in range(self.listWidget_sub.count())
                ]
                for item in items:
                    if self.str_contains(item.text(), string):
                        item.setSelected(False)
            self.btn_sel_clr_sub.setText("Select all")

    def str_contains(self, string, substring):
        if substring in string:
            return True
        else:
            return False

    def click_select_deselect_all(self, name):
        if name == "smp":
            if self.btn_sel_clr_smp.text() == "Select all":
                self.select_by_filter(self.lineEdit_smp_filter.text(), name)
            elif self.btn_sel_clr_smp.text() == "Clear selection":
                self.deselect_by_filter(self.lineEdit_smp_filter.text(), name)
        elif name == "bkg":
            if self.btn_sel_clr_bkg.text() == "Select all":
                self.select_by_filter(self.lineEdit_bkg_filter.text(), name)
            elif self.btn_sel_clr_bkg.text() == "Clear selection":
                self.deselect_by_filter(self.lineEdit_bkg_filter.text(), name)
        elif name == "sub":
            if self.btn_sel_clr_sub.text() == "Select all":
                self.select_by_filter(self.lineEdit_sub_filter.text(), name)
            elif self.btn_sel_clr_sub.text() == "Clear selection":
                self.deselect_by_filter(self.lineEdit_sub_filter.text(), name)

    def click_subtract(self):
        # check that one sample and more than one background is selected
        if len(self.listWidget_smp.selectedIndexes()) < 1:
            self.show_warning_messagebox("No sample selected.", title="Error")
            return

        if len(self.listWidget_bkg.selectedIndexes()) != 1:
            self.show_warning_messagebox("No background selected.", title="Error")
            return

        # if len(self.listWidget_bkg.selectedIndexes()) > 1:
        #     if len(self.listWidget_bkg.selectedIndexes()) != len(
        #         self.listWidget_smp.selectedIndexes()
        #     ):
        #         self.show_warning_messagebox(
        #             "number of selected background and samples different. \
        #                 Returning."
        #         )
        #     return

        # check that all sample and background data sets are 1D or 2D
        is2d = None
        temp = self.listWidget_bkg.selectedIndexes()[0].data()
        if isinstance(self.background_data[temp], Data_2d):
            for item in self.get_all_selected():
                if not isinstance(item, Data_2d):
                    self.show_warning_messagebox("A data set is not 2 dimensional.")
                    return
            is2d = True
        elif isinstance(self.background_data[temp], Data_1d):
            for item in self.get_all_selected():
                if not isinstance(item, Data_1d):
                    self.show_warning_messagebox("A data set is not 1 dimensional.")
                    return
            is1d = True
        else:
            self.show_warning_messagebox("Data is not one or two dimensional.")
        sample_names = self.listWidget_smp.selectedIndexes()
        prog_dialog = QProgressDialog(self)
        prog_dialog.show()
        prog_dialog.autoClose()
        prog_dialog.canceled.connect(self.cancel_process)
        prog_dialog.setWindowTitle("Subtracting data")
        prog_dialog.setLabelText(f"Subtracting {len(sample_names)} files")
        if is2d:
            self.worker = Worker(
                subtract_2d,
                self.listWidget_smp.selectedIndexes(),
                self.sample_data, 
                self.background_data[self.listWidget_bkg.selectedIndexes()[0].data()],
                self.mask, 
                self.dsb_scale_factor.value(), 
                float(self.lineEdit_smp_TM.text().strip()), 
                float(self.lineEdit_bkg_TM.text().strip()),
                self.bit_depth
                )
        elif is1d:
            self.worker = Worker(
            subtract_1d,
            self.listWidget_smp.selectedIndexes(),
            self.sample_data, 
            self.background_data[self.listWidget_bkg.selectedIndexes()[0].data()],
            self.dsb_scale_factor.value(), 
            float(self.lineEdit_smp_TM.text().strip()), 
            float(self.lineEdit_bkg_TM.text().strip()),
            )
        self.worker.start()
        self.worker.export_data_signal.connect(self.append_data)
        if self.batch_mode:
            self.worker.export_data_signal.connect(self.append_batch_mode_lists)
        if not prog_dialog.wasCanceled():
            self.worker.progress_signal.connect(prog_dialog.setValue)
        self.worker.finished.connect(self.worker.deleteLater)

        if not self.batch_mode:
                self.worker.finished.connect(self.clear_lists)

    def get_data_dict(self, data_type):
        if data_type == "smp":
            return self.sample_data
        elif data_type == "bkg":
            return self.background_data
        elif data_type == "sub":
            return self.subtracted_data

    def click_sum_data(self):
        for data_type in ["smp", "bkg", "sub"]:
            all_data = self.get_all_selected(data_type)
            if len(all_data) > 0:
                data_dim = self.check_selected_data_dim(*all_data)
                if data_dim == "two_dim":
                    new_data = Data_2d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name(
                            all_data[0].name + "_sum_" + str(len(all_data)) + "_0",
                            self.get_data_dict(data_type),
                        ),
                        self.sum_2d(all_data),
                        all_data[0].info,
                    )
                    new_data.array = self.check_overflow_pix(
                        new_data.array, new_data.name
                    )
                    self.append_data(new_data)
                elif data_dim == "one_dim":
                    intensity, err = self.sum_1d(all_data)
                    new_data = Data_1d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name(
                            all_data[0].name + "_sum_" + str(len(all_data)) + "_0",
                            self.get_data_dict(data_type),
                        ),
                        all_data[0].q,
                        intensity,
                        err,
                        all_data[0].info,
                    )
                    self.append_data(new_data)
                else:
                    pass

    def click_average_data(self):
        for data_type in ["smp", "bkg", "sub"]:
            all_data = self.get_all_selected(data_type)
            if len(all_data) > 0:
                data_dim = self.check_selected_data_dim(*all_data)
                if data_dim == "two_dim":
                    new_data = Data_2d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name(
                            all_data[0].name + "_avg_" + str(len(all_data)) + "_0",
                            self.get_data_dict(data_type),
                        ),
                        np.divide(self.sum_2d(all_data), len(all_data)),
                        all_data[0].info,
                    )
                    self.append_data(new_data)
                elif data_dim == "one_dim":
                    intensity, err = self.avg_1d(all_data)
                    new_data = Data_1d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name(
                            all_data[0].name + "_avg_" + str(len(all_data)) + "_0",
                            self.get_data_dict(data_type),
                        ),
                        all_data[0].q,
                        np.divide(intensity, len(all_data)),
                        np.divide(err, len(all_data)),
                        all_data[0].info,
                    )
                    self.append_data(new_data)
                else:
                    pass

    def check_selected_data_dim(self, *args):
        data_dim = None
        for x in args:
            if isinstance(x, Data_2d) and (data_dim == "two_dim" or data_dim is None):
                data_dim = "two_dim"
            elif isinstance(x, Data_1d) and (data_dim == "one_dim" or data_dim is None):
                data_dim = "one_dim"
            elif isinstance(x, Data_1d) and data_dim == "two_dim":
                self.show_warning_messagebox("Mixture of 1D and 2D data.")
                return None
            elif isinstance(x, Data_2d) and data_dim == "one_dim":
                self.show_warning_messagebox("Mixture of 1D and 2D data.")
                return None
        return data_dim

    def sum_2d(self, all_data):
        cur_sum = []
        for item in all_data:
            if len(cur_sum) == 0:
                cur_sum = item.array
            else:
                cur_sum = np.add(cur_sum, item.array, dtype="int64")
        return cur_sum

    def avg_1d(self, all_data):
        sum_i = []
        sum_err2 = []
        for item in all_data:
            if len(sum_i) == 0:
                sum_i = item.intensity
                sum_err2 = np.power(item.err, 2)
            else:
                sum_i = np.add(sum_i, item.intensity)
                sum_err2 = np.add(sum_err2, np.power(item.err, 2))
        # check the divide by N or N-1
        return np.divide(sum_i, len(all_data)), np.sqrt(
            np.divide(sum_err2, len(all_data))
        )

    def sum_1d(self, all_data):
        sum_i = []
        sum_err2 = []
        for item in all_data:
            if len(sum_i) == 0:
                sum_i = item.intensity
                sum_err2 = np.power(item.err, 2)
            else:
                sum_i = np.add(sum_i, item.intensity)
                sum_err2 = np.add(sum_err2, np.power(item.err, 2))
        return sum_i, np.sqrt(sum_err2)

    def onclick(self, event):
        """
        This function has significant repeated code, the
        integration functions need to be made modular.
        double result = atan2(P3.y - P1.y, P3.x - P1.x) -
            atan2(P2.y - P1.y, P2.x - P1.x);
        """

        if event.button == 3 and isinstance(self.get_plot_image_data(), Data_2d):
            if self.ai is None:
                self.no_ai_found_error()
                return
            self.ix, self.iy = event.xdata, event.ydata
            q = np.squeeze(self.ai.qFunction(self.iy, self.ix)) / 10
            chi = np.rad2deg(self.ai.chi(self.iy, self.ix))
            p1 = (float(self.lineEdit_X_dir.text()), float(self.lineEdit_Y_dir.text()))
            p3 = (self.ix, self.iy)
            len_p1_p3 = np.sqrt((p1[0] - p3[0]) ** 2 + (p1[1] - p3[1]) ** 2)
            p2 = (p3[0], p3[1] + len_p1_p3)
            # - np.arctan2(p2[1]-p1[1], p2[0] - p1[0])
            # angle = np.arctan2(p3[1] - p1[1], p3[0] - p1[0])
            menu = QMenu()
            menu.addAction(f"q is: {q:.5f} A^-1")
            menu.addAction(f"chi is: {chi:.2f} deg.")
            menu.addSeparator()
            # if not self.BL23A_mode:
            #     set_angle_rot = menu.addAction('Set angle && rotate')
            #     menu.addSeparator()
            set_chi_min = menu.addAction("Set chi min")
            set_chi_max = menu.addAction("Set chi max")
            show_chi = menu.addAction("Show chi")
            menu.addSeparator()
            set_q_min = menu.addAction("Set q min")
            set_q_max = menu.addAction("Set q max")
            menu.addSeparator()
            #azi_integrate = menu.addAction("get I vs Q")
            #rad_integrate = menu.addAction("get I vs chi")
            action = menu.exec_(QtGui.QCursor.pos())

            # if action == set_angle_rot:
            #     self.dsb_rot_ang.setValue(np.rad2deg(angle + np.pi / 2))
            #     self.click_rot_img()
            if action == set_chi_min:
                self.dsb_chi_start.setValue(chi)
                self.p1 = (self.ix, self.iy)
            elif action == set_chi_max:
                self.dsb_chi_end.setValue(chi)
                self.p2 = (self.ix, self.iy)
            elif action == set_q_min:
                self.dsb_start_q.setValue(q)
            elif action == set_q_max:
                self.dsb_end_q.setValue(q)
            elif action == show_chi:
                center = (
                    float(self.lineEdit_X_dir.text()),
                    float(self.lineEdit_Y_dir.text()),
                )
                p1 = [self.p1, center]
                p2 = [self.p2, center]
                (line1,) = self.ax.plot(*zip(*p1), color="lime")
                (line2,) = self.ax.plot(*zip(*p2), color="lime")
                # point, = ax.plot(*center, marker="o")
                AngleAnnotation(
                    center,
                    p1[0],
                    p2[0],
                    text=r"$\chi$",
                    textposition="outside",
                    ax=self.ax,
                    size=75,
                    color="lime",
                    text_kw=dict(color="lime"),
                )
                self.canvas.draw()
            # elif action == azi_integrate:
            #     data = self.get_plot_image_data()
            #     self.figure2.clear()
            #     ax2 = self.figure2.add_subplot(111)
            #     if data.info["type"] == "smp":
            #         norm_value = float(self.lineEdit_smp_TM.text().strip())
            #     elif data.info["type"] == "bkg":
            #         norm_value = float(self.lineEdit_bkg_TM.text().strip())
            #     else:
            #         norm_value = 1

            #     norm_value /= self.dsb_scale_factor.value()
            #     if self.monitor_002:
            #         norm_value *= data.info["civi"]

            #     q, intensity, err = data.integrate_image(
            #         self.ai,
            #         self.sb_q_bins.value(),
            #         self.dsb_chi_start.value(),
            #         self.dsb_chi_end.value(),
            #         self.mask,
            #         norm_value,
            #     )

            #     new_data = Data_1d(
            #         data.dir,
            #         "dat",
            #         "1D~" + data.name.split("~")[1],
            #         q,
            #         intensity,
            #         err,
            #         {"type": data.info["type"]},
            #     )
            #     self.append_data(new_data)
            #     self.plot_1d_1d_data(
            #         ax2,
            #         new_data.q,
            #         new_data.intensity,
            #         new_data.err,
            #         new_data.name.split("~")[1],
            #     )
            #     self.canvas2.draw()
            #     self.tabWidget.setCurrentWidget(self.tab_2)

            # elif action == rad_integrate:
            #     item = self.get_plot_image_data()
            #     self.figure2.clear()
            #     ax2 = self.figure2.add_subplot(111)
            #     chi, intensity = self.integrate_radial(item)
            #     if len(intensity) < 2:
            #         self.show_warning_messagebox(
            #             "Warning, length of data is less than 2!!"
            #         )
            #         return
            #     data = Data_1d_az(
            #         item.dir,
            #         "dat",
            #         "1Daz~" + item.name.split("~")[1],
            #         chi,
            #         intensity,
            #         {"type": item.info["type"]},
            #     )
            #     self.append_data(data)
            #     self.plot_1d_az(ax2, data.chi, data.intensity, data.name.split("~")[1])
            #     self.tabWidget.setCurrentWidget(self.tab_2)

    def no_data_selected(self):
        if (
            not self.listWidget_smp.selectedItems()
            and not self.listWidget_bkg.selectedItems()
            and not self.listWidget_sub.selectedItems()
        ):
            return True

    def click_rot_img(self):
        if self.ai is None:
            self.no_ai_found_error()
        else:
            # data = self.get_first_sel()
            data = self.get_plot_image_data()
            if isinstance(data, Data_2d):
                rotd_img = data.rotate(self.dsb_rot_ang.value())
                name = "2d_rot_" + data.name.split("~")[1]
                self.append_data(
                    Data_2d_rot(data.dir, data.ext, name, rotd_img, data.info)
                )
                self.set_plot_image_name(name, data.info["type"])
                self.plot_2d(rotd_img, name)
                self.clear_lists()

    def click_load_reject(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select reject file", "", " REJECT (REJECT.dat);;All Files (*)"
        )
        if fname and fname != "":
            mask_data = np.loadtxt(fname, usecols=(0, 1), comments="#")
            if self.listWidget_smp.count() < 1:
                self.show_warning_messagebox(
                    "No data loaded, load a sample image file first."
                )
                return
            for index in range(self.listWidget_smp.count()):
                item = self.listWidget_smp.item(index).text()
                data = self.sample_data[item]
                if isinstance(data, Data_2d):
                    if self.mask is None:
                        self.mask = make_reject_mask(
                            np.zeros(np.shape(data.array)), mask_data
                        )
                        return
                    else:
                        self.mask = combine_masks(
                            make_reject_mask(np.zeros(np.shape(data.array)), mask_data),
                            self.mask,
                        )
                        return
            self.show_warning_messagebox(
                "No image files loaded. Load an image file and try again."
            )

    def click_load_mask(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select a mask file",
            "",
            "Fit2d mask (*.msk) ;;tif Image (*.tif);;edf Image \
                (*.edf);;All Files (*)",
        )
        if fname and fname != "":
            self.mask = fabio.open(fname).data
            if fname.endswith(".msk"):
                self.mask = np.flipud(self.mask)
            if self.fit2d_mode:
                self.mask = np.flipud(self.mask)

    # def mask_pix_zero(self, image):
    #     inv_mask = np.abs(1 - self.mask)
    #     masked_image = np.multiply(image, inv_mask)
    #     return masked_image

    def mask_pix_nan(self, image):
        # inv_mask = np.abs(1-self.mask)
        image = image.astype(float)
        image[self.mask == 1] = np.nan
        return image

    def click_load_psaxs(self):
        plank_const = float(4.135667696e-15)
        speed_light = float(299_792_458)

        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select PSAXSpar.txt file", "", "txt (*.txt);;All Files (*)"
        )
        if fname and fname != "":
            fit2d_dic = self.readSAXSpar(fname)

            self.ai = azimuthalIntegrator.AzimuthalIntegrator(
                detector=fit2d_dic["detector"],
                wavelength=plank_const * speed_light / 1000 / fit2d_dic["energy"],
            )
            self.ai.setFit2D(
                fit2d_dic["directBeam"],
                fit2d_dic["beamX"],
                fit2d_dic["beamY"],
                fit2d_dic["tilt"],
                fit2d_dic["tiltPlanRotation"],
            )
            del fit2d_dic
            fit2d_dic = self.ai.getFit2D()

            # fill out line entrys
            self.lineEdit_X.setText(str(fit2d_dic["pixelX"])[0:12])
            self.lineEdit_Y.setText(str(fit2d_dic["pixelY"])[0:12])
            # .text(fit2d_dic["directDist"])
            self.lineEdit_SD.setText(str(fit2d_dic["directDist"])[0:12])
            self.lineEdit_wavelength.setText(
                str(10_000_000_000 * self.ai.get_wavelength())[0:12]
            )
            self.lineEdit_X_dir.setText(str(fit2d_dic["centerX"])[0:12])
            self.lineEdit_Y_dir.setText(str(fit2d_dic["centerY"])[0:12])
            self.lineEdit_rotAngTiltPlane.setText(
                str(fit2d_dic["tiltPlanRotation"])[0:12]
            )
            self.lineEdit_angDetTilt.setText(str(fit2d_dic["tilt"])[0:12])

    def check002(self, checked):
        if checked:
            self.monitor_002 = True
        else:
            self.monitor_002 = False

    def click_rename(self):
        if len(self.listWidget_smp.selectedIndexes()) != 0:
            for item in self.listWidget_smp.selectedItems():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(
                    self,
                    "Rename Dialog",
                    "Change name from " + old_name.split("~")[1] + " to:",
                )
                if ok and new_name != "":
                    split_name = old_name.split("~")[0] + "~" + new_name
                    if split_name in self.sample_data:
                        self.show_warning_messagebox("Name already exists, try again.")
                        return
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.sample_data[old_name].name = new_name
                    self.sample_data[new_name] = self.sample_data[old_name]
                    del self.sample_data[old_name]
                elif new_name == "":
                    self.show_warning_messagebox("Name cannot be empty.")

        if len(self.listWidget_bkg.selectedIndexes()) != 0:
            for item in self.listWidget_bkg.selectedItems():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(
                    self,
                    "Rename Dialog",
                    "Change name from " + old_name.split("~")[1] + " to:",
                )
                if ok and new_name != "":
                    split_name = old_name.split("~")[0] + "~" + new_name
                    if split_name in self.background_data:
                        self.show_warning_messagebox("Name already exists, try again.")
                        return
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.background_data[old_name].name = new_name

                    self.background_data[new_name] = self.background_data[old_name]

                    del self.background_data[old_name]

        if len(self.listWidget_sub.selectedIndexes()) != 0:
            for item in self.listWidget_sub.selectedItems():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(
                    self,
                    "Rename Dialog",
                    "Change name from " + old_name.split("~")[1] + " to:",
                )
                if ok and new_name != "":
                    split_name = old_name.split("~")[0] + "~" + new_name
                    if split_name in self.subtracted_data:
                        self.show_warning_messagebox("Name already exists, try again.")
                        return
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.subtracted_data[old_name].name = new_name
                    self.subtracted_data[new_name] = self.subtracted_data[old_name]
                    del self.subtracted_data[old_name]
        self.clear_lists()

    def click_integrate_radial(self):
        del self.ai
        _ = self.get_ai()
        if self.ai is None:
            self.no_ai_found_error()
        else:
            self.figure2.clear()
            ax2 = self.figure2.add_subplot(111)
            for item in self.get_all_selected():
                if isinstance(item, Data_2d):
                    chi, intensity = self.integrate_radial(item)
                    if len(intensity) < 2:
                        self.show_warning_messagebox(
                            "Warning, length of data is less than 2!!"
                        )
                        return
                    data = Data_1d_az(
                        item.dir,
                        "dat",
                        "1Daz~" + item.name.split("~")[1],
                        chi,
                        intensity,
                        {"type": item.info["type"]},
                    )
                    self.append_data(data)
                    self.plot_1d_az(
                        ax2, data.chi, data.intensity, data.name.split("~")[1]
                    )
            self.canvas2.draw()
            self.tabWidget.setCurrentWidget(self.tab_2)
            self.clear_lists()

            # self.plot_2Daz(data.data) # put plotting here

    def integrate_radial(self, data):
        # if data.info["type"] == "smp":
        #     norm_value = float(self.lineEdit_smp_TM.text().strip())
        # elif data.info["type"] == "bkg":
        #     norm_value = float(self.lineEdit_bkg_TM.text().strip())
        # else:
        norm_value = 1

        chi, intensity = self.ai.integrate_radial(
            data.array,
            self.sb_chi_points.value(),
            npt_rad=1000,
            correctSolidAngle=True,
            radial_range=(self.dsb_start_q.value(), self.dsb_end_q.value()),
            azimuth_range=None,
            mask=self.mask,
            dummy=None,
            delta_dummy=None,
            polarization_factor=None,
            dark=None,
            flat=None,
            method="cython",
            unit="chi_deg",
            radial_unit="q_A^-1",
            normalization_factor=norm_value,
        )
        return chi, intensity

    def click_integrate_2d(self):
        del self.ai
        _ = self.get_ai()
        if self.ai is None:
            self.no_ai_found_error()
        else:
            for item in self.get_all_selected():
                if isinstance(item, Data_2d):
                    az_image = item.integrate_2D(self.ai, self.mask)
                    data = Data_2d_az(
                        item.dir,
                        item.ext,
                        "2Daz~" + item.name.split("~")[1],
                        az_image,
                        {"type": item.info["type"], "dim": "2D"},
                    )
                    self.append_data(data)
                    self.set_plot_image_name(data.name, data.info["type"])
                    self.plot_2d_az(data.array, data.name)

            return data

    def subtract_1d_old(self):
        if len(self.listWidget_smp.selectedIndexes()) < 1:
            self.show_warning_messagebox("No sample selected.")
            return

        if len(self.listWidget_bkg.selectedIndexes()) < 1:
            self.show_warning_messagebox("No background selected.")
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1 and len(
            self.listWidget_bkg.selectedIndexes()
        ) != len(self.listWidget_smp.selectedIndexes()):
            self.show_warning_messagebox(
                "number of selected background and samples different. \
                    Returning."
            )
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1:
            self.show_warning_messagebox(
                "More than one background selected, only one background \
                    can be used at a time."
            )
            return

        for item in self.get_all_selected():
            if not isinstance(item, Data_1d):
                self.show_warning_messagebox("A data set is not 1 dimensional.")
                return

        bkg_name = self.listWidget_bkg.selectedIndexes()[0].data()
        bkg_data = self.background_data[bkg_name].intensity
        bkg_err = self.background_data[bkg_name].err

        for index in self.listWidget_smp.selectedIndexes():
            part1 = np.divide(
                self.sample_data[index.data()].intensity, float(self.lineEdit_smp_TM.text())
            )
            part2 = np.divide(bkg_data, float(self.lineEdit_bkg_TM.text()))
            err_p1 = np.divide(
                self.sample_data[index.data()].err, float(self.lineEdit_smp_TM.text())
            )
            err_p2 = np.divide(bkg_err, float(self.lineEdit_bkg_TM.text()))

            name = self.sample_data[index.data()].name
            name = "1D~" + "subd_" + name.split("~")[1]
            name = append_name(name, self.subtracted_data)
            out = Data_1d(
                self.sample_data[index.data()].dir,
                "dat",
                name,
                self.sample_data[index.data()].q,
                np.subtract(part1, part2),
                np.sqrt(np.add(np.power(err_p1, 2), np.power(err_p2, 2))),
                {"type": "sub", "dim": "1D"},
            )

            self.subtracted_data[out.name] = out
            self.listWidget_sub.addItem(out.name)
            if self.batch_mode:
                self.batch_sub_1d.append(out.name)

        self.tabWidget.setCurrentWidget(self.tab_2)
        self.clear_lists()

    def no_ai_found_error(self):
        self.show_warning_messagebox(
            "Scattering geometry information is not found, \
                input a .poni file or information from fit 2d",
            title="Error",
        )
    
    def click_integrate(self):
        try:
            if self.get_all_selected() == []:
                self.show_warning_messagebox("No data selected.")
                return
            
            del self.ai
            _ = self.get_ai()
            if self.ai is None:
                self.no_ai_found_error()
            else:
                self.figure2.clear()
                ax2 = self.figure2.add_subplot(111)
                
                temp = self.get_names_types_selected()

                names_types = []
                for item in temp:
                    if item[1] == "smp":
                        if isinstance(self.sample_data[item[0]], Data_2d):
                            names_types.append(item)
                        else:
                            self.show_warning_messagebox("A data set is not 2 dimensional.")
                            return
                    elif item[1] == "bkg":
                        if isinstance(self.background_data[item[0]], Data_2d):
                            names_types.append(item)
                        else:
                            self.show_warning_messagebox("A data set is not 2 dimensional.")
                            return
                    else:
                        if isinstance(self.subtracted_data[item[0]], Data_2d):
                            names_types.append(item)
                        else:
                            self.show_warning_messagebox("A data set is not 2 dimensional.")
                            return
                
                prog_dialog = QProgressDialog(self)
                prog_dialog.show()
                prog_dialog.autoClose()
                prog_dialog.canceled.connect(self.cancel_process)
                prog_dialog.setWindowTitle("Integrating data")
                prog_dialog.setLabelText(f"Integrating {len(names_types)} files")
                self.worker = Worker(
                    integrate_data,
                    self.ai,
                    self.sample_data,
                    self.background_data,
                    self.subtracted_data,
                    names_types,
                    self.sb_q_bins.value(),
                    self.dsb_chi_start.value(),
                    self.dsb_chi_end.value(),
                    self.mask,
                    self.batch_mode,
                    self.monitor_002
                    )
                self.worker.start() 
                self.worker.export_data_signal.connect(self.append_data)
                if self.batch_mode:
                    self.worker.export_data_signal.connect(self.append_batch_mode_lists)
                if not prog_dialog.wasCanceled():
                    self.worker.progress_signal.connect(prog_dialog.setValue)
                self.worker.finished.connect(self.worker.deleteLater)

                if not self.batch_mode:
                    self.worker.finished.connect(self.clear_lists)
        except Exception as e:
            self.show_warning_messagebox(str(e))       
 
    def click_load_poni(self):
        try:
            if self.BL23A_mode:
                fname, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Select parameter file.toml",
                    "",
                    "toml (*.toml);;All Files (*)",
                )
                if fname and fname != "":
                    with open(fname, "rb") as f:
                        fit2d_dic = tomli.load(f)
                    self.fill_param_settings(fit2d_dic)
                    _ = self.get_ai()
                    self.disable_params_input()
                    self.set_enable_data_operations(True)
            else:
                if self.fit2d_mode:
                    self.show_warning_messagebox(
                        "FIT2d mode is currently set so the image \
                            is flipped compared to .poni orientation. \
                                Please restart and set no to FIT2d option \
                                    or proceed with care!"
                    )
                fname, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self, "Select PONI file", "", "PONI (*.poni);;All Files (*)"
                )
                if fname and fname != "":
                    self.ai = pyFAI.load(fname)
                    fit2d_dic = self.ai.getFit2D()
                    self.fill_param_settings(fit2d_dic)
                    self.disable_params_input()
                    self.set_enable_data_operations(True)
        except Exception as e:
            print(e)

    def fill_param_settings(self, fit2d_dic):
        self.lineEdit_X.setText(str(fit2d_dic["pixelX"])[0:12])
        self.lineEdit_Y.setText(str(fit2d_dic["pixelY"])[0:12])
        # .text(fit2d_dic["directDist"])
        self.lineEdit_SD.setText(str(fit2d_dic["directDist"])[0:12])
        self.lineEdit_wavelength.setText(str(fit2d_dic["waveLength"])[0:12])
        self.lineEdit_X_dir.setText(str(fit2d_dic["centerX"])[0:12])
        # invert Y below ###############################################
        self.lineEdit_Y_dir.setText(str(fit2d_dic["centerY"])[0:12])  # 2352 -
        #################################################################
        self.lineEdit_rotAngTiltPlane.setText(str(fit2d_dic["tiltPlanRotation"])[0:12])
        self.lineEdit_angDetTilt.setText(str(fit2d_dic["tilt"])[0:12])

    def disable_params_input(self):
        self.lineEdit_X.setDisabled(True)
        self.lineEdit_Y.setDisabled(True)
        self.lineEdit_SD.setDisabled(True)
        self.lineEdit_wavelength.setDisabled(True)
        self.lineEdit_X_dir.setDisabled(True)
        self.lineEdit_Y_dir.setDisabled(True)
        self.lineEdit_rotAngTiltPlane.setDisabled(True)
        self.lineEdit_angDetTilt.setDisabled(True)
        self.btn_load_PONI.setDisabled(True)
        self.btn_save_PONI.setDisabled(True)

    def get_ai(self):
        fit2d_dic = {}
        fit2d_dic["pixelX"] = float(self.lineEdit_X.text().strip())
        fit2d_dic["pixelY"] = float(self.lineEdit_Y.text().strip())
        fit2d_dic["directDist"] = float(self.lineEdit_SD.text().strip())
        fit2d_dic["waveLength"] = float(self.lineEdit_wavelength.text().strip())
        fit2d_dic["centerX"] = float(self.lineEdit_X_dir.text().strip())
        fit2d_dic["centerY"] = float(self.lineEdit_Y_dir.text().strip())
        fit2d_dic["tiltPlanRotation"] = float(
            self.lineEdit_rotAngTiltPlane.text().strip()
        )
        fit2d_dic["tilt"] = float(self.lineEdit_angDetTilt.text().strip())

        self.ai = azimuthalIntegrator.AzimuthalIntegrator(
            wavelength=float(self.lineEdit_wavelength.text().strip()) / 10_000_000_000
        )

        self.ai.setFit2D(
            fit2d_dic["directDist"],
            fit2d_dic["centerX"],
            fit2d_dic["centerY"],  # 2352 -
            fit2d_dic["tilt"],
            fit2d_dic["tiltPlanRotation"],
            fit2d_dic["pixelX"],
            fit2d_dic["pixelY"],
        )
        return fit2d_dic

    def click_save_poni(self):
        try:
            fit2d_dic = self.get_ai()

            if self.BL23A_mode:
                fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self, "Parameter file save name", "", "toml (*.toml);;All Files (*)"
                )
                if fname and fname != "":
                    if os.path.splitext(fname)[1] != ".toml":
                        fname += ".toml"
                    with open(fname, "wb") as f:
                        tomli_w.dump(fit2d_dic, f)
            else:
                fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self, "Poni file save name", "", "PONI (*.poni);;All Files (*)"
                )

                self.ai.write(fname)
            self.disable_params_input()
            self.set_enable_data_operations(True)

        except Exception as e:
            print(e)
            return

    def get_first_sel(self):
        try:
            if len(self.listWidget_smp.selectedItems()) != 0:
                # self.listWidget_smp.selectedIndexes()[0].data():
                item = self.listWidget_smp.selectedIndexes()[0].data()
                data = self.sample_data[item]
                # if isinstance(data, Data_2d) or isinstance(data, Data_2d_az):
                return data
            if len(self.listWidget_bkg.selectedItems()) != 0:
                item = self.listWidget_bkg.selectedIndexes()[0].data()
                data = self.background_data[item]
                # if isinstance(data, Data_2d) or isinstance(data, Data_2d_az):
                return data
            if len(self.listWidget_sub.selectedIndexes()) != 0:
                item = self.listWidget_sub.selectedIndexes()[0].data()
                data = self.subtracted_data[item]
                # if isinstance(data, Data_2d) or isinstance(data, Data_2d_az):
                return data
        except Exception as e:
            data_2d = None
            print(e)
            return data_2d

    def get_names_types_selected(self, data_type="all"):
        all_names = []
        if len(self.listWidget_smp.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "smp":
                for item in self.listWidget_smp.selectedIndexes():
                    all_names.append((item.data(), "smp"))
        if len(self.listWidget_bkg.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "bkg":
                for item in self.listWidget_bkg.selectedIndexes():
                    all_names.append((item.data(), "bkg"))
        if len(self.listWidget_sub.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "sub":
                for item in self.listWidget_sub.selectedIndexes():
                    all_names.append((item.data(), "sub"))
        return all_names
    
    
    def get_all_selected(self, data_type="all"):
        '''
        todo update to using list comprehension
        '''
        all_data = []
        if len(self.listWidget_smp.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "smp":
                for item in self.listWidget_smp.selectedIndexes():
                    all_data.append(self.sample_data[item.data()])
        if len(self.listWidget_bkg.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "bkg":
                for item in self.listWidget_bkg.selectedIndexes():
                    all_data.append(self.background_data[item.data()])
        if len(self.listWidget_sub.selectedIndexes()) != 0:
            if data_type == "all" or data_type == "sub":
                for item in self.listWidget_sub.selectedIndexes():
                    all_data.append(self.subtracted_data[item.data()])
        return all_data

    def remove_selected(self):
        # update to while list
        while len(self.listWidget_smp.selectedIndexes()) > 0:
            item = self.listWidget_smp.selectedIndexes()[0]
            del self.sample_data[item.data()]
            self.listWidget_smp.takeItem(item.row())
            

        while len(self.listWidget_bkg.selectedIndexes()) > 0:
            item = self.listWidget_bkg.selectedIndexes()[0]
            del self.background_data[item.data()]
            self.listWidget_bkg.takeItem(item.row())
            

        while len(self.listWidget_sub.selectedIndexes()) > 0:
            item = self.listWidget_sub.selectedIndexes()[0]
            del self.subtracted_data[item.data()]
            self.listWidget_sub.takeItem(item.row())
            
        gc.collect()

    def set_plot_image_name(self, name, img_type):
        self.plt_info = (name, img_type)


    def get_plot_image_data(self):
        if self.plt_info[1] == "smp":
            return self.sample_data[self.plt_info[0]]
        elif self.plt_info[1] == "bkg":
            return self.background_data[self.plt_info[0]]
        else:
            return self.subtracted_data[self.plt_info[0]]

    def click_show_data(self):
        data = self.get_first_sel()
        if (
            isinstance(data, Data_2d)
            or isinstance(data, Data_2d_az)
            or isinstance(data, Data_2d_rot)
        ):
            self.set_plot_image_name(data.name, data.info["type"])
            self.tabWidget.setCurrentWidget(self.tab)
            self.show_image()
        elif isinstance(data, Data_1d) or isinstance(data, Data_1d_az):
            self.tabWidget.setCurrentWidget(self.tab_2)
            self.plot_1d()

    def show_image(self, data = None):
        if data is None:
            data_2d = self.get_first_sel()
        else:
            data_2d = data
        
        if isinstance(data_2d, Data_2d):
            image = data_2d.array
            # try:
            if image is not None:
                if self.mask is not None:
                    image = mask_pix_zero(image, self.mask)
                self.plot_2d(image, data_2d.name)
                self.set_plot_image_name(data_2d.name, data_2d.info["type"])
                self.clear_lists()
            # except:
            #    self.show_warning_messagebox("Image did not pass.")
        elif isinstance(data_2d, Data_2d_az):
            self.plot_2d_az(data_2d.array, data_2d.name)
            self.set_plot_image_name(data_2d.name, data_2d.info["type"])
            self.clear_lists()

        elif isinstance(data_2d, Data_2d_rot):
            self.plot_2d(data_2d.array, data_2d.name)
            self.set_plot_image_name(data_2d.name, data_2d.info["type"])
            self.clear_lists()

        elif isinstance(data_2d, Data_1d):
            self.show_warning_messagebox("Selected is one dimensional data.")
            self.clear_lists()

    def clear_lists(self):
        self.listWidget_smp.clearSelection()
        self.listWidget_bkg.clearSelection()
        self.listWidget_sub.clearSelection()

    def check_overflow_pix(self, array, name):
        num_high_pix = self.count_overflow_pix(array.copy())
        if num_high_pix > 0 and self.bit_depth < 32:
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("Pixel(s) overflowing, convert to higher bit depth")
            dlg.setText(
                str(num_high_pix)
                + " saturated pixels in image "
                + name
                + '. \n Select "YES" to set image type to '
                + str(2 * self.bit_depth)
                + ' bit. \n Select "NO" \
                    to keep 16 bit images and set satureated values to '
                + str(2**self.bit_depth - 1)
            )
            dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            dlg.setIcon(QtWidgets.QMessageBox.Question)
            button = dlg.exec()
            if button == QtWidgets.QMessageBox.Yes:
                self.bit_depth *= 2
                return array
            else:
                return self.set_overflow_pix_saturated(array.copy())

        elif num_high_pix > 0 and self.bit_depth == 32:
            self.set_overflow_pix_saturated(array.copy())
            self.show_warning_messagebox(
                str(num_high_pix)
                + " saturated pixels in image, \
                        all saturated pixels will be set to"
                + str(2**self.bit_depth - 1)
            )
            return self.set_overflow_pix_saturated(array.copy())
        else:
            return array

    def set_overflow_pix_saturated(self, a):
        overflow_pix = np.squeeze(np.where(a > 2**self.bit_depth - 1))
        a[overflow_pix[0], overflow_pix[1]] = 2**self.bit_depth - 1
        return np.array(a)  # , dtype = "int"+str(self.bit_depth))

    def count_overflow_pix(self, a):
        overflow_pix = np.squeeze(np.where(a >= 2**self.bit_depth - 1))
        a.fill(0)
        a[overflow_pix[0], overflow_pix[1]] = 1
        return np.sum(a)

    def click_export(self):
        try:
            if self.get_all_selected() == []:
                self.show_warning_messagebox("No data selected.")
                return
            
            names_types = self.get_names_types_selected()
            
            prog_dialog = QProgressDialog(self)
            prog_dialog.show()
            prog_dialog.autoClose()
            prog_dialog.canceled.connect(self.cancel_process)
            prog_dialog.setWindowTitle("Exporting data")
            prog_dialog.setLabelText(f"Exporting {len(names_types)} files")
            self.worker = Worker(
                export_data,
                self.sample_data,
                self.background_data,
                self.subtracted_data,
                names_types,
                self.bit_depth,
                self.batch_mode
            )
            self.worker.start()
            if not prog_dialog.wasCanceled():
                self.worker.progress_signal.connect(prog_dialog.setValue)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(self.clear_lists)
        except Exception as e:
            print(e)
            self.show_warning_messagebox("Exporting failed.")

    def evt_update_batchmode_data(self, data):
        self.toggle_select_by_string(data, data.info["type"], False)
        if data.info["type"] == "smp" and isinstance(data, Data_2d):
            self.batch_smp_2d.append(data.name)
        elif data.info["type"] == "bkg" and isinstance(data, Data_2d):
            self.batch_bkg_2d.append(data.name)
        elif data.info["type"] == "smp" and isinstance(data, Data_1d):
            self.batch_smp_1d.append(data.name)
        elif data.info["type"] == "bkg" and isinstance(data, Data_1d):
            self.batch_bkg_1d.append(data.name)

    
    def click_remove_outliers(self):
        # if we have a large number selected we copy these to a new list??
        # this is not needed...
        if self.get_all_selected() == []:
                self.show_warning_messagebox("No data selected.")
                return

        temp = self.get_names_types_selected()
        names_types = []
        for item in temp:
            if item[1] == "smp":
                if isinstance(self.sample_data[item[0]], Data_2d):
                    names_types.append(item)
            elif item[1] == "bkg":
                if isinstance(self.background_data[item[0]], Data_2d):
                    names_types.append(item)
            else:
                if isinstance(self.subtracted_data[item[0]], Data_2d):
                    names_types.append(item)

        if self.comboBox_size.currentText() == "3":
            size = int(3)
        elif self.comboBox_size.currentText() == "5":
            size = int(5)
        
        threshold = float(self.lineEdit_threshold.text())
        
        prog_dialog = QProgressDialog(self)
        prog_dialog.show()
        prog_dialog.autoClose()
        prog_dialog.canceled.connect(self.cancel_process)
        prog_dialog.setWindowTitle("Removing outliers.")
        prog_dialog.setLabelText(f"Processing {len(names_types)} files")
        self.worker = Worker(
                    remove_outliers,
                    names_types,
                    self.sample_data,
                    self.background_data,
                    self.subtracted_data,
                    size, 
                    threshold, 
                    self.batch_mode
        )
        self.worker.start()
        self.worker.export_data_signal.connect(self.append_data)
        if self.batch_mode == True:
            self.worker.export_data_signal.connect(self.append_batch_mode_lists)
        
                  
        if not prog_dialog.wasCanceled():
            self.worker.progress_signal.connect(prog_dialog.setValue)
        if not self.batch_mode:
            self.worker.finished.connect(self.clear_lists)
        self.worker.finished.connect(self.worker.deleteLater)
        
        #TODO : do we need this quit?
        #self.worker.finished.connect(self.worker.quit)

    def append_batch_mode_lists(self,data):
        if isinstance(data, Data_1d):
            if data.info["type"] == "smp":
                self.batch_smp_1d.append(data.name)
            elif data.info["type"] == "bkg":
                self.batch_bkg_1d.append(data.name)
            elif data.info["type"] == "sub":
                self.batch_sub_1d.append(data.name)
        elif isinstance(data, Data_2d):
            if data.info["type"] == "smp":
                self.batch_smp_2d.append(data.name)
            elif data.info["type"] == "bkg":
                self.batch_bkg_2d.append(data.name)
            elif data.info["type"] == "sub":
                self.batch_sub_2d.append(data.name)
    

    def plot_1d_1d_data(self, axis, q, intensity, err, label):
        axis.errorbar(q, intensity, yerr=err, label=label)
        # plt.plot(item.q,item.I,label=item.name)
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("q [Ang.^-1]")
        axis.set_ylabel("I(q) [arb. units]")
        axis.legend(fontsize=9)

    def plot_1d_az(self, axis, chi, intensity, label):
        axis.plot(chi, intensity, label=label)
        axis.set_xscale("linear")
        axis.set_yscale("linear")
        axis.set_xlabel("chi [deg.]")
        axis.set_ylabel("I(q) [arb. units]")
        axis.legend(fontsize=9)

    def plot_1d(self):
        # clearing old figure
        # self.tabWidget.setCurrentIndex(1)
        self.figure2.clear()

        # create an axis
        ax2 = self.figure2.add_subplot(111)
        # self.get_scale_max(image)
        # plot data
        for item in self.get_all_selected():
            if isinstance(item, Data_1d):
                self.plot_1d_1d_data(
                    ax2, item.q, item.intensity, item.err, item.name.split("~")[1]
                )
            elif isinstance(item, Data_1d_az):
                self.plot_1d_az(ax2, item.chi, item.intensity, item.name.split("~")[1])

        self.canvas2.draw()
        self.clear_lists()

    def plot_2d_az(self, image, title):
        self.figure.clear()

        # create an axis
        ax = self.figure.add_subplot(111)
        # self.get_scale_max(image)
        # plot data
        colornorm = SymLogNorm(
            1, base=10, vmin=np.nanmin(image[0]), vmax=np.nanmax(image[0])
        )
        # colornorm = 'linear'
        ax.imshow(
            image[0],
            cmap="inferno",
            extent=[image[1][0].min(), image[1].max(), image[2].min(), image[2].max()],
            norm=colornorm,
            origin="lower",
        )
        ax.set_title(title)
        ax.set_aspect("auto")
        ax.set_xlabel("q [Ang. ^-1]")
        ax.set_ylabel("azi. ang. chi (deg.)")
        # ,extent=[image[1][0],image[1][-1],image[2][0],image[2][-1]],
        # ax.set_xticks(image[1])
        # ax.set_yticks(image[2])
        # ax.set_position([0.2, 0.2, 0.6, 0.6])
        # refresh canvas
        # self.figure.tight_layout(pad=0.4, w_pad=20, h_pad=1.0)
        # self.figure.tight_layout()
        # self.figure.
        self.canvas.draw()

    def plot_2d(self, image, title):
        self.figure.clear()
        colornorm = SymLogNorm(1, base=10, vmin=np.nanmin(image), vmax=np.nanmax(image))
        self.ax = self.figure.add_subplot(111)
        self.get_scale_max(image)

        self.ax.imshow(image, cmap="inferno", norm=colornorm, origin="lower",interpolation="none")
        self.ax.set_title(title)
        self.canvas.draw()

    ##########################################

    def get_scale_max(self, image):
        maxindex = np.amax(image)
        meanindex = np.mean(image)

        if maxindex > 10 * meanindex:
            self.scale_max = int(meanindex * 5)
        else:
            self.scale_max = int(maxindex)

    def append_data(self, data):
        data_type = data.info["type"]
        if data_type == "smp":
            data.name = append_name(data.name, self.sample_data)
            self.sample_data[data.name] = data
            self.listWidget_smp.addItem(self.sample_data[data.name].name)
            # self.listWidget_smp.setCurrentItem(QtWidgets.QListWidgetItem(sample_data[data.name].name))
        elif data_type == "bkg":
            data.name = append_name(data.name, self.background_data)
            self.background_data[data.name] = data
            self.listWidget_bkg.addItem(self.background_data[data.name].name)
        elif data_type == "sub":
            data.name = append_name(data.name, self.subtracted_data)
            self.subtracted_data[data.name] = data
            self.listWidget_sub.addItem(self.subtracted_data[data.name].name)
        del data

    def set_bit_depth(self, array):
        if array.dtype == "uint8" or array.dtype == "int8":
            self.bit_depth = 8
        elif array.dtype == "uint16" or array.dtype == "int16":
            self.bit_depth = 16
        elif array.dtype == "uint32" or array.dtype == "int32":
            self.bit_depth = 32
        else:
            self.show_warning_messagebox(
                "Image appears to be neither a 8, 16, or 32 bit image. \
                    This is currently not supported."
            )

    def init_image_import(self, data):
        array = data.array
        del data
        if self.bit_depth is None:
            self.set_bit_depth(array)
            if not self.BL23A_mode:
                self.show_warning_messagebox(
                    "Image bit depth of "
                    + str(self.bit_depth)
                    + " found and will be used for writing and manipulating\
                            images, please be aware of bit overflow\n\
                                Max value for images is "
                    + str(2**self.bit_depth - 1)
                )

        if (self.saturated_pix_mask is False) and (
            self.auto_mask_saturated_pixels is True
        ):
            self.mask = make_saturated_mask(array, self.bit_depth)
            if not self.BL23A_mode:
                self.show_warning_messagebox(
                    "Masked "
                    + str(np.sum(self.mask))
                    + " saturated pixels which had values of 2^"
                    + str(self.bit_depth)
                    + "-1"
                )
            self.saturated_pix_mask = True

    def evt_update_pbar_label(self, message):
        self.lbl_pbar.setVisible(True)
        self.lbl_pbar.setText(message)
        
    def click_import_data(self, data_type):

        # open file dialog returns a tuple
        fnames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select multiple files",
            "",
            " tif Image (*.tif);;h5 Image (*master.h5);;1D data (*.dat);;All Files (*)",
        )
        if len(fnames) == 0:
            return
        
        self.t1 = perf_counter()
        prog_dialog = QProgressDialog(self) #, f"Importing {len(fnames)} files", "Importing data")
        
        #self.prog_dialog = ProgressDialog(self, f"Importing {len(fnames)} files", "Importing data")
        prog_dialog.show()
        prog_dialog.autoClose()
        prog_dialog.canceled.connect(self.cancel_process)
        prog_dialog.setWindowTitle("Importing data")
        prog_dialog.setLabelText(f"Importing {len(fnames)} files")
        self.worker = Worker(import_data, fnames, data_type, self.fit2d_mode, self.monitor_002)
        
        self.worker.start() 

        self.worker.export_data_signal.connect(self.append_data)
        self.worker.export_data_signal.connect(self.init_image_import)

        # need to do the init part later

        # need to do cancel later
        if not prog_dialog.wasCanceled():
            self.worker.progress_signal.connect(prog_dialog.setValue)
        self.worker.finished.connect(self.worker.deleteLater)
        self.clear_lists()
    
    def cancel_process(self):
        #self.prog_dialog.destroy(destroyWindow=True)
        if self.worker.isRunning():
            self.worker.cancel_signal.emit(True)
        QApplication.processEvents()
        #self.worker.quit()


    def show_warning_messagebox(self, text, title="Warning"):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        # setting message for Message Box
        msg.setText(text)

        # setting Message box window title
        msg.setWindowTitle(title)

        # declaring buttons on Message Box
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        # start the app
        msg.exec_()
        # retval = msg.exec_()

    def subtract_2d(self):
        # try:

        

        # except:
        #    self.show_warning_messagebox("No background selected.")
        #    return
        # if len(self.listWidget_bkg.selectedIndexes()) == 1:
        bkg_name = self.listWidget_bkg.selectedIndexes()[0].data()
        bkg_data = self.background_data[bkg_name].array

        if self.mask is not None:
            bkg_data = self.mask_pix_zero(bkg_data, self.mask)

        for index in self.listWidget_smp.selectedIndexes():
            out = {}
            out["dir"] = self.sample_data[index.data()].dir
            out["ext"] = self.sample_data[index.data()].ext
            name = self.sample_data[index.data()].name
            out["name"] = name.split("~")[0] + "~" + "subd_" + name.split("~")[1]
            out["name"] = append_name(
                out["name"], self.subtracted_data
            )  # add one if exists
            out["info"] = {"type": "sub"}
            if self.mask is not None:
                smp_data = mask_pix_zero(self.sample_data[index.data()].array, self.mask)
            else:
                smp_data = self.sample_data[index.data()].array

            scale_factor = 1

            # if self.monitor_002:
            #     civi_smp = sample_data[index.data()].info['civi']
            #     civi_bkg = background_data[bkg_name].info['civi']
            # else:
            civi_smp = 1
            civi_bkg = 1

            part1 = np.divide(
                smp_data * scale_factor, float(self.lineEdit_smp_TM.text()) * civi_smp
            )
            part2 = np.divide(
                bkg_data * scale_factor, float(self.lineEdit_bkg_TM.text()) * civi_bkg
            )
            out["array"] = np.subtract(part1, part2)
            
            if self.bit_depth == 8:
                out["array"] = out["array"].astype(np.uint8)
            elif self.bit_depth == 16:
                out["array"] = out["array"].astype(np.uint16)
            else:
                out["array"] = out["array"].astype(np.uint32)

            self.subtracted_data[out["name"]] = Data_2d(
                out["dir"], out["ext"], out["name"], out["array"], out["info"]
            )
            self.listWidget_sub.addItem(out["name"])
            if self.batch_mode:
                self.batch_sub_2d.append(out["name"])
                QApplication.processEvents()

        if not self.batch_mode:
            self.set_plot_image_name(out["name"], out["info"]["type"])
            self.plot_2d(self.subtracted_data[out["name"]].array, out["name"])

        self.tabWidget.setCurrentWidget(self.tab)
        self.listWidget_smp.clearSelection()
        self.listWidget_bkg.clearSelection()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
