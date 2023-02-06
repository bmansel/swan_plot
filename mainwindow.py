# -*- coding: utf-8 -*-

from utils import *

import ctypes

import sys 
#sys.path.insert(0, "/opt/dectris/albula/4.1/bin") 
#sys.path.insert(0, "/opt/dectris/albula/4.1/python") 
#import dectris.albula
import numpy as np
import fabio
import os
import tifffile
import pyFAI
#import imutils
#import cv2
import PIL.Image as IImage

from pyFAI import azimuthalIntegrator
from PyQt5 import QtCore, QtGui, QtWidgets
#from dataclasses import dataclass
from matplotlib import pyplot
from pathlib import Path

from scipy import ndimage as ndi 
from skimage.morphology import disk
from skimage import io


# adding below for matplotlib
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout, QInputDialog, QMenu, QAction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
import random




class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 900)
        #####################################################################
        # not needed on linux etc
        #myappid = u'SWAN_plot'
        #ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) 
        #####################################################################
        MainWindow.setWindowIcon(QtGui.QIcon('../images/icon.png'))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.grpBx_TM = QtWidgets.QGroupBox(self.centralwidget)
        self.grpBx_TM.setGeometry(QtCore.QRect(20, 20, 541, 71))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.grpBx_TM.setFont(font)
        self.grpBx_TM.setObjectName("grpBx_TM")
        self.gridLayoutWidget = QtWidgets.QWidget(self.grpBx_TM)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 30, 541, 33))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(6, 0, 6, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_bkg_TM = QtWidgets.QLineEdit(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_bkg_TM.setFont(font)
        self.lineEdit_bkg_TM.setObjectName("lineEdit_bkg_TM")
        self.gridLayout.addWidget(self.lineEdit_bkg_TM, 0, 3, 1, 1)
        self.lbl_bkg_TM = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lbl_bkg_TM.setFont(font)
        self.lbl_bkg_TM.setObjectName("lbl_bkg_TM")
        self.gridLayout.addWidget(self.lbl_bkg_TM, 0, 2, 1, 1)
        self.lineEdit_smp_TM = QtWidgets.QLineEdit(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_smp_TM.setFont(font)
        self.lineEdit_smp_TM.setObjectName("lineEdit_smp_TM")
        self.gridLayout.addWidget(self.lineEdit_smp_TM, 0, 1, 1, 1)
        self.lbl_smp_TM = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.lbl_smp_TM.setFont(font)
        self.lbl_smp_TM.setObjectName("lbl_smp_TM")
        self.gridLayout.addWidget(self.lbl_smp_TM, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(20, 100, 951, 771))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.groupBox)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 20, 951, 171))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_2 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.groupBox_2)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(-1, 19, 311, 141))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.btn_import_smp = QtWidgets.QPushButton(self.verticalLayoutWidget, clicked = lambda: self.import_data("smp"))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_smp.setFont(font)
        self.btn_import_smp.setObjectName("btn_import_smp")
        self.verticalLayout.addWidget(self.btn_import_smp)
        self.listWidget_smp = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.listWidget_smp.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.listWidget_smp.setObjectName("listWidget_smp")
        self.verticalLayout.addWidget(self.listWidget_smp)
        self.horizontalLayout.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.groupBox_3)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(0, 20, 311, 144))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.btn_import_bkg = QtWidgets.QPushButton(self.verticalLayoutWidget_2, clicked = lambda: self.import_data("bkg"))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_bkg.setFont(font)
        self.btn_import_bkg.setObjectName("btn_import_bkg")
        self.verticalLayout_2.addWidget(self.btn_import_bkg)
        self.listWidget_bkg = QtWidgets.QListWidget(self.verticalLayoutWidget_2)
        self.listWidget_bkg.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.listWidget_bkg.setObjectName("listWidget_bkg")
        self.listWidget_bkg.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.verticalLayout_2.addWidget(self.listWidget_bkg)
        self.horizontalLayout.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_4.setFont(font)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.groupBox_4)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(0, 20, 311, 141))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.btn_import_subd = QtWidgets.QPushButton(self.verticalLayoutWidget_3, clicked = lambda: self.import_data("sub"))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_import_subd.setFont(font)
        self.btn_import_subd.setObjectName("btn_import_subd")
        self.verticalLayout_3.addWidget(self.btn_import_subd)
        self.listWidget_processed = QtWidgets.QListWidget(self.verticalLayoutWidget_3)
        self.listWidget_processed.setObjectName("listWidget_processed")
        self.listWidget_processed.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.verticalLayout_3.addWidget(self.listWidget_processed)
        self.horizontalLayout.addWidget(self.groupBox_4)
        self.tabWidget = QtWidgets.QTabWidget(self.groupBox)
        self.tabWidget.setGeometry(QtCore.QRect(10, 230, 931, 531))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.tabWidget.setFont(font)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.btn_show = QtWidgets.QPushButton(self.groupBox, clicked= lambda: self.click_show_data())
        self.btn_show.setGeometry(QtCore.QRect(371, 190, 101, 25))
        self.btn_show.setObjectName("btn_show")
        self.btn_show.setFont(font)
        self.btn_sum = QtWidgets.QPushButton(self.groupBox, clicked= lambda: self.click_sum_data())
        self.btn_sum.setGeometry(QtCore.QRect(491, 190, 101, 25))
        self.btn_sum.setObjectName("btn_sum")
        self.btn_sum.setFont(font)
        
        self.btn_average = QtWidgets.QPushButton(self.groupBox, clicked= lambda: self.click_average_data())
        self.btn_average.setGeometry(QtCore.QRect(611, 190, 101, 25))
        self.btn_average.setObjectName("btn_average")
        self.btn_average.setFont(font)

        self.groupBox_5 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_5.setGeometry(QtCore.QRect(739, 40, 181, 161))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_5.setFont(font)
        self.groupBox_5.setObjectName("groupBox_5")

        self.groupBox_rot_img = QtWidgets.QGroupBox(self.tab)
        self.groupBox_rot_img.setGeometry(QtCore.QRect(739, 211, 181, 101))
        self.groupBox_rot_img.setObjectName("groupBox_rot_img")
        self.groupBox_rot_img.setFont(font)

        #self.btn_get_rot_ang = QtWidgets.QPushButton(self.groupBox_rot_img, clicked= lambda: self.click_get_rot_ang())
        #self.btn_get_rot_ang.setGeometry(QtCore.QRect(10, 100, 75, 25))
        #self.btn_get_rot_ang.setObjectName("btn_get_rot_ang")

        self.lbl_rot_ang = QtWidgets.QLabel(self.groupBox_rot_img)
        self.lbl_rot_ang.setGeometry(QtCore.QRect(15, 30, 67, 17))

        self.dsb_rot_ang = QtWidgets.QDoubleSpinBox(self.groupBox_rot_img)
        self.dsb_rot_ang.setGeometry(QtCore.QRect(15, 57, 67, 26))
        self.dsb_rot_ang.setMinimum(-360.0)
        self.dsb_rot_ang.setMaximum(360.0)
        self.dsb_rot_ang.setValue(0.0)

        self.btn_rot_img = QtWidgets.QPushButton(self.groupBox_rot_img, clicked= lambda: self.click_rot_img())
        self.btn_rot_img.setGeometry(QtCore.QRect(95, 57, 75, 25))
        self.btn_rot_img.setObjectName("btn_rot_img")


        self.label = QtWidgets.QLabel(self.groupBox_5)
        self.label.setGeometry(QtCore.QRect(10, 30, 67, 17))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.lineEdit_radius = QtWidgets.QLineEdit(self.groupBox_5)
        self.lineEdit_radius.setGeometry(QtCore.QRect(10, 50, 113, 25))
        self.lineEdit_radius.setObjectName("lineEdit_radius")
        self.lineEdit_threshold = QtWidgets.QLineEdit(self.groupBox_5)
        self.lineEdit_threshold.setGeometry(QtCore.QRect(10, 100, 113, 25))
        self.lineEdit_threshold.setObjectName("lineEdit_threshold")
        self.label_2 = QtWidgets.QLabel(self.groupBox_5)
        self.label_2.setGeometry(QtCore.QRect(10, 80, 91, 17))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.btn_remove_outliers = QtWidgets.QPushButton(self.groupBox_5, clicked= lambda: self.click_rem_outliers())
        self.btn_remove_outliers.setGeometry(QtCore.QRect(10, 130, 151, 25))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setBold(False)
        font.setWeight(50)
        self.btn_remove_outliers.setFont(font)
        self.btn_remove_outliers.setObjectName("btn_remove_outliers")
        self.btn_2d_subtract = QtWidgets.QPushButton(self.tab, clicked = lambda: self.subtract_2D())
        self.btn_2d_subtract.setGeometry(QtCore.QRect(788, 454, 121, 41))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_2d_subtract.setFont(font)
        self.btn_2d_subtract.setObjectName("btn_2d_subtract")
        

        #####################################################################
        self.btn_2d_integrate = QtWidgets.QPushButton(self.tab, clicked = lambda: self.click_integrate_2D())
        self.btn_2d_integrate.setGeometry(QtCore.QRect(788, 404, 121, 41))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_2d_integrate.setFont(font)
        self.btn_2d_integrate.setObjectName("btn_2d_integrate")


        #####################################################################
        #self.frame = QtWidgets.QFrame(self.tab)
        #self.frame.setGeometry(QtCore.QRect(9, 9, 721, 481))
        #self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        #self.frame.setObjectName("frame")
        ######################################################################
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        #self.Btn_show_1d = QtWidgets.QPushButton(self.tab_2, clicked = lambda: self.click_plot_1D())
        #self.Btn_show_1d.setGeometry(QtCore.QRect(798, 10, 111, 25))
        #self.Btn_show_1d.setObjectName("Btn_show_1d")
        self.btn_1D_subtract = QtWidgets.QPushButton(self.tab_2, clicked = lambda: self.click_1D_subtract())
        self.btn_1D_subtract.setGeometry(QtCore.QRect(798, 100, 111, 25))
        self.btn_1D_subtract.setObjectName("btn_1D_subtract")
        #self.btn_integrate = QtWidgets.QPushButton(self.tab_2, clicked = lambda: self.click_integrate())
        #self.btn_integrate.setGeometry(QtCore.QRect(798, 40, 111, 25))
        #self.btn_integrate.setObjectName("btn_integrate")
        #self.lbl_chi = QtWidgets.QLabel(self.tab_2)
        #self.lbl_chi.setGeometry(QtCore.QRect(798, 70, 111, 25))
        #self.lbl_chi.setObjectName("lbl_chi")
        #self.lbl_chi.setText("text")
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
        self.btn_load_PONI = QtWidgets.QPushButton(self.groupBox_6,clicked=lambda: self.click_load_PONI())
        self.btn_load_PONI.setGeometry(QtCore.QRect(10, 280, 91, 25))
        self.btn_load_PONI.setObjectName("btn_load_PONI")
        self.btn_save_PONI = QtWidgets.QPushButton(self.groupBox_6,clicked=lambda: self.click_save_PONI())
        self.btn_save_PONI.setGeometry(QtCore.QRect(110, 280, 89, 25))
        self.btn_save_PONI.setObjectName("btn_save_PONI")
        self.btn_load_PSAXS = QtWidgets.QPushButton(self.groupBox_6, clicked=lambda: self.click_load_PSAXS())
        self.btn_load_PSAXS.setGeometry(QtCore.QRect(10, 310, 121, 25))
        self.btn_load_PSAXS.setObjectName("btn_load_PSAXS")
        self.btn_load_mask = QtWidgets.QPushButton(self.groupBox_6, clicked=lambda: self.click_load_mask())
        self.btn_load_mask.setGeometry(QtCore.QRect(10, 340, 89, 25))
        self.btn_load_mask.setObjectName("btn_load_mask")
        self.btn_load_reject = QtWidgets.QPushButton(self.groupBox_6, clicked=lambda: self.click_load_reject())
        self.btn_load_reject.setGeometry(QtCore.QRect(10, 370, 89, 25))
        self.btn_load_reject.setObjectName("btn_load_reject")
        
        self.cb_002 = QtWidgets.QCheckBox(self.groupBox_6)
        self.cb_002.setGeometry(QtCore.QRect(141, 310, 141, 25))
        self.cb_002.stateChanged.connect(self.check002)

        self.saturated_pix_mask = False

        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.addTab(self.tab_settings, "")
        #self.btn_remove = QtWidgets.QPushButton(self.groupBox)
        
        self.btn_remove = QtWidgets.QPushButton(self.groupBox, clicked=lambda: self.remove_selected())
        self.btn_remove.setGeometry(QtCore.QRect(10, 190, 101, 25))
        font = QtGui.QFont()
        font.setStyleName('Microsoft Sans Serif')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_remove.setFont(font)
        self.btn_remove.setObjectName("btn_remove")
        self.btn_export = QtWidgets.QPushButton(self.groupBox, clicked = lambda: self.click_export())
        self.btn_export.setGeometry(QtCore.QRect(130, 190, 101, 25))
        font = QtGui.QFont()
        font.setStyleName('Helvetica')
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.btn_export.setFont(font)
        self.btn_export.setObjectName("btn_export")

        self.btn_rename = QtWidgets.QPushButton(self.groupBox, clicked = lambda: self.click_rename())
        self.btn_rename.setGeometry(QtCore.QRect(250, 190, 101, 25))
        self.btn_rename.setFont(font)
        self.btn_rename.setObjectName("btn_rename")

        ####################################################################
        self.groupBox_az_integration = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_az_integration.setGeometry(QtCore.QRect(739, 140, 181, 161))
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
        self.btn_az_integrate = QtWidgets.QPushButton(self.groupBox_az_integration, clicked = lambda: self.click_integrate())
        self.btn_az_integrate.setGeometry(QtCore.QRect(40, 130, 89, 25))
        self.btn_az_integrate.setObjectName("btn_az_integrate")
        #####################################################################

        #####################################################################
        self.groupBox_rad_integration = QtWidgets.QGroupBox(self.tab_2)
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
        self.btn_rad_integrate = QtWidgets.QPushButton(self.groupBox_rad_integration, clicked = lambda: self.click_integrate_radial())
        self.btn_rad_integrate.setGeometry(QtCore.QRect(40, 130, 89, 25))
        self.btn_rad_integrate.setObjectName("btn_rad_integrate")
        self.lbl_chi_points = QtWidgets.QLabel(self.groupBox_rad_integration)
        self.lbl_chi_points.setGeometry(QtCore.QRect(30, 80, 131, 17))
        self.lbl_chi_points.setObjectName("lbl_chi_points")

        #################################################
        #plot test here...
        self.layout = QtWidgets.QWidget(self.tab)
        self.layout.setGeometry(QtCore.QRect(0, 0, 730,490))
        self.layout.setObjectName("layout")
        self.layout = QtWidgets.QVBoxLayout(self.layout)
        
        
        
        #self.figure = pyplot.figure(figsize=(1, 1))
        self.figure = pyplot.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.tab)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        #self.canvas.setParent(self.tab)
        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        #self.tab.installEventFilter(self)
        #self.toolbar.setOrientation(QtCore.Qt.Vertical)
        
        ################################################

        #################################################
        #plot 1d test here...
        self.layout2 = QtWidgets.QWidget(self.tab_2)
        self.layout2.setGeometry(QtCore.QRect(0, 0, 730,490))
        self.layout2.setObjectName("layout2")
        self.layout2 = QtWidgets.QVBoxLayout(self.layout2)
        
        self.figure2 = pyplot.figure()
        
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self.tab_2)
        self.layout2.addWidget(self.toolbar2)
        self.layout2.addWidget(self.canvas2)
        #self.figure2 = pyplot.figure(figsize=(7, 5))
        #self.canvas2.setParent(self.tab_2)
        
        #self.toolbar2.setOrientation(QtCore.Qt.Vertical)
        
        ################################################

        #####################################################################

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        

        self.monitor_002 = False
        self.mask = None
        self.bit_depth = None
        self.ai = None
        #self.show_warning_messagebox("The Y direct beam input box is now set to be consistant with pyFAI not FIT2d. For the LFP image and FIT2d use 2352 - Y direct beam. The best option is to always use a .poni file.")
        
        dlg = QtWidgets.QMessageBox(MainWindow)
        dlg.setWindowTitle("Use FIT2d mode?")
        dlg.setText("FIT2d uses flipped images, select Yes to set FIT2d mode and directly enter calibration values outputted from FIT2d. Otherwise select No and input a .poni file.")
        dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dlg.setIcon(QtWidgets.QMessageBox.Question)
        button = dlg.exec()
        if button == QtWidgets.QMessageBox.Yes:
            self.fit2d_mode = True
        else:
            self.fit2d_mode = False

        self.sample_data = {}
        self.background_data = {}
        self.processed_data = {}

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SWAN Plot"))
        self.grpBx_TM.setTitle(_translate("MainWindow", "TM"))
        self.lineEdit_bkg_TM.setText(_translate("MainWindow", "1.0"))
        self.lbl_bkg_TM.setText(_translate("MainWindow", "Background TM:"))
        self.lineEdit_smp_TM.setText(_translate("MainWindow", "1.0"))
        self.lbl_smp_TM.setText(_translate("MainWindow", "Sample TM:"))
        self.groupBox.setTitle(_translate("MainWindow", "WAXS"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Sample"))
        self.btn_import_smp.setText(_translate("MainWindow", "Import"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Background"))
        self.btn_import_bkg.setText(_translate("MainWindow", "Import"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Subtracted"))
        self.btn_import_subd.setText(_translate("MainWindow", "Import"))
        self.btn_show.setText(_translate("MainWindow", "Show"))
        self.btn_sum.setText(_translate("MainWindow", "Sum"))
        self.btn_average.setText(_translate("MainWindow", "Average"))
        self.groupBox_5.setTitle(_translate("MainWindow", "Remove outliers:"))
        self.groupBox_rot_img.setTitle(_translate("MainWindow", "Rotate image:"))
        self.lbl_rot_ang.setText(_translate("MainWindow", "Angle:"))
        #self.btn_get_rot_ang.setText(_translate("MainWindow", "Get angle"))
        self.btn_rot_img.setText(_translate("MainWindow", "Apply"))
        self.label.setText(_translate("MainWindow", "Radius:"))
        self.lineEdit_radius.setText(_translate("MainWindow", "2.0"))
        self.lineEdit_threshold.setText(_translate("MainWindow", "50"))
        self.label_2.setText(_translate("MainWindow", "Threshold:"))
        self.btn_remove_outliers.setText(_translate("MainWindow", "Apply to selected"))
        self.btn_2d_subtract.setText(_translate("MainWindow", "2D subtraction"))
        self.btn_2d_integrate.setText(_translate("MainWindow", "2D integrate"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "2D Tools"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "1D Tools"))
        self.btn_2d_subtract.setText(_translate("MainWindow", "2D subtract"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "2D Tools"))
        #self.Btn_show_1d.setText(_translate("MainWindow", "Plot selected"))
        self.btn_1D_subtract.setText(_translate("MainWindow", "1D Subtract"))
        #self.btn_integrate.setText(_translate("MainWindow", "Integrate"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "1D Tools"))
        self.groupBox_6.setTitle(_translate("MainWindow", "Integration (fit 2D format)  "))
        self.label_3.setText(_translate("MainWindow", "X pix. size [Microns]"))
        self.label_4.setText(_translate("MainWindow", "Y pix. size [Microns]"))
        self.label_5.setText(_translate("MainWindow", "S-D dist. [mm]"))
        self.label_6.setText(_translate("MainWindow", "Wavelength [Ang.]"))
        self.label_7.setText(_translate("MainWindow", "X dir. Beam [Pix.]"))
        self.label_8.setText(_translate("MainWindow", "Y dir. Beam [Pix.]"))
        self.label_9.setText(_translate("MainWindow", "Rot. ang. tilt plane [deg.]"))
        self.label_10.setText(_translate("MainWindow", "Ang of det. tilt in plane [deg.]"))
        self.label_11.setText(_translate("MainWindow", "Scale factor (1d data)"))
        self.btn_load_PONI.setText(_translate("MainWindow", "Load PONI"))
        self.btn_load_mask.setText(_translate("MainWindow", "Load mask"))
        self.btn_load_reject.setText(_translate("MainWindow", "Load reject"))
        self.btn_save_PONI.setText(_translate("MainWindow", "Save PONI"))
        self.btn_load_PSAXS.setText(_translate("MainWindow", "Load PSAXS.txt"))
        self.cb_002.setText(_translate("MainWindow", "monitor 002.txt"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_settings), _translate("MainWindow", "Settings"))
        self.btn_remove.setText(_translate("MainWindow", "Remove"))
        self.btn_export.setText(_translate("MainWindow", "Export"))
        self.btn_rename.setText(_translate("MainWindow", "Rename"))
        self.groupBox_az_integration.setTitle(_translate("MainWindow", "Azimuthal int. (I vs q)"))
        self.lbl_chi_range.setText(_translate("MainWindow", "chi range (degrees): "))
        self.lbl_q_bins.setText(_translate("MainWindow", "Number of bins: "))
        self.btn_az_integrate.setText(_translate("MainWindow", "Get I vs. q"))
        self.groupBox_rad_integration.setTitle(_translate("MainWindow", "Radial int. (I vs chi)  "))
        self.lbl_radial_range.setText(_translate("MainWindow", "Radial range (q [A^-1]):  "))
        self.btn_rad_integrate.setText(_translate("MainWindow", "Get I vs. chi"))
        self.lbl_chi_points.setText(_translate("MainWindow", "Number of points: "))

    ###################################################
    
    # def contextMenuEvent(self, event):
    #     contextMenu = QMenu(self)
    #     newAct = contextMenu.addAction("New")
    #     openAct = contextMenu.addAction("Open")
    #     quitAct = contextMenu.addAction("Quit")
    #     action = contextMenu.exec_(self.mapToGlobal(event.pos()))

    def get_data_dict(self, data_type):
        if data_type == "smp":
            return self.sample_data
        elif data_type == "bkg":
            return self.background_data
        elif data_type == "sub":
            return self.processed_data
            
    def click_sum_data(self):
        for data_type in ["smp", "bkg","sub"]:
            all_data = self.get_all_selected(data_type)
            if len(all_data) > 0:
                data_dim = self.check_selected_data_dim(*all_data)
                if data_dim == "two_dim":
                    new_data = Data_2d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name( all_data[0].name + "_sum_" + str(len(all_data)) + "_0", self.get_data_dict(data_type)),
                        self.sum_2D(all_data),
                        all_data[0].info
                        )
                    new_data.array = self.check_overflow_pix(new_data.array, new_data.name)
                    self.append_data(new_data, data_type)
                elif data_dim == "one_dim":
                    I, err = self.sum_1D(all_data)
                    new_data = Data_1d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name( all_data[0].name + "_sum_" + str(len(all_data)) + "_0", self.get_data_dict(data_type)), 
                        all_data[0].q, 
                        I, 
                        err, 
                        all_data[0].info
                        )
                    self.append_data(new_data, data_type)
                else:
                    # the other case is handled in the check_selected_data_dim function
                    pass
                    
        
    def click_average_data(self):
        for data_type in ["smp", "bkg","sub"]:
            all_data = self.get_all_selected(data_type)
            if len(all_data) > 0:
                data_dim = self.check_selected_data_dim(*all_data)
                if data_dim == "two_dim":
                    new_data = Data_2d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name( all_data[0].name + "_avg_" + str(len(all_data)) + "_0", self.get_data_dict(data_type)),
                        np.divide(self.sum_2D(all_data), len(all_data)),
                        all_data[0].info
                        )
                    self.append_data(new_data, data_type)
                elif data_dim == "one_dim":
                    I, err = self.avg_1D(all_data)
                    new_data = Data_1d(
                        all_data[0].dir,
                        all_data[0].ext,
                        append_name( all_data[0].name + "_avg_" + str(len(all_data)) + "_0", self.get_data_dict(data_type)), 
                        all_data[0].q, 
                        np.divide(I,len(all_data)) , 
                        np.divide(err,len(all_data)), 
                        all_data[0].info
                        )
                    self.append_data(new_data, data_type)
                else:
                    # the other case is handled in the check_selected_data_dim function
                    pass
    
    def check_selected_data_dim(self, *args):
        data_dim = None
        for x in args:
            if isinstance(x, Data_2d) and (data_dim == "two_dim" or data_dim is None) :
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

    def sum_2D(self, all_data):
        cur_sum = []
        for item in all_data:
            if len(cur_sum) == 0:
                cur_sum = item.array
            else:
                cur_sum = np.add(cur_sum,item.array, dtype='int64')
        return cur_sum


    def avg_1D(self,all_data):
        sum_I = []
        sum_err2 = []
        for item in all_data:
            if len(sum_I) == 0:
                sum_I = item.I
                sum_err2 = np.power(item.err,2)
            else:
                sum_I = np.add(sum_I,item.I)
                sum_err2 = np.add(sum_err2, np.power(item.err,2))
        # check the divide by N or N-1
        return np.divide(sum_I,len(all_data)), np.sqrt(np.divide(sum_err2,len(all_data)))
    
    def sum_1D(self, all_data):
        sum_I = []
        sum_err2 = []
        for item in all_data:
            if len(sum_I) == 0:
                sum_I = item.I
                sum_err2 = np.power(item.err,2)
            else:
                sum_I = np.add(sum_I,item.I)
                sum_err2 = np.add(sum_err2, np.power(item.err,2))
        return sum_I, np.sqrt(sum_err2)
    
    def onclick(self,event):
        '''
            This function has significant repeated code, the integration functions need to be made modular.
            double result = atan2(P3.y - P1.y, P3.x - P1.x) -
                atan2(P2.y - P1.y, P2.x - P1.x);
        '''
        
        if event.button == 3 and isinstance(self.get_plot_image_data(), Data_2d):
            
            self.ix, self.iy = event.xdata, event.ydata
            q = np.squeeze(self.ai.qFunction(self.iy, self.ix)) / 10
            chi = np.rad2deg(self.ai.chi(self.iy, self.ix))
            p1 = (float(self.lineEdit_X_dir.text()),float(self.lineEdit_Y_dir.text()))
            p3 = (self.ix,self.iy)
            len_p1_p3 = np.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
            p2 = (p3[0],p3[1] + len_p1_p3)
            angle = np.arctan2(p3[1] - p1[1], p3[0] - p1[0]) #- np.arctan2(p2[1]-p1[1], p2[0] - p1[0])
            menu = QMenu()
            menu.addAction(f'q is: {q:.5f} A^-1')
            menu.addAction(f'chi is: {chi:.2f} deg.')
            menu.addSeparator()
            set_angle_rot = menu.addAction('Set angle && rotate')
            menu.addSeparator()
            set_chi_min = menu.addAction('Set chi min')
            set_chi_max = menu.addAction('Set chi max')
            show_chi = menu.addAction('Show chi')
            menu.addSeparator()
            set_q_min = menu.addAction('Set q min')
            set_q_max = menu.addAction('Set q max')
            menu.addSeparator()
            azi_integrate = menu.addAction('get I vs Q')
            rad_integrate = menu.addAction('get I vs chi')
            action = menu.exec_(QtGui.QCursor.pos())
            
            if action == set_angle_rot:
                self.dsb_rot_ang.setValue( np.rad2deg(angle + np.pi / 2) )
                self.click_rot_img()
            elif action == set_chi_min:
                self.dsb_chi_start.setValue(chi)
                self.p1 = (self.ix,self.iy) 
            elif action == set_chi_max:
                self.dsb_chi_end.setValue(chi)
                self.p2 = (self.ix,self.iy) 
            elif action == set_q_min:
                self.dsb_start_q.setValue(q)
            elif action == set_q_max:
                self.dsb_end_q.setValue(q)
            elif action == show_chi:
                center = (float(self.lineEdit_X_dir.text()),float(self.lineEdit_Y_dir.text()))
                p1 = [self.p1, center]
                p2 = [self.p2,center]
                line1, = self.ax.plot(*zip(*p1), color="lime")
                line2, = self.ax.plot(*zip(*p2), color="lime")
                #point, = ax.plot(*center, marker="o")
                am1 = AngleAnnotation(center, p2[0], p1[0], text=r"$\chi$",textposition="outside", ax=self.ax, size=75, color="lime",text_kw=dict(color="lime")) #
                self.canvas.draw()
            elif action == azi_integrate:
                data = self.get_plot_image_data()
                if data.info["type"] == "smp":
                    normValue = float(self.lineEdit_smp_TM.text().strip())
                elif data.info["type"] == "bkg":    
                    normValue = float(self.lineEdit_bkg_TM.text().strip())
                else:
                    normValue = 1
                
                q, I, err = data.integrate_image(
                    self.ai,
                    self.sb_q_bins.value(),
                    self.dsb_chi_start.value(),
                    self.dsb_chi_end.value(),
                    self.mask,
                    normValue
                )
                    
                
                new_data = Data_1d(
                    data.dir,
                    "dat",
                    "1D~" + data.name.split("~")[1],
                    q,
                    I,
                    err,
                    {"type": data.info["type"]}
                )
                self.append_data(new_data, new_data.info['type'])

            elif action == rad_integrate:
                item = self.get_plot_image_data()
                chi, I = self.integrate_radial(item)
                if len(I) < 2:
                    self.show_warning_messagebox("Warning, length of data is less than 2!!")
                    return
                data = Data_1d_az(
                item.dir,
                "dat",
                "1Daz~" + item.name.split("~")[1],
                chi,
                I,
                {"type":item.info["type"]}
                )
                self.append_data(data, data.info["type"])
                self.clear_lists()

            #print(p3, " this is p3" )
            #print(p2, " this is p2" )
            #print(np.rad2deg(angle + np.pi / 2))
    

    def no_data_selected(self):
        if (not self.listWidget_smp.selectedItems() and 
        not self.listWidget_bkg.selectedItems() and
        not self.listWidget_processed.selectedItems()):
            return True

    def click_rot_img(self):
        if self.ai is None:
            self.no_ai_found_error()
        else:
            #data = self.get_first_sel()
            data = self.get_plot_image_data()
            if isinstance(data,Data_2d):
                rotd_img = data.rotate(self.dsb_rot_ang.value())
                #print(rotd_img)
                name = "2d_rot_" + data.name.split('~')[1]
                self.append_data(Data_2d_rot(data.dir, data.ext, name, rotd_img, data.info), data.info["type"])
                self.set_plot_image_name(name,data.info["type"])
                self.plot_2D(rotd_img,name)
                self.clear_lists()

    def click_load_reject(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(MainWindow, 
        "Select reject file", "", " REJECT (REJECT.dat);;All Files (*)")
        mask_data = np.loadtxt(fname, usecols=(0, 1),comments='#')
        #print(self.listWidget_smp.count())
        if self.listWidget_smp.count() < 1:
            self.show_warning_messagebox("No data loaded, load a sample image file first.")
            return
        for index in range(self.listWidget_smp.count()):
            item = self.listWidget_smp.item(index).text()
            data = self.sample_data[item]
            if isinstance(data,Data_2d):
                if self.mask is None:
                    self.mask = make_reject_mask(np.zeros(np.shape(data.array)), mask_data)
                    return
                else:
                    self.mask = combine_masks(make_reject_mask(np.zeros(np.shape(data.array)), mask_data), self.mask)
                    return    
        self.show_warning_messagebox("No image files loaded. Load an image file and try again.")
        
        
    def click_load_mask(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(MainWindow, 
        "Select a mask file", "", " tif Image (*.tif);;edf Image (*.edf);;All Files (*)")
        
        self.mask = fabio.open(fname).data

    def mask_pix_zero(self,image):
        inv_mask = np.abs(1-self.mask)
        masked_image = np.multiply(image,inv_mask)
        return masked_image

    def mask_pix_nan(self,image):
        #inv_mask = np.abs(1-self.mask)
        image = image.astype(float)
        image[self.mask == 1] = np.nan
        return image

    
    def click_load_PSAXS(self):
        plankC = float(4.135667696e-15)
        speedLightC = float(299_792_458)

        fname, _ = QtWidgets.QFileDialog.getOpenFileName(MainWindow, "Select PSAXSpar.txt file", "", "txt (*.txt);;All Files (*)")
        if fname and fname != "":
            Fit2dDic = self.readSAXSpar(fname)

            self.ai = azimuthalIntegrator.AzimuthalIntegrator(detector=Fit2dDic['detector'],wavelength=plankC * speedLightC / 1000 / Fit2dDic['energy'])
            self.ai.setFit2D(
            Fit2dDic["directBeam"],
            Fit2dDic["beamX"],
            Fit2dDic["beamY"],
            Fit2dDic["tilt"],
            Fit2dDic["tiltPlanRotation"]
            )
            del Fit2dDic
            Fit2dDic = self.ai.getFit2D()
            
            # fill out line entrys
            self.lineEdit_X.setText(str(Fit2dDic["pixelX"])[0:12])
            self.lineEdit_Y.setText(str(Fit2dDic["pixelY"])[0:12])
            self.lineEdit_SD.setText(str(Fit2dDic["directDist"])[0:12])   # .text(Fit2dDic["directDist"])
            self.lineEdit_wavelength.setText(str(10_000_000_000 * self.ai.get_wavelength())[0:12])
            self.lineEdit_X_dir.setText(str(Fit2dDic["centerX"])[0:12])
            self.lineEdit_Y_dir.setText(str(Fit2dDic["centerY"])[0:12])
            self.lineEdit_rotAngTiltPlane.setText(str(Fit2dDic["tiltPlanRotation"])[0:12])
            self.lineEdit_angDetTilt.setText(str(Fit2dDic["tilt"])[0:12])
    
    def check002(self, checked):
        if checked:
            self.monitor_002 = True
            #print(self.monitor_002)
        else:
            self.monitor_002 = False
            #print(self.monitor_002)

    def click_rename(self):
        if len(self.listWidget_smp.selectedIndexes()) != 0:
            for item in self.listWidget_smp.selectedItems():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(MainWindow, 'Rename Dialog', 'Change name from ' + old_name.split("~")[1] + ' to:')
                if ok:
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.sample_data[old_name].name = new_name
                    self.sample_data[new_name] = self.sample_data[old_name]
                    del self.sample_data[old_name]
        
        if len(self.listWidget_bkg.selectedIndexes()) != 0:
            for item in self.listWidget_bkg.selectedIndexes():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(MainWindow, 'Rename Dialog', 'Change name from ' + old_name.split("~")[1] + ' to:')
                if ok:
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.background_data[old_name].name = new_name
                    self.background_data[new_name] = self.background_data[old_name]
                    del self.background_data[old_name]
        
        if len(self.listWidget_bkg.selectedIndexes()) != 0:        
            for item in self.listWidget_bkg.selectedIndexes():
                old_name = item.text()
                new_name, ok = QInputDialog.getText(MainWindow, 'Rename Dialog', 'Change name from ' + old_name.split("~")[1] + ' to:')
                if ok:
                    new_name = old_name.split("~")[0] + "~" + new_name
                    item.setText(new_name)
                    self.processed_data[old_name].name = new_name
                    self.processed_data[new_name] = self.background_data[old_name]
                    del self.processed_data[old_name]
        self.clear_lists()  
    
    
    
    def click_integrate_radial(self):
        if self.ai is None:
            self.no_ai_found_error()
        else:
            self.figure2.clear()
            ax2 =  self.figure2.add_subplot(111)
            for item in self.get_all_selected():
                if isinstance(item, Data_2d):
                    chi, I = self.integrate_radial(item)
                    if len(I) < 2:
                        self.show_warning_messagebox("Warning, length of data is less than 2!!")
                        return
                    data = Data_1d_az(
                    item.dir,
                    "dat",
                    "1Daz~" + item.name.split("~")[1],
                    chi,
                    I,
                    {"type":item.info["type"]}
                    )
                    self.append_data(data, data.info["type"])
                    self.plot_1D_az(
                        ax2,
                        data.chi,
                        data.I,
                        data.name.split("~")[1]
                    )
            self.canvas2.draw()
            self.clear_lists()

                    #self.plot_2Daz(data.data) # put plotting here

    def integrate_radial(self,data):
        if data.info["type"] == "smp":
            normValue = float(self.lineEdit_smp_TM.text().strip())
        elif data.info["type"] == "bkg":    
            normValue = float(self.lineEdit_bkg_TM.text().strip())
        else:
            normValue = 1

        chi, I = self.ai.integrate_radial(
            data.array,
            self.sb_chi_points.value(),
            npt_rad=1000,
            correctSolidAngle=True,
            radial_range=(self.dsb_start_q.value(),self.dsb_end_q.value()), 
            azimuth_range=None,
            mask=self.mask,
            dummy=None, 
            delta_dummy=None, 
            polarization_factor=None, 
            dark=None, 
            flat=None, 
            method='cython', 
            unit='chi_deg', 
            radial_unit='q_A^-1',
            normalization_factor=normValue
            )
        return chi, I
   
   
    def click_integrate_2D(self):
        if self.ai is None:
            self.no_ai_found_error()
        else:
            for item in self.get_all_selected():
                if isinstance(item, Data_2d):
                    az_image = item.integrate_2D(self.ai,self.mask)
                    data = Data_2d_az(
                        item.dir,
                        item.ext,
                        "2Daz~" + item.name.split("~")[1],
                        az_image,
                        {"type":item.info["type"],"dim": "2D"}
                    )
                    self.append_data(data, data.info["type"])
                    self.plot_2Daz(data.array, data.name)
        
            return data    
    
    def click_1D_subtract(self):
        if len(self.listWidget_smp.selectedIndexes()) < 1:
            self.show_warning_messagebox("No sample selected.")
            return

        if len(self.listWidget_bkg.selectedIndexes()) < 1:
            self.show_warning_messagebox("No background selected.")
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1 and len(self.listWidget_bkg.selectedIndexes()) != len(self.listWidget_smp.selectedIndexes()):
            self.show_warning_messagebox('number of selected background and samples different. Returning.')
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1:
            self.show_warning_messagebox('More than one background selected, one background per sample mode.')

        for item in self.get_all_selected(): # check that all selected are 1D data
            if not isinstance(item, Data_1d):
                self.show_warning_messagebox('A data set is not 1 dimensional.')
                return

        #except:
        #    self.show_warning_messagebox("No background selected.")
        #    return
        if len(self.listWidget_bkg.selectedIndexes()) == 1:
            bkg_name = self.listWidget_bkg.selectedIndexes()[0].data()
            bkg_data = self.background_data[bkg_name].I
            bkg_err = self.background_data[bkg_name].err
            
            for index in self.listWidget_smp.selectedIndexes():
                part1 = np.divide(self.sample_data[index.data()].I, float(self.lineEdit_smp_TM.text()))
                part2 = np.divide(bkg_data, float(self.lineEdit_bkg_TM.text()))
                errP1 = np.divide(self.sample_data[index.data()].err, float(self.lineEdit_smp_TM.text()))
                errP2 = np.divide(bkg_err, float(self.lineEdit_bkg_TM.text()))

                name = self.sample_data[index.data()].name
                name = "1D~" + "subd_" + name.split("~")[1]
                name = append_name(name,self.processed_data)
                out = Data_1d(
                    self.sample_data[index.data()].dir,
                    "dat",
                    name,
                    self.sample_data[index.data()].q,
                    np.subtract(part1,part2),
                    np.sqrt(np.add(np.power(errP1, 2), np.power(errP2, 2))),
                    {"type": "sub","dim": "1D"}
                )
                
                self.processed_data[out.name] = out
                self.listWidget_processed.addItem(out.name)
         

        else:
            for count, index in enumerate(self.listWidget_smp.selectedIndexes()):
                
                bkg_name = self.listWidget_bkg.selectedIndexes()[count].data()
                bkg_data = self.background_data[bkg_name].I
                bkg_err = self.background_data[bkg_name].err
                part1 = np.divide(self.sample_data[index.data()].I, float(self.lineEdit_smp_TM.text()))
                part2 = np.divide(bkg_data, float(self.lineEdit_bkg_TM.text()))
                errP1 = np.divide(self.sample_data[index.data()].err, float(self.lineEdit_smp_TM.text()))
                errP2 = np.divide(bkg_err, float(self.lineEdit_bkg_TM.text()))

                
                name = self.sample_data[index.data()].name
                name = "1D~" + "subd_" + name.split("~")[1]
                name = append_name(name,self.processed_data)
                out = Data_1d(
                    self.sample_data[index.data()].dir,
                    "dat",
                    name,
                    self.sample_data[index.data()].q,
                    np.subtract(part1,part2),
                    np.sqrt(np.add(np.power(errP1, 2), np.power(errP2, 2))),
                    {"type": "sub","dim": "1D"}
                )
                
                self.processed_data[out.name] = out
                self.listWidget_processed.addItem(out.name)
        self.clear_lists()      

    def no_ai_found_error(self):
        self.show_warning_messagebox("Scattering geometry information is not found, input a .poni file or information from fit 2d", title="Error")
    
    def click_integrate(self):
        if self.ai is None:
            self.no_ai_found_error()
        else:
            self.figure2.clear()
            ax2 =  self.figure2.add_subplot(111)
            for data in self.get_all_selected():
                if isinstance(data,Data_2d) and self.ai:
                    
                    if data.info["type"] == "smp":
                        normValue = float(self.lineEdit_smp_TM.text().strip())
                    elif data.info["type"] == "bkg":    
                        normValue = float(self.lineEdit_bkg_TM.text().strip())
                    else:
                        normValue = 1
                    if self.monitor_002:
                        normValue *= data.info["civi"]
                    
                    #count =0
                    #while count < 1000:

                    q, I, err = data.integrate_image(
                        self.ai,
                        self.sb_q_bins.value(),
                        self.dsb_chi_start.value(),
                        self.dsb_chi_end.value(),
                        self.mask,
                        normValue / self.dsb_scale_factor.value()
                    )
                        #count += 1

                    new_data = Data_1d(
                        data.dir,
                        "dat",
                        "1D~" + data.name.split("~")[1],
                        q,
                        I,
                        err,
                        {"type": data.info["type"]}
                    )
                    self.append_data(new_data, new_data.info['type'])
                    
                    self.plot_1D_1D_data( 
                        ax2, 
                        new_data.q, 
                        new_data.I, new_data.err, 
                        new_data.name.split("~")[1]
                        )

            self.canvas2.draw()
            self.clear_lists()                             

    def click_load_PONI(self):
        if self.fit2d_mode:
            self.show_warning_messagebox("FIT2d mode is currently set so the image is flipped compared to .poni orientation. Please restart and set no to FIT2d option or proceed with care!")
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(MainWindow, "Select PONI file", "", "PONI (*.poni);;All Files (*)")
        if fname and fname != "":
            self.ai = pyFAI.load(fname)
            Fit2dDic = self.ai.getFit2D()
            #print(Fit2dDic)
            self.lineEdit_X.setText(str(Fit2dDic["pixelX"])[0:12])
            self.lineEdit_Y.setText(str(Fit2dDic["pixelY"])[0:12])
            self.lineEdit_SD.setText(str(Fit2dDic["directDist"])[0:12])   # .text(Fit2dDic["directDist"])
            self.lineEdit_wavelength.setText(str(10_000_000_000 * self.ai.get_wavelength())[0:12])
            self.lineEdit_X_dir.setText(str(Fit2dDic["centerX"])[0:12])
            # invert Y below ###############################################
            self.lineEdit_Y_dir.setText(str(Fit2dDic["centerY"])[0:12]) # 2352 - 
            #################################################################
            self.lineEdit_rotAngTiltPlane.setText(str(Fit2dDic["tiltPlanRotation"])[0:12])
            self.lineEdit_angDetTilt.setText(str(Fit2dDic["tilt"])[0:12])

    def click_save_PONI(self):
        
        plankC = float(4.135667696e-15)
        speedLightC = float(299_792_458)

        Fit2dDic = {}
        Fit2dDic["pixelX"] = float(self.lineEdit_X.text().strip())
        Fit2dDic["pixelY"] = float(self.lineEdit_X.text().strip())
        Fit2dDic["directDist"] = float(self.lineEdit_SD.text().strip())
        Fit2dDic["energy"] = plankC * speedLightC / 1000 / float(self.lineEdit_wavelength.text().strip()) / 10_000_000_000
        Fit2dDic["centerX"] = float(self.lineEdit_X_dir.text().strip())
        Fit2dDic["centerY"] = float(self.lineEdit_Y_dir.text().strip())
        Fit2dDic["tiltPlanRotation"] = float(self.lineEdit_rotAngTiltPlane.text().strip())
        Fit2dDic["tilt"] = float(self.lineEdit_angDetTilt.text().strip())
        
        self.ai = azimuthalIntegrator.AzimuthalIntegrator(wavelength=float(self.lineEdit_wavelength.text().strip()) / 10_000_000_000)
        
        self.ai.setFit2D(
        Fit2dDic["directDist"],
        Fit2dDic["centerX"],
        Fit2dDic["centerY"],    # 2352 - 
        Fit2dDic["tilt"],
        Fit2dDic["tiltPlanRotation"],
        Fit2dDic["pixelX"],
        Fit2dDic["pixelY"]
        )

        fname, _ = QtWidgets.QFileDialog.getSaveFileName(MainWindow, "Poni file save name", "", "PONI (*.poni);;All Files (*)")

        self.ai.write(fname)

        #print(self.ai)
        #print(self.ai.getFit2D())
  
    def get_first_sel(self):
        try:
            if len(self.listWidget_smp.selectedItems()) != 0:
                #self.listWidget_smp.selectedIndexes()[0].data():
                item = self.listWidget_smp.selectedIndexes()[0].data()
                data = self.sample_data[item]
                #if isinstance(data, Data_2d) or isinstance(data, Data_2d_az):
                return data
            if len(self.listWidget_bkg.selectedItems())  != 0:
                item = self.listWidget_bkg.selectedIndexes()[0].data()
                data = self.background_data[item]
                #if isinstance(data, Data_2d) or isinstance(data, Data_2d_az): 
                return data
            if len(self.listWidget_processed.selectedIndexes()) != 0:
                item = self.listWidget_processed.selectedIndexes()[0].data()
                data = self.processed_data[item]
                #if isinstance(data, Data_2d) or isinstance(data, Data_2d_az):
                return data
        except:
            data_2d = None
            self.show_warning_messagebox("No data selected.")
            return data_2d
    
    def get_all_selected(self, data_type="all"):
        all_data = []
        if len(self.listWidget_smp.selectedIndexes()) != 0 and (data_type == "all" or data_type == "smp"):
            for item in self.listWidget_smp.selectedIndexes():
                all_data.append(self.sample_data[item.data()])
        if len(self.listWidget_bkg.selectedIndexes()) != 0 and (data_type == "all" or data_type == "bkg"):
            for item in self.listWidget_bkg.selectedIndexes():
                all_data.append(self.background_data[item.data()])
        if len(self.listWidget_processed.selectedIndexes()) != 0 and (data_type == "all" or data_type == "sub"):
            for item in self.listWidget_processed.selectedIndexes():
                all_data.append(self.processed_data[item.data()])
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

        while len(self.listWidget_processed.selectedIndexes()) > 0:
            item = self.listWidget_processed.selectedIndexes()[0]
            del self.processed_data[item.data()]
            self.listWidget_processed.takeItem(item.row())

    def set_plot_image_name(self, name, img_type):
        self.plt_info = (name, img_type)
        #print(self.plt_info[0])
        #print(self.plt_info[1])

    def get_plot_image_data(self):
        #print( self.plt_info[1])
        if self.plt_info[1] == "smp":
            #print(self.sample_data[self.plt_info[0]])
            return self.sample_data[self.plt_info[0]]
        elif self.plt_info[1] == "bkg":
            return self.background_data[self.plt_info[0]]
        else:
            return self.processed_data[self.plt_info[0]]
    
    def click_show_data(self):
        data = self.get_first_sel()
        if (isinstance(data,Data_2d) or 
            isinstance(data,Data_2d_az) or 
            isinstance(data,Data_2d_rot)):

            self.set_plot_image_name(data.name, data.info['type'])
            #print(self.plt_info[0])
            self.tabWidget.setCurrentWidget(self.tab)
            self.show_image()
        elif isinstance(data,Data_1d) or isinstance(data,Data_1d_az):
            self.tabWidget.setCurrentWidget(self.tab_2)
            self.plot_1D()
    
    def show_image(self):
        data_2d = self.get_first_sel()
        if isinstance(data_2d, Data_2d):
            image = data_2d.array
            #try:
            if image is not None:
                if self.mask is not None:
                    image = self.mask_pix_zero(image)
                self.plot_2D(image,data_2d.name)
                self.clear_lists()
            #except:
            #    self.show_warning_messagebox("Image did not pass.")
        elif isinstance(data_2d, Data_2d_az):
            self.plot_2Daz(data_2d.array,data_2d.name)
            self.clear_lists()

        elif isinstance(data_2d,Data_2d_rot):
            self.plot_2D(data_2d.array,data_2d.name)
            self.clear_lists()
        
        elif isinstance(data_2d, Data_1d):
            self.show_warning_messagebox("Selected is one dimensional data.")
            self.clear_lists()
   
    def clear_lists(self):
        self.listWidget_smp.clearSelection()
        self.listWidget_bkg.clearSelection()
        self.listWidget_processed.clearSelection()
        
    
    def check_overflow_pix(self, array, name):
        num_high_pix = self.count_overflow_pix(array.copy())
        print(num_high_pix)
        print(array.dtype)
        print(np.max(array))
        if num_high_pix > 0 and self.bit_depth < 32:
            dlg = QtWidgets.QMessageBox(MainWindow)
            dlg.setWindowTitle("Pixel(s) overflowing, convert to higher bit depth")
            dlg.setText(str(num_high_pix) + " saturated pixels in image " + name + ", select yes to set image type to " + str(2*self.bit_depth) +" bit or no to set satureated values to " + str(2**self.bit_depth - 1))
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
            self.show_warning_messagebox(str(num_high_pix) + " saturated pixels in image, as this is a 32 bit image all saturated pixels will be set to" + str(2**self.bit_depth -1))
            return self.set_overflow_pix_saturated(array.copy())
        else:
            return array

    def set_overflow_pix_saturated(self,a):
        overflow_pix = np.squeeze(np.where(a > 2**self.bit_depth - 1))
        a[overflow_pix[0], overflow_pix[1]] = 2**self.bit_depth - 1
        return np.array(a) #, dtype = "int"+str(self.bit_depth))

    def count_overflow_pix(self, a):
        overflow_pix = np.squeeze(np.where(a >= 2**self.bit_depth - 1))
        a.fill(0)
        a[overflow_pix[0], overflow_pix[1]] = 1
        return np.sum(a)

    def export_single_image(self,data):
        if self.bit_depth == 32:
            data.array = data.array.astype('int32')
        elif self.bit_depth == 16:
            data.array = data.array.astype('int16')
        elif self.bit_depth == 8:
            data.array = data.array.astype('int8')

        path = os.path.join(data.dir, data.name.split("~")[1] + '.' + 'tif') # always save as tif
        if os.path.exists(path):
            old_path = path
            path = self.append_file(path)
            self.show_warning_messagebox('File ' + old_path + ' found, saving to ' + path)
        tifffile.imwrite(path, data.array, data.array.dtype)
        self.clear_lists()

    def export_single_dat(self, data):
        path = os.path.join(data.dir, data.name.split("~")[1] + '.' + data.ext)
        if os.path.exists(path):
            old_path = path
            path = self.append_file(path)
            self.show_warning_messagebox('File ' + old_path + ' found, saving to ' + path)
        np.savetxt(path, np.transpose([data.q,data.I,data.err]), fmt='%1.6e', delimiter='    ')
    
    def click_export(self):

        for data in self.get_all_selected():
            if data != []:
                if isinstance(data, Data_2d):
                    self.export_single_image(data)
                elif isinstance(data, Data_1d_az):
                    pass

                elif isinstance(data,Data_1d):
                    self.export_single_dat(data)

    def export_1d_az(self, data):
        path = os.path.join(data.dir, data.name.split("~")[1] + '_azimuthal_' + '.' + data.ext)
        if os.path.exists(path):
            old_path = path
            path = self.append_file(path)
            self.show_warning_messagebox('File ' + old_path + ' found, saving to ' + path)
        np.savetxt(path, np.transpose([data.chi,data.I]), fmt='%1.6e', delimiter='    ')

    def append_file(self,path):
        counter = 0
        basePath = os.path.dirname(path)
        ext = os.path.basename(path).split('.')[-1]
        name = Path(path).stem
        if os.path.exists(path):
            #check if number suffix already:
            suff = name.split("_")[-1]
            
            if suff.isnumeric():
                counter = int(suff)
                pref = name.split("_")[:-1]
                pref = ''.join(map(str,pref))
            else: 
                counter = 0
                pref = name

            while True:
                counter += 1
                
                newName = pref + '_' + str(counter)
                newPath = os.path.join(basePath, newName + '.' + ext)
                if os.path.exists(newPath):
                    continue
                else:
                    path = newPath
                    break
        return path
    
    def click_rem_outliers(self):

        data_2d_all = self.get_all_selected()

        for data_2d in data_2d_all:
            if not isinstance(data_2d, Data_2d):
                data_2d_all.remove(data_2d)

        if not data_2d_all:
            self.show_warning_messagebox("No 2d data selected.")

        for data_2d in data_2d_all:
            im_corr = data_2d.remove_outliers(
                float(self.lineEdit_radius.text()), 
                float(self.lineEdit_threshold.text())
            )
            
            self.plot_2D(im_corr,"2D~" + "OLrm_" + data_2d.name.split("~")[1])

            corr_data = {'dir':data_2d.dir,'ext':data_2d.ext ,'name': "2D~" + "OLrm_" + data_2d.name.split("~")[1],'array': im_corr}

            self.append_data(
                Data_2d(
                    corr_data['dir'],
                    corr_data['ext'],
                    corr_data['name'],
                    corr_data['array'],
                    data_2d.info["type"]
                ),
                data_2d.info["type"]
            )
            
        self.clear_lists()

    def plot_1D_1D_data(self, axis, q, I, err, label):
        axis.errorbar(q,I,yerr=err,label=label)
        #plt.plot(item.q,item.I,label=item.name)
        axis.set_xscale('log')
        axis.set_yscale('log')
        axis.set_xlabel('q [Ang.^-1]')
        axis.set_ylabel('I(q) [arb. units]')
        axis.legend(fontsize=9)

    def plot_1D_az(self, axis, chi, I, label):
        axis.plot(chi,I,label=label)
        axis.set_xscale('linear')
        axis.set_yscale('linear')
        axis.set_xlabel('chi [deg.]')
        axis.set_ylabel('I(q) [arb. units]')
        axis.legend(fontsize=9)

    def plot_1D(self):
        # clearing old figure
        #self.tabWidget.setCurrentIndex(1)
        self.figure2.clear()
        
        # create an axis
        ax2 =  self.figure2.add_subplot(111)
        #self.get_scale_max(image)
        # plot data
        for item in self.get_all_selected():
            if isinstance(item,Data_1d):
                self.plot_1D_1D_data(
                    ax2, 
                    item.q, 
                    item.I, 
                    item.err, 
                    item.name.split("~")[1]
                    )
                
            elif isinstance(item, Data_1d_az):
                self.plot_1D_az(
                    ax2, 
                    item.chi, 
                    item.I, 
                    item.name.split("~")[1]
                    )
                
        #ax.errorbar(image,cmap="turbo",vmin=0,vmax=self.scale_max) #,norm="log",vmin=0,vmax=self.scale_max
        #ax.set_position([0.2, 0.2, 0.6, 0.6])
        # refresh canvas
        #self.figure.tight_layout(pad=0.4, w_pad=20, h_pad=1.0)
        
        #
        #self.figure2.tight_layout()
        self.canvas2.draw()
        self.clear_lists()
    
    def plot_2Daz(self, image, title):
        self.figure.clear()
        
        # create an axis
        ax = self.figure.add_subplot(111)
        #self.get_scale_max(image)
        # plot data
        colornorm = SymLogNorm(1, base=10,
                           vmin=np.nanmin(image[0]),
                           vmax=np.nanmax(image[0]))      
        #colornorm = 'linear'
        ax.imshow(image[0],cmap="inferno",extent=[image[1][0].min(),image[1].max(),image[2].min(),image[2].max()],norm=colornorm,origin='lower') #,vmin=0,vmax=self.scale_max,origin='lower') #,norm="log",vmin=0,vmax=self.scale_max
        ax.set_title(title)
        ax.set_aspect('auto')
        ax.set_xlabel('q [Ang. ^-1]')
        ax.set_ylabel('azi. ang. chi (deg.)')
        #,extent=[image[1][0],image[1][-1],image[2][0],image[2][-1]],
        #ax.set_xticks(image[1])
        #ax.set_yticks(image[2])
        #ax.set_position([0.2, 0.2, 0.6, 0.6])
        # refresh canvas
        #self.figure.tight_layout(pad=0.4, w_pad=20, h_pad=1.0)
        #self.figure.tight_layout()
        #self.figure.
        self.canvas.draw()
    '''
    def bin_ndarray(self,ndarray, new_shape, operation='mean'):
    
        if not operation.lower() in ['sum', 'mean', 'average', 'avg']:
            raise ValueError("Operation {} not supported.".format(operation))
        if ndarray.ndim != len(new_shape):
            raise ValueError("Shape mismatch: {} -> {}".format(ndarray.shape,
                                                            new_shape))
        compression_pairs = [(d, c//d) for d, c in zip(new_shape,
                                                    ndarray.shape)]
        flattened = [l for p in compression_pairs for l in p]
        ndarray = ndarray.reshape(flattened)
        for i in range(len(new_shape)):
            if operation.lower() == "sum":
                ndarray = ndarray.sum(-1*(i+1))
            elif operation.lower() in ["mean", "average", "avg"]:
                ndarray = ndarray.mean(-1*(i+1))
        return ndarray
    '''

    def plot_2D(self,image,title):
        # clearing old figure
        
        #image = self.bin_ndarray(image, (2,3))

        #main_frame, sub_frame = dectris.albula.display(dectris.albula.DImage(image))
        self.figure.clear()
        
        colornorm = SymLogNorm(1, base=10,
                           vmin=np.nanmin(image),
                           vmax=np.nanmax(image))
        #colornorm = 'linear'
        
        # create an axis
        self.ax = self.figure.add_subplot(111)
        self.get_scale_max(image)
        # plot data
        self.ax.imshow(image,cmap="inferno",norm=colornorm) #,vmin=0,vmax=self.scale_max) #,norm="log",vmin=0,vmax=self.scale_max
        self.ax.set_title(title)
        #ax.set_position([0.2, 0.2, 0.6, 0.6])
        # refresh canvas
        #self.figure.tight_layout(pad=0.4, w_pad=20, h_pad=1.0)
        #self.figure.tight_layout()
        self.canvas.draw()
         
    ##########################################
    
    def get_scale_max(self,image):
        maxindex = np.amax(image)
        meanindex = np.mean(image)
        
        if maxindex > 10*meanindex:
            self.scale_max = int(meanindex*5)
        else:
            self.scale_max = int(maxindex)
    
    def append_data(self, data, data_type):
        if data_type == "smp":
            data.name = append_name(data.name, self.sample_data)
            self.sample_data[data.name] = data
            self.listWidget_smp.addItem(self.sample_data[data.name].name)
            #self.listWidget_smp.setCurrentItem(QtWidgets.QListWidgetItem(self.sample_data[data.name].name))
        elif data_type == "bkg":
            data.name = append_name(data.name, self.background_data)
            self.background_data[data.name] = data
            self.listWidget_bkg.addItem(self.background_data[data.name].name)
        elif data_type == "sub":
            data.name = append_name(data.name, self.processed_data)
            self.processed_data[data.name] = data
            self.listWidget_processed.addItem(self.processed_data[data.name].name)
    
    def set_bit_depth(self,array):
        print(array.dtype)
        if array.dtype == 'uint8' or array.dtype == 'int8':
            self.bit_depth = 8
        elif array.dtype == 'uint16' or array.dtype == 'int16':
            self.bit_depth = 16
        elif array.dtype == 'uint32' or array.dtype == 'int32':
            self.bit_depth = 32
        else:
            self.show_warning_messagebox('Image appears to be neither a 8, 16, or 32 bit image. This is currently not supported.')

    def init_image_import(self, array):
        if self.bit_depth is None:
            self.set_bit_depth(array)
            self.show_warning_messagebox("Image bit depth of " + str(self.bit_depth) + " found and will be used for writing and manipulating images, please be aware of bit overflow\nMax value for images is " + str(2**self.bit_depth - 1))

        if self.saturated_pix_mask is False:
            self.mask = make_saturated_mask(array, self.bit_depth)
            self.show_warning_messagebox("Masked " + str(np.sum(self.mask)) + " saturated pixels which had values of 2^" + str(self.bit_depth) +"-1")
            self.saturated_pix_mask = True

    
    def import_data(self,data_type):
        #open file dialog returns a tuple
        fnames, _ = QtWidgets.QFileDialog.getOpenFileNames(MainWindow, "Select multiple files", "", " tif Image (*.tif);;h5 Image (*master.h5);;1D data (*.dat);;All Files (*)")
        
        if fnames and fnames != "":
            for item in fnames:
                if item.split('.')[-1] == "tif":
                    data = Data_2d(
                        os.path.dirname(item),
                        os.path.basename(item).split('.')[-1],
                        "2D~" + Path(item).stem,
                        tifffile.imread(item),
                        {"type": data_type}
                    ) 

                    if self.fit2d_mode:
                        data.array = np.flipud(data.array)
                    
                    self.plot_2D(data.array,data.name)
                    self.init_image_import(data.array.copy())

                    self.set_plot_image_name(data.name,data.info['type'])
                    self.append_data(data, data_type)

                if item.split('.')[-1] == "h5":
                    if self.monitor_002:
                            civi, rigi, expTime = self.readHeaderFile(os.path.dirname(item),Path(item).stem[0:3])
                    
                    imgData = fabio.open(item)
                    for num in range(imgData.nframes):
                        dict = {
                            'dir' : os.path.dirname(item),
                            'ext' : os.path.basename(item).split('.')[-1],
                            'name' : '2D~' + Path(item).stem + '_' + str(num),
                            'info' : {"type": data_type}
                        }
                        if imgData.nframes > 1:
                            dict['data'] = imgData.getframe(num).data
                            
                        else:
                            dict['data'] = imgData.data
                        if self.monitor_002:
                            dict['info']['civi'] = civi[num]
                            dict['info']['rigi'] = rigi[num]
                            dict['info']['expTime'] = expTime[num]

                        data = Data_2d(
                            dict['dir'],
                            dict['ext'],
                            dict['name'],
                            dict['data'],
                            dict['info']
                        )
                        if self.fit2d_mode:
                            data.array = np.flipud(data.array)
                        self.append_data(data,data_type)
                        self.init_image_import(dict['data'].copy())
                        # if self.bit_depth is None:
                        #     self.set_bit_depth(data.array)

                        # if self.saturated_pix_mask is False:
                        #     self.mask = make_saturated_mask(dict['data'].copy())
                        #     self.show_warning_messagebox("Saturated pixels with value 2^32-1 are masked.")
                        #     self.saturated_pix_mask = True
                    self.plot_2D(data.array,data.name)
                    self.set_plot_image_name(data.name,data.info['type'])
                    

                elif item.split('.')[-1] == "dat":
                    try:
                        raw_data = np.loadtxt(item, usecols=(0,1,2))
                        #print(raw_data[:,1])
                        data = Data_1d(
                            os.path.dirname(item),
                            os.path.basename(item).split('.')[-1],
                            "1D~" + Path(item).stem,
                            raw_data[:,0],
                            raw_data[:,1],
                            {"type": data_type},
                            err = raw_data[:,2]
                                                )
                        self.append_data(data,data_type)
                    except:
                        self.show_warning_messagebox("There is likely an issue with the header.")

        self.clear_lists()

    def show_warning_messagebox(self,text, title = "Warning"):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        # setting message for Message Box
        msg.setText(text)

        # setting Message box window title
        msg.setWindowTitle(title)

        # declaring buttons on Message Box
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        # start the app
        retval = msg.exec_()
    
    
    def subtract_2D(self):
        #try:
        
        if len(self.listWidget_smp.selectedIndexes()) < 1:
            self.show_warning_messagebox("No sample selected.", title="Error")
            return

        if len(self.listWidget_bkg.selectedIndexes()) < 1:
            self.show_warning_messagebox("No background selected.", title="Error")
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1 and len(self.listWidget_bkg.selectedIndexes()) != len(self.listWidget_smp.selectedIndexes()):
            self.show_warning_messagebox('number of selected background and samples different. Returning.')
            return

        if len(self.listWidget_bkg.selectedIndexes()) > 1:
            self.show_warning_messagebox('More than one background selected, one background per sample mode.')

        #except:
        #    self.show_warning_messagebox("No background selected.")
        #    return
        if len(self.listWidget_bkg.selectedIndexes()) == 1:
            bkg_name = self.listWidget_bkg.selectedIndexes()[0].data()
            bkg_data = self.background_data[bkg_name].array
            
            if self.mask is not None:
                bkg_data = self.mask_pix_zero(bkg_data)

            for index in self.listWidget_smp.selectedIndexes():
                out = {}
                #out['path'] = os.path.join(self.sample_data[index.data()].dir,  "subd_" + self.sample_data[index.data()].name)
                out['dir'] = self.sample_data[index.data()].dir
                out['ext'] = self.sample_data[index.data()].ext
                name = self.sample_data[index.data()].name
                out['name'] =name.split("~")[0] + "~" + "subd_" + name.split("~")[1]
                out['name'] = append_name(out['name'], self.processed_data) # add one if exists
                out['info'] = {"type": "sub"}
                if self.mask is not None:
                    smp_data = self.mask_pix_zero(self.sample_data[index.data()].array)
                else:
                    smp_data = self.sample_data[index.data()].array

                scale_factor = 1

                # if self.monitor_002:
                #     civi_smp = self.sample_data[index.data()].info['civi']
                #     civi_bkg = self.background_data[bkg_name].info['civi']
                # else:
                civi_smp = 1
                civi_bkg = 1

                part1 = np.divide(smp_data * scale_factor, float(self.lineEdit_smp_TM.text()) * civi_smp )
                part2 = np.divide(bkg_data * scale_factor, float(self.lineEdit_bkg_TM.text()) * civi_bkg )
                out['array'] = np.subtract(part1,part2)
                self.processed_data[out["name"]] = Data_2d(
                    out['dir'],
                    out['ext'],
                    out['name'],
                    out['array'],
                    out['info']
                )
                #self.processed_data[out["name"]].info = {"type": "sub","dim": "2D"} # add data type, this is not easy to read
                self.listWidget_processed.addItem(out["name"])

                #plot data
                self.set_plot_image_name(out['name'],out['info']['type'])
                self.plot_2D(self.processed_data[out["name"]].array, out['name'])
        else:
            for count, index in enumerate(self.listWidget_smp.selectedIndexes()):
                bkg_name = self.listWidget_bkg.selectedIndexes()[count].data()

                if self.mask is not None:
                    bkg_data = self.mask_pix_zero(bkg_data)

                bkg_data = self.background_data[bkg_name].array
                out = {}
                # out['path'] = os.path.join(self.sample_data[index.data()].dir,  "subd_" + self.sample_data[index.data()].name)
                out['dir'] = self.sample_data[index.data()].dir
                out['ext'] = self.sample_data[index.data()].ext
                name = self.sample_data[index.data()].name
                out['name'] =name.split("~")[0] + "~" + "subd_" + name.split("~")[1]
                out['name'] = self.append_name(out['name'], self.processed_data)  # add one if exists
                if self.mask is not None:
                    smp_data = self.mask_pix_zero(self.sample_data[index.data()].array)
                else:
                    smp_data = self.sample_data[index.data()].array

                part1 = np.divide(smp_data, float(self.lineEdit_smp_TM.text()))
                part2 = np.divide(bkg_data, float(self.lineEdit_bkg_TM.text()))
                out['data'] = np.subtract(part1, part2)
                self.processed_data[out["name"]] = Data_2d(
                    out['dir'],
                    out['ext'],
                    out['name'],
                    out['array'],
                    out['info']
                )
                self.processed_data[out["name"]].info = {"type": "sub","dim": "2D"}  # add data type, this is not easy to read
                self.listWidget_processed.addItem(out["name"])

                # plot data
                self.set_plot_image_name(out['name'],out['info']['type'])
                self.plot_2D(self.processed_data[out["name"]].data, out['name'])  #here

        #except:
        #    self.show_warning_messagebox("2d images not compatible.")
        #    return   

        self.clear_lists()
            

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
