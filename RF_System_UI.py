# coding: utf-8
'''
Created on Jul 28, 2019

@author: sanin
'''

import sys
import json
import logging
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import qApp
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QLineEdit
from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QTimer
import PyQt5.QtGui as QtGui

import tango

from TangoWidgets.TangoWidget import TangoWidget
from TangoWidgets.TangoCheckBox import TangoCheckBox
from TangoWidgets.TangoComboBox import TangoComboBox
from TangoWidgets.TangoLED import TangoLED
from TangoWidgets.TangoLabel import TangoLabel
from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox
from TangoWidgets.TangoRadioButton import TangoRadioButton
from TangoWidgets.TangoPushButton import TangoPushButton

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'RF_System_UI'
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1_0'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
f_str = '%(asctime)s,%(msecs)d %(funcName)s(%(lineno)s) ' + \
        '%(levelname)-7s %(message)s'
log_formatter = logging.Formatter(f_str, datefmt='%H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Global configuration dictionary
CONFIG = {}
TIMER_PERIOD = 300  # ms


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        global logger
        # Initialization of the superclass
        super(MainWindow, self).__init__(parent)
        # logging config
        self.logger = logger
        # members definition
        self.n = 0
        self.elapsed = 0.0

        # Load the UI
        uic.loadUi(UI_FILE, self)

        # main window parameters
        ##self.setMinimumSize(QSize(480, 640))        # min size
        self.resize(QSize(480, 640))                # size
        self.move(QPoint(50, 50))                   # position
        self.setWindowTitle(APPLICATION_NAME)       # title
        self.setWindowIcon(QtGui.QIcon('icon.png')) # icon

        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')

        self.restore_settings()

        # define devices in use
        dn = 'binp/nbi/dac0'
        self.dac_device = tango.DeviceProxy(dn)
        TangoWidget.DEVICES.append((dn, self.dac_device))
        dn = 'binp/nbi/adc0'
        self.adc_device = tango.DeviceProxy(dn)
        TangoWidget.DEVICES.append((dn, self.adc_device))
        dn = 'binp/nbi/timing'
        self.timer_device = tango.DeviceProxy(dn)
        TangoWidget.DEVICES.append((dn, self.timer_device))

        # read attributes TangoWidgets list
        self.rdwdgts = (
            # rf system
            #TangoLED('binp/nbi/timing/di63', self.pushButton_1),
        )
        # writable attributes TangoWidgets list
        self.wtwdgts = (
            # rf system
            TangoAbstractSpinBox('binp/nbi/dac0/channel0', self.spinBox_1, False),
            TangoAbstractSpinBox('binp/nbi/dac0/channel1', self.spinBox_2, False),
            TangoPushButton('binp/nbi/timing/do0', self.pushButton_3, False),
            TangoPushButton('binp/nbi/timing/do1', self.pushButton_4, False),
            TangoPushButton('binp/nbi/timing/do2', self.pushButton_5, False),
        )
        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(TIMER_PERIOD)

    def onQuit(self) :
        # Save global settings
        self.save_settings()
        self.timer.stop()
        
    def save_settings(self, widgets=(), file_name=CONFIG_FILE) :
        global CONFIG
        try:
            # Save window size and position
            p = self.pos()
            s = self.size()
            CONFIG['main_window'] = {'size':(s.width(), s.height()), 'position':(p.x(), p.y())}
            #get_state(self.comboBox_1, 'comboBox_1')
            for w in widgets:
                #get_widget_state(w, CONFIG)
                pass
            with open(file_name, 'w') as configfile:
                configfile.write(json.dumps(CONFIG, indent=4))
            self.logger.info('Configuration saved to %s' % file_name)
            return True
        except :
            self.logger.log(logging.WARNING, 'Configuration save error to %s' % file_name)
            print_exception_info()
            return False
        
    def restore_settings(self, widgets=(), file_name=CONFIG_FILE) :
        global CONFIG
        try :
            with open(file_name, 'r') as configfile:
                s = configfile.read()
            CONFIG = json.loads(s)
            # Restore log level
            if 'log_level' in CONFIG:
                v = CONFIG['log_level']
                self.logger.setLevel(v)
                levels = [logging.NOTSET, logging.DEBUG, logging.INFO,
                          logging.WARNING, logging.ERROR, logging.CRITICAL, logging.CRITICAL+10]
                n = 1
                for m in range(len(levels)):
                    if v < levels[m]:
                        n = m
                        break
                self.comboBox_1.setCurrentIndex(n-1)
            # Restore window size and position
            if 'main_window' in CONFIG:
                self.resize(QSize(CONFIG['main_window']['size'][0], CONFIG['main_window']['size'][1]))
                self.move(QPoint(CONFIG['main_window']['position'][0], CONFIG['main_window']['position'][1]))
            #set_state(self.plainTextEdit_1, 'plainTextEdit_1')
            #set_state(self.comboBox_1, 'comboBox_1')
            for w in widgets:
                #set_widget_state(w, CONFIG)
                pass
            self.logger.log(logging.INFO, 'Configuration restored from %s' % file_name)
            return True
        except :
            self.logger.log(logging.WARNING, 'Configuration restore error from %s' % file_name)
            print_exception_info()
            return False

    def timer_handler(self):
        t0 = time.time()
        if len(self.rdwdgts) <= 0 and len(self.wtwdgts) <= 0:
            return
        self.elapsed = 0.0
        count = 0
        while time.time() - t0 < TIMER_PERIOD/2000.0:
            try:
                av = self.adc_device.read_attribute('chan16')
                if av.quality != tango._tango.AttrQuality.ATTR_VALID:
                    self.pushButton_1.setChecked(False)
                else:
                        av_config = self.adc_device.get_attribute_config_ex('chan16')[0]
                        av_coeff = float(av_config.display_unit)
                        if av.value*av_coeff > 9.0:
                            self.pushButton_1.setChecked(True)
                        else:
                            self.pushButton_1.setChecked(False)
            except:
                self.pushButton_1.setChecked(False)
            if self.n < len(self.rdwdgts) and self.rdwdgts[self.n].widget.isVisible():
                self.rdwdgts[self.n].update()
            if self.n < len(self.wtwdgts) and self.wtwdgts[self.n].widget.isVisible():
                self.wtwdgts[self.n].update(decorate_only=True)
            self.n += 1
            if self.n >= max(len(self.rdwdgts), len(self.wtwdgts)):
                self.n = 0
            count += 1
            if count == max(len(self.rdwdgts), len(self.wtwdgts)):
                self.elapsed = time.time() - self.elapsed
                return


def print_exception_info(level=logging.DEBUG):
    logger.log(level, "Exception ", exc_info=True)


if __name__ == '__main__':
    # Create the GUI application
    app = QApplication(sys.argv)
    # Instantiate the main window
    dmw = MainWindow()
    app.aboutToQuit.connect(dmw.onQuit)
    # Show it
    dmw.show()
    # Start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(app.exec_())
