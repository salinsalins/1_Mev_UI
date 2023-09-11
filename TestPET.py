# coding: utf-8
"""
Created on Jul 28, 2019

@author: sanin
"""

import sys

if '../TangoUtils' not in sys.path: sys.path.append('../TangoUtils')

from log_exception import log_exception

from TangoCheckBox import TangoCheckBox

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer

import tango

from TangoWidgets.TangoWidget import TangoWidget
from TangoWidgets.TangoLED import TangoLED
from TangoWidgets.TangoLabel import TangoLabel
from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox
from TangoWidgets.TangoPushButton import TangoPushButton
from TangoWidgets.TangoAttribute import TangoAttribute
from TangoWidgets.Utils import *

from config_logger import config_logger

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1.0'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Globals
TIMER_PERIOD = 500  # ms


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        # Initialization of the superclass
        super(MainWindow, self).__init__(parent)
        # logging config
        self.logger = config_logger(level=logging.DEBUG)
        # members definition
        self.n = 0
        self.elapsed = 0.0
        # Load the UI
        uic.loadUi(UI_FILE, self)
        # main window parameters
        self.resize(QSize(480, 640))                 # size
        self.move(QPoint(50, 50))                    # position
        self.setWindowTitle(APPLICATION_NAME)        # title
        self.setWindowIcon(QtGui.QIcon('icon.png'))  # icon

        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')

        restore_settings(self, file_name=CONFIG_FILE)

        self.rdwdgts = []
        self.wtwdgts = []
        layout = self.gridLayout
        device_name = self.config.get('device', 'binp/nbi/testPET')
        try:
            dp = tango.DeviceProxy(device_name)
        except tango.ConnectionFailed:
            log_exception('Device proxy can not be connected, exiting')
            exit(-1)
        pet_type = dp.read_attribute('device_type')
        self.label_1.setText(pet_type.value)
        ip = dp.read_attribute('IP')
        self.label_2.setText(ip.value)
        al = dp.get_attribute_list()
        row = 2
        for a in al:
            ac = dp.get_attribute_config_ex(a)
            if a.startswith('do'):
                lb = QLabel(a + ': ', self)
                layout.addWidget(lb, row, 0)
                cb = QCheckBox(a, self)
                layout.addWidget(cb, row, 1)
                row += 1
                self.rdwdgts.append(TangoCheckBox(device_name + '/' + a, cb))
            if a.startswith('di'):
                lb = QLabel(a + ': ', self)
                layout.addWidget(lb, row, 0)
                cb = QCheckBox(a, self)
                layout.addWidget(cb, row, 1)
                row += 1
                self.rdwdgts.append(TangoLED(device_name + '/' + a, cb))
            if a.startswith('ai'):
                lb = QLabel(a + ': ', self)
                layout.addWidget(lb, row, 0)
                lb = QLabel(a, self)
                layout.addWidget(lb, row, 1)
                row += 1
                self.rdwdgts.append(TangoLabel(device_name + '/' + a, lb))

        TangoWidget.RECONNECT_TIMEOUT = 5.0
        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(TIMER_PERIOD)

    def setpoint_valueChanged(self):
        self.lauda.write_attribute('1100', self.spinBox_4.value())

    def lauda_pump_on_callback(self, value):
        if value:
            # reset
            self.pushButton_9.tango_widget.pressed()
            self.pushButton_9.tango_widget.released()
            # enable
            self.pushButton_6.setChecked(True)
            self.pushButton_6.tango_widget.clicked()

    def onQuit(self) :
        # Save global settings
        save_settings(self, file_name=CONFIG_FILE)
        self.timer.stop()
        
    def timer_handler(self):
        t0 = time.time()
        if len(self.rdwdgts) <= 0 and len(self.wtwdgts) <= 0:
            return
        self.elapsed = 0.0
        count = 0
        while time.time() - t0 < TIMER_PERIOD/2000.0:
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
