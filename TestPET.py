# coding: utf-8
"""
Created on Jul 28, 2019

@author: sanin
"""

import sys

from TangoCheckBox import TangoCheckBox

if '../TangoUtils' not in sys.path: sys.path.append('../TangoUtils')

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer

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
        device_name = self.config.get('device', 'binp/test/test_pet')
        dp = tango.DeviceProxy(device_name)
        al = dp.get_attribute_list()
        row = 2
        for a in al:
            ac = dp.get_attribute_config_ex(a)
            if a.startswith('do'):
                print(a)
                cb = QCheckBox(a, self)
                layout.addWidget(cb, row, 1)
                row += 1
                # self.rdwdgts.append(TangoLED(device_name + '/' + a, cb))
                self.rdwdgts.append(TangoCheckBox(device_name + '/' + a, cb))

        # attributes
        # self.rdwdgts = (
        #     # lauda
        #     TangoLED(self.config.get('pump', 'binp/nbi/lauda/6230_7'), self.pushButton_34),  # Pump On
        #     TangoLED(self.config.get('valve_state', 'binp/nbi/lauda/6230_0'), self.pushButton_31),  # Valve
        #     TangoLabel(self.config.get('return', 'binp/nbi/lauda/1012'), self.label_23),       # Return
        # )
        # writable attributes TangoWidgets list
        # self.wtwdgts = (
            # lauda
        #     TangoAbstractSpinBox(self.config.get('setpoint', 'binp/nbi/lauda/6200'), self.spinBox_4, False),  # SetPoint
        #     TangoPushButton(self.config.get('valve', 'binp/nbi/lauda/6210_3'), self.pushButton_4, False),  # Valve
        #     TangoPushButton(self.config.get('run', 'binp/nbi/lauda/6210_1'), self.pushButton_3, False),  # Run
        #     TangoPushButton(self.config.get('enable', 'binp/nbi/lauda/6210_0'), self.pushButton_6, False),  # Enable
        #     TangoPushButton(self.config.get('reset', 'binp/nbi/lauda/6210_2'), self.pushButton_9, False),  # Reset
        # )
        #
        TangoWidget.RECONNECT_TIMEOUT = 5.0
        # Connect signals with slots
        # self.pushButton_3.clicked.connect(self.lauda_pump_on_callback)
        # self.spinBox_4.valueChanged.connect(self.setpoint_valueChanged)
        self.lauda = None
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
