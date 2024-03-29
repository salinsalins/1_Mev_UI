# coding: utf-8
'''
Created on Jan 3, 2020

@author: sanin
'''
import time
from PyQt5.QtWidgets import QRadioButton
from TangoWidgets.TangoWidget import TangoWidget


class TangoRadioButton(TangoWidget):
    def __init__(self, name, widget: QRadioButton, readonly=True):
        super().__init__(name, widget, readonly)
        self.widget.toggled.connect(self.callback)

    def set_widget_value(self):
        self.widget.setChecked(self.value)
        return self.attr.value

    def decorate_error(self):
        self.widget.setStyleSheet('color: gray')
        self.widget.setEnabled(False)

    def decorate_invalid(self, text: str = None):
        self.widget.setStyleSheet('color: red')
        self.widget.setEnabled(True)

    def decorate_valid(self):
        self.widget.setStyleSheet('color: black')
        self.widget.setEnabled(True)

    def callback(self, value):
        if self.connected:
            try:
                self.dp.write_attribute(self.an, bool(value))
                self.decorate_valid()
            except:
                self.logger.debug('Exception %s in callback', exc_info=True)
                self.decorate_error()
        else:
            if time.time() - self.time > TangoWidget.RECONNECT_TIMEOUT:
                self.connect_attribute_proxy()
            self.decorate_error()
