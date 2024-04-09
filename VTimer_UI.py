# coding: utf-8
"""
Created on Jul 28, 2019

@author: sanin
"""

import os.path
import sys
from collections import deque

util_path = os.path.realpath('../TangoUtils')
if util_path not in sys.path:
    sys.path.append(util_path)
del util_path

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer
import PyQt5.QtGui as QtGui

from TangoWidgets.TangoCheckBox import TangoCheckBox
from TangoWidgets.TangoComboBox import TangoComboBox
from TangoWidgets.TangoLED import TangoLED
from TangoWidgets.TangoLabel import TangoLabel
from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox
from TangoWidgets.Timer_on_LED import Timer_on_LED
from TangoWidgets.RF_ready_LED import RF_ready_LED
from TangoWidgets.Lauda_ready_LED import Lauda_ready_LED

from config_logger import config_logger
from log_exception import log_exception
from TangoWidgets.Utils import *

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '0.1'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Globals
TIMER_PERIOD = 300  # ms


class MainWindow(QMainWindow):
    def __init__(self):
        # Initialization of the superclass
        super(MainWindow, self).__init__(None)
        # logging config
        self.logger = config_logger()
        #
        self.saved_states = deque(maxlen=100)
        self.last_state = []
        # members definition
        self.n = 0
        self.elapsed = 0.0
        self.remained = 0.0
        # Load the Qt UI
        uic.loadUi(UI_FILE, self)
        # Default main window parameters
        self.resize(QSize(480, 640))  # size
        self.move(QPoint(50, 50))  # position
        self.setWindowTitle(APPLICATION_NAME)  # title
        # restore settings
        restore_settings(self, file_name=CONFIG_FILE)
        #
        self.timer_device_name = self.config.get('timer_device_name', 'binp/nbi/timer1')
        self.config['timer_device_name'] = self.timer_device_name
        # Widgets definition
        self.enable_widgets = [
            TangoCheckBox(self.timer_device_name + '/channel1', self.checkBox_8),  # ch0           2
            TangoCheckBox(self.timer_device_name + '/channel2', self.checkBox_9),  # ch1           3
            TangoCheckBox(self.timer_device_name + '/channel3', self.checkBox_10),  # ch2          4
            TangoCheckBox(self.timer_device_name + '/channel4', self.checkBox_11),  # ch3          5
            TangoCheckBox(self.timer_device_name + '/channel5', self.checkBox_12),  # ch4
            TangoCheckBox(self.timer_device_name + '/channel6', self.checkBox_13),  # ch5
            TangoCheckBox(self.timer_device_name + '/channel7', self.checkBox_14),  # ch6
            TangoCheckBox(self.timer_device_name + '/channel8', self.checkBox_15),  # ch7
            TangoCheckBox(self.timer_device_name + '/channel9', self.checkBox_16),  # ch8
            TangoCheckBox(self.timer_device_name + '/channel10', self.checkBox_17),  # ch9
            TangoCheckBox(self.timer_device_name + '/channel11', self.checkBox_18),  # ch10
            TangoCheckBox(self.timer_device_name + '/channel12', self.checkBox_19),  # ch11        13
        ]
        self.restore = False
        self.stop_widgets = [
            TangoAbstractSpinBox(self.timer_device_name + '/channel1_stop', self.spinBox_11),  # ch0        26
            TangoAbstractSpinBox(self.timer_device_name + '/channel2_stop', self.spinBox_13),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel3_stop', self.spinBox_15),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel4_stop', self.spinBox_17),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel5_stop', self.spinBox_19),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel6_stop', self.spinBox_21),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel7_stop', self.spinBox_23),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel8_stop', self.spinBox_25),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel9_stop', self.spinBox_27),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel10_stop', self.spinBox_29),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel11_stop', self.spinBox_31),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel12_stop', self.spinBox_33),  # ch11      37
        ]
        self.rdwdgts = [
            # timer labels from enabled channels
            TangoLabel(self.timer_device_name + '/channel1', self.label_30, prop='label'),  # ch0
            TangoLabel(self.timer_device_name + '/channel3', self.label_31, prop='label'),  # ch1
            TangoLabel(self.timer_device_name + '/channel3', self.label_34, prop='label'),  # ch2
            TangoLabel(self.timer_device_name + '/channel4', self.label_35, prop='label'),  # ch3
            TangoLabel(self.timer_device_name + '/channel5', self.label_36, prop='label'),  # ch4
            TangoLabel(self.timer_device_name + '/channel6', self.label_38, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel7', self.label_39, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel8', self.label_40, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel9', self.label_41, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel10', self.label_42, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel11', self.label_43, prop='label'),  # ch
            TangoLabel(self.timer_device_name + '/channel12', self.label_44, prop='label'),  # ch11
            # pg
            # TangoLED('binp/nbi/pg_offset/output_state', self.pushButton_31),  # PG offset on
            # # lauda
            # # TangoLED('binp/nbi/laudapy/6230_7', self.pushButton_30),  # Pump On
            # # TangoLED('binp/nbi/laudapy/6230_0', self.pushButton_30),  # Valve
            # Lauda_ready_LED('binp/nbi/laudapy/', self.pushButton_30),
            # rf system
            # RF_ready_LED('binp/nbi/timer1/di60', self.pushButton_32),  # RF system ready
        ]
        # read/write attributes TangoWidgets list
        self.wtwdgts = [
            # timer
            TangoAbstractSpinBox(self.timer_device_name + '/Period', self.spinBox),  # period             0
            TangoComboBox(self.timer_device_name + '/Start_mode', self.comboBox),  # single/periodical    1
            TangoAbstractSpinBox(self.timer_device_name + '/channel1_start', self.spinBox_10),  # ch1       14
            TangoAbstractSpinBox(self.timer_device_name + '/channel2_start', self.spinBox_12),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel3_start', self.spinBox_14),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel4_start', self.spinBox_16),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel5_start', self.spinBox_18),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel6_start', self.spinBox_20),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel7_start', self.spinBox_22),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel8_start', self.spinBox_24),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel9_start', self.spinBox_26),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel10_start', self.spinBox_28),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel11_start', self.spinBox_30),  # ch
            TangoAbstractSpinBox(self.timer_device_name + '/channel12_start', self.spinBox_32),  # ch11     25
            TangoAbstractSpinBox('binp/nbi/adc0/Acq_start', self.spinBox_34),  # adc start
            TangoAbstractSpinBox('binp/nbi/adc0/Acq_stop', self.spinBox_35),  # adc stop
        ]
        # timer on led
        self.timer_on_led = TangoLED(self.timer_device_name + '/pulse',
                                     self.pushButton_29)
        self.timer_device = self.timer_on_led.attribute.device_proxy
        # interlock widgets
        self.anode_power_led = TangoLED('binp/nbi/rfpowercontrol/anode_power_ok',
                                        self.pushButton_33)
        # lauda
        self.lauda = Lauda_ready_LED('binp/nbi/laudapy/', self.pushButton_30)
        # RF system
        self.rf = RF_ready_LED('binp/nbi/timer1/di60', self.pushButton_32)  # RF system ready
        # PG offset
        self.pg = TangoLED('binp/nbi/pg_offset/output_state', self.pushButton_31)  # PG offset on
        # elapsed widget
        self.elapsed_widget = TangoLabel('binp/nbi/adc0/Elapsed', self.label_3)
        # combine all processed widgets
        self.widgets = (self.rdwdgts + self.wtwdgts +
                        self.enable_widgets + self.stop_widgets +
                        [self.lauda, self.rf, self.pg,
                         self.anode_power_led, self.elapsed_widget])
        self.max_time = 0.0
        # *******************************
        # additional decorations
        self.single_periodical_callback(self.comboBox.currentIndex())
        # *******************************
        # Connect signals with slots
        # single/periodical combo
        self.comboBox.currentIndexChanged.disconnect(self.comboBox.tango_widget.callback)
        self.comboBox.currentIndexChanged.connect(self.single_periodical_callback)
        # run button
        self.pushButton.clicked.connect(self.run_button_clicked)
        # execute button
        self.pushButton_2.clicked.connect(self.execute_button_clicked)
        # show more/less protection buttons
        self.pushButton_5.clicked.connect(self.show_more_protection_button_clicked)
        self.pushButton_8.clicked.connect(self.show_less_protection_button_clicked)
        # prevent non tango leds from changing color when clicked
        self.pushButton_34.mouseReleaseEvent = self.absorb_event
        self.pushButton_29.mouseReleaseEvent = self.absorb_event
        # ************
        # Defile callback task and start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        self.timer.start(TIMER_PERIOD)
        # ************
        # resize main window
        self.resize_main_window()
        # ************
        # populate comboBox_2 - scripts for timer
        self.populate_scripts()
        # ************
        # lock timer for exclusive use of this app
        # self.lock_timer()
        # Welcome message
        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')

    def lock_timer(self):
        if self.timer_device is not None:
            if self.timer_device.is_locked():
                self.logger.warning('Timer device is already locked')
                self.pushButton.setEnabled(False)
                self.comboBox.setEnabled(False)
            else:
                if self.timer_device.lock(100000):
                    self.logger.debug('Timer device locked successfully')
                else:
                    self.logger.error('Can not lock timer device')

    def populate_scripts(self):
        scripts = read_folder('scripts')
        truncated = [s.replace('.py', '') for s in scripts]
        for i in range(self.comboBox_2.count()):
            self.comboBox_2.removeItem(0)
        self.comboBox_2.insertItems(0, truncated)
        if 'SetDefault' in truncated:
            self.comboBox_2.setCurrentIndex(truncated.index('SetDefault'))

    def absorb_event(self, ev):
        pass

    def check_protection_interlock(self):
        if self.checkBox_23.isChecked():
            self.pushButton_33.tango_widget.update()
            if not self.pushButton_33.isChecked():
                return False
        if self.checkBox_20.isChecked():
            self.pushButton_30.tango_widget.update()
            if not self.pushButton_30.isChecked():
                return False
        if self.checkBox_21.isChecked():
            self.pushButton_31.tango_widget.update()
            if not self.pushButton_31.isChecked():
                return False
        if self.checkBox_22.isChecked():
            self.pushButton_32.tango_widget.update()
            if not self.pushButton_32.isChecked():
                return False
        return True

    def execute_button_clicked(self):
        file_name = ''
        try:
            file_name = os.path.join('scripts', self.comboBox_2.currentText() + '.py')
            with open(file_name, 'r') as scriptfile:
                s = scriptfile.read()
                exec(s)
                self.logger.debug('Script %s executed', file_name)
                self.comboBox_2.setStyleSheet('')
        except KeyboardInterrupt:
            raise
        except:
            self.comboBox_2.setStyleSheet('color: red')
            log_exception('Error script %s execution', file_name)

    def resize_main_window(self):
        self.frame.setVisible(True)
        self.resize(QSize(self.gridLayout_2.sizeHint().width(),
                          self.gridLayout_2.sizeHint().height() +
                          self.gridLayout_3.sizeHint().height()))

    def single_periodical_callback(self, value):
        if value == 0:  # switch to single
            # hide remained
            self.label_4.setVisible(False)
            self.label_5.setVisible(False)
            # run button
            self.pushButton.setText('Shoot')
            self.comboBox.blockSignals(True)
            self.comboBox.tango_widget.callback(value)
            self.comboBox.tango_widget.read(force=True, sync=True)
            self.comboBox.blockSignals(False)
        elif value == 1:  # switch to periodical
            # check protection interlock
            if not self.check_protection_interlock():
                self.logger.error('Protection - Shot has been rejected')
                self.comboBox.blockSignals(True)
                self.comboBox.setCurrentIndex(0)
                self.comboBox.tango_widget.callback(0)
                self.comboBox.setStyleSheet('border: 3px solid red')
                self.comboBox.blockSignals(False)
                QMessageBox.critical(self, 'Protection',
                                     'Protection interlock.\nShot has been rejected.',
                                     QMessageBox.Ok)
                return
            # check for period expired
            try:
                remained = self.spinBox.value() - int(self.label_3.text())
            except KeyboardInterrupt:
                raise
            except:
                remained = -1
            if remained > 0:
                self.logger.error('Period is not expired - Shot has been rejected')
                self.comboBox.blockSignals(True)
                self.comboBox.setCurrentIndex(0)
                self.comboBox.tango_widget.callback(0)
                self.comboBox.setStyleSheet('border: 3px solid red')
                self.comboBox.blockSignals(False)
                QMessageBox.critical(self, 'Period',
                                     'Period is not expired.\nShot has been rejected.',
                                     QMessageBox.Ok)
                return
            # show remained
            self.label_4.setVisible(True)
            self.label_5.setVisible(True)
            self.max_time = self.read_max_time() / 1000.0
            self.comboBox.blockSignals(True)
            self.comboBox.tango_widget.callback(1)
            self.comboBox.tango_widget.read(force=True, sync=True)
            self.comboBox.blockSignals(False)

    def read_max_time(self):
        mt = 0.0
        for i, w in enumerate(self.enable_widgets):
            w.attribute.read()
            if w.attribute.value():
                mt = max(mt, self.stop_widgets[i].get_widget_value())
        return mt

    def show_more_protection_button_clicked(self, value):
        self.stackedWidget_2.setCurrentIndex(0)

    def show_less_protection_button_clicked(self, value):
        self.stackedWidget_2.setCurrentIndex(1)

    def update_ready_led(self):
        # if self.pushButton_34.isVisible():
        if self.check_protection_interlock():
            self.pushButton_34.setChecked(True)
        else:
            self.pushButton_34.setChecked(False)
            if self.timer_on_led.widget.isEnabled():
                self.pulse_off('Protection interlock')

    def run_button_clicked(self, value):
        if self.comboBox.currentIndex() == 0:  # single
            if self.timer_on_led.get_widget_value():  # pulse is on
                self.pulse_off('Interrupted by user.')
            else:
                # check protection interlock
                if not self.check_protection_interlock():
                    self.logger.error('Shot has been rejected')
                    self.pushButton.setStyleSheet('border: 3px solid red')
                    QMessageBox.critical(self, 'Interlock',
                                         'Shot has been rejected', QMessageBox.Ok)
                    return
                self.max_time = self.read_max_time() / 1000.0
                self.timer_on_led.attribute.device_proxy.write_attribute('Start_single', 1)
                self.timer_on_led.attribute.device_proxy.write_attribute('Start_single', 0)
            for w in self.enable_widgets:
                if w.get_widget_value():
                    return
            # QMessageBox.critical(self, 'No active channels',
            # 'No active channels', QMessageBox.Ok)
        elif self.comboBox.currentIndex() == 1:  # periodical
            if self.timer_on_led.get_widget_value():  # pulse is on
                self.pulse_off('Interrupted by user!')
            self.comboBox.setCurrentIndex(0)

    def pulse_off(self, msg='Interrupted by user.'):
        self.save_state()
        n = 0
        try:
            self.timer_device.write_attribute('run', 0)
        except KeyboardInterrupt:
            raise
        except:
            n += 1
        if n <= 0:
            # a = QMessageBox.question(self, 'Shot Interrupted',
            #                          msg + '\n\nRestore enabled channels?',
            #                          QMessageBox.Yes | QMessageBox.No)
            # if a == QMessageBox.Yes:
            #     self.restore = True
            # # self.max_time = 0.0
            self.timer_on_led.update(False)
            return
        QMessageBox.critical(self, 'Can not stop pulse!',
        'Can not stop pulse!', QMessageBox.Ok)
        self.logger.error("Can not stop pulse")
        self.logger.debug("Last Exception ", exc_info=True)
        self.restore = False

    def save_state(self, state=None):
        if state is None:
            state = self.get_state()
        if state == self.last_state:
            self.logger.debug('State save ignored')
            return None
        self.saved_states.append(state)
        self.last_state = state
        self.logger.debug('State saved to index %s', len(self.saved_states) - 1)
        return state

    def get_state(self):
        func_list = [self.checkBox_8.isChecked,
                     self.spinBox_10.value,
                     self.spinBox_11.value,
                     self.checkBox_9.isChecked,
                     self.spinBox_12.value,
                     self.spinBox_13.value,
                     self.checkBox_10.isChecked,
                     self.spinBox_14.value,
                     self.spinBox_15.value,
                     self.checkBox_11.isChecked,
                     self.spinBox_16.value,
                     self.spinBox_17.value,
                     self.checkBox_12.isChecked,
                     self.spinBox_18.value,
                     self.spinBox_19.value,
                     self.checkBox_13.isChecked,
                     self.spinBox_20.value,
                     self.spinBox_21.value,
                     self.checkBox_14.isChecked,
                     self.spinBox_22.value,
                     self.spinBox_23.value,
                     self.checkBox_15.isChecked,
                     self.spinBox_24.value,
                     self.spinBox_25.value,
                     self.checkBox_16.isChecked,
                     self.spinBox_26.value,
                     self.spinBox_27.value,
                     self.checkBox_17.isChecked,
                     self.spinBox_28.value,
                     self.spinBox_29.value,
                     self.checkBox_18.isChecked,
                     self.spinBox_30.value,
                     self.spinBox_31.value,
                     self.checkBox_19.isChecked,
                     self.spinBox_32.value,
                     self.spinBox_33.value,
                     self.spinBox_34.value,
                     self.spinBox_35.value]
        state = [f() for f in func_list]
        return state

    def set_state(self, state=None):
        if state is None:
            if len(self.saved_states) <= 0:
                self.logger.info('State stack is empty')
                return
            state = self.saved_states.pop()
            state_id = 'index %s' % len(self.saved_states)
        else:
            state_id = str(state)[:10]
        func_list = [self.checkBox_8.setChecked,
                     self.spinBox_10.setValue,
                     self.spinBox_11.setValue,
                     self.checkBox_9.setChecked,
                     self.spinBox_12.setValue,
                     self.spinBox_13.setValue,
                     self.checkBox_10.setChecked,
                     self.spinBox_14.setValue,
                     self.spinBox_15.setValue,
                     self.checkBox_11.setChecked,
                     self.spinBox_16.setValue,
                     self.spinBox_17.setValue,
                     self.checkBox_12.setChecked,
                     self.spinBox_18.setValue,
                     self.spinBox_19.setValue,
                     self.checkBox_13.setChecked,
                     self.spinBox_20.setValue,
                     self.spinBox_21.setValue,
                     self.checkBox_14.setChecked,
                     self.spinBox_22.setValue,
                     self.spinBox_23.setValue,
                     self.checkBox_15.setChecked,
                     self.spinBox_24.setValue,
                     self.spinBox_25.setValue,
                     self.checkBox_16.setChecked,
                     self.spinBox_26.setValue,
                     self.spinBox_27.setValue,
                     self.checkBox_17.setChecked,
                     self.spinBox_28.setValue,
                     self.spinBox_29.setValue,
                     self.checkBox_18.setChecked,
                     self.spinBox_30.setValue,
                     self.spinBox_31.setValue,
                     self.checkBox_19.setChecked,
                     self.spinBox_32.setValue,
                     self.spinBox_33.setValue,
                     self.spinBox_34.setValue,
                     self.spinBox_35.setValue]
        for i in range(len(state)):
            func_list[i](state[i])
        self.last_state = state
        self.logger.debug('State has been restored from %s', state_id)
        return state

    def onQuit(self):
        # Save global settings
        self.timer.stop()
        save_settings(self, file_name=CONFIG_FILE)

    def timer_handler(self):
        t0 = time.time()
        try:
            self.save_state()
            if len(self.widgets) <= 0:
                return
            # during pulse
            # if self.timer_on_led.value:   # pulse is on
            self.update_ready_led()
            self.elapsed_widget.update()
            v = self.elapsed_widget.attribute.valid_value()
            if isinstance(v, float) and v < self.max_time:
                # pulse is ON LED -> ON
                self.pushButton.setStyleSheet('color: red; font: bold')
                self.pushButton.setText('Stop')
                self.timer_on_led.set_widget_value(1.0)
            else:
                # pulse is OFF LED -> OFF
                self.pushButton.setStyleSheet('')
                self.timer_on_led.set_widget_value(0.0)
                if self.comboBox.currentIndex() == 0:
                    self.pushButton.setText('Shoot')
                if self.restore:
                    for w in self.enable_widgets:
                        try:
                            self.timer_device.write_attribute(w.attribute.attribute_name,
                                                              w.last_state)
                        except KeyboardInterrupt:
                            raise
                        except:
                            pass
                    self.set_state()
                    self.restore = False
            # remained
            try:
                self.remained = self.spinBox.value() - int(self.label_3.text())
            except KeyboardInterrupt:
                raise
            except:
                self.remained = -1
            self.label_5.setText('%d s' % self.remained)
            # main loop updating widgets
            count = 0
            while time.time() - t0 < TIMER_PERIOD / 1000.00 * 0.8:
                if self.n < len(self.widgets) and self.widgets[self.n].widget.isVisible():
                    self.widgets[self.n].update()
                self.n += 1
                if self.n >= len(self.widgets):
                    self.n = 0
                count += 1
                if count == len(self.widgets):
                    break
            self.update_ready_led()
            self.elapsed = time.time() - t0
        except KeyboardInterrupt:
            raise
        except:
            log_exception('Unexpected exception in timer callback')
        # self.logger.debug("total time %s s", time.time() - t0)


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
