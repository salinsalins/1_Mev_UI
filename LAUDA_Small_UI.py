# coding: utf-8
"""
Created on Mar 25, 2025

@author: sanin
"""
import inspect
import os
import sys
if os.path.realpath('../TangoUtils') not in sys.path: sys.path.append(os.path.realpath('../TangoUtils'))

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer

from TangoWidgets.TangoComboBox import TangoComboBox
from TangoWidgets.TangoWidget import TangoWidget
from TangoWidgets.TangoLED import TangoLED
from TangoWidgets.TangoLabel import TangoLabel
from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox
from TangoWidgets.TangoPushButton import TangoPushButton
from TangoWidgets.TangoAttribute import TangoAttribute
from TangoWidgets.Utils import *

from config_logger import config_logger
from log_exception import log_exception

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

        # read only attributes
        self.rdwdgts = (
            TangoLED(self.config.get('run', 'binp/nbi/small_lauda/run'), self.pushButton_31),
            TangoLED(self.config.get('error', 'binp/nbi/small_lauda/error_diagnosis'), self.pushButton_32),
            TangoLabel(self.config.get('output_temp', 'binp/nbi/small_lauda/output_temp'), self.label_3),
            TangoLabel(self.config.get('pressure', 'binp/nbi/small_lauda/pressure'), self.label_5)
        )
        # writable attributes
        self.wtwdgts = (
            TangoAbstractSpinBox(self.config.get('set_point', 'binp/nbi/small_lauda/set_point'), self.spinBox, False),
            TangoPushButton(self.config.get('run', "binp/nbi/small_lauda/run"), self.pushButton, False),
            TangoComboBox(self.config.get('cooling_mode', "binp/nbi/small_lauda/cooling_mode"), self.comboBox, False),
            TangoAbstractSpinBox(self.config.get('pump', 'binp/nbi/small_lauda/pump'), self.spinBox_2, False)
        )
        # widgets tuning

        def set_status_value(swgt=None, value=None):
            if swgt is None:
                swgt = inspect.stack()[1].frame.f_locals['self']
            if value is None:
                value = swgt.attribute.value() == '0000000'
            swgt.widget.setChecked(bool(value))
            return bool(value)

        self.rdwdgts[1].set_widget_value = set_status_value
        #
        TangoWidget.RECONNECT_TIMEOUT = 5.0
        # Connect signals with slots
        # self.pushButton.clicked.connect(self.lauda_pump_on_callback)
        # self.spinBox.valueChanged.connect(self.setpoint_valueChanged)
        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(TIMER_PERIOD)

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
        count_max = max(len(self.rdwdgts), len(self.wtwdgts))
        while time.time() - t0 < TIMER_PERIOD/2000.0:
            if self.n < len(self.rdwdgts) and self.rdwdgts[self.n].widget.isVisible():
                self.rdwdgts[self.n].update()
            if self.n < len(self.wtwdgts) and self.wtwdgts[self.n].widget.isVisible():
                self.wtwdgts[self.n].update(decorate_only=True)
            self.n += 1
            if self.n >= count_max:
                self.n = 0
            count += 1
            if count >= count_max:
                self.elapsed = time.time() - t0
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
