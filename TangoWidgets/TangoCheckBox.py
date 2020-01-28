# coding: utf-8
'''
Created on Jan 3, 2020

@author: sanin
'''
import sys
import time
from PyQt5.QtWidgets import QCheckBox
from TangoWidgets.TangoWidget import TangoWidget


class TangoCheckBox(TangoWidget):
    def __init__(self, name, widget: QCheckBox, readonly=False):
        super().__init__(name, widget)
        if not readonly:
            self.widget.stateChanged.connect(self.callback)

    def set_widget_value(self):
        self.widget.setChecked(self.attr.value)
        return self.attr.value

    def decorate_error(self):
        print('cberror')
        self.widget.setStyleSheet('color: gray')
        self.widget.setEnabled(False)

    def decorate_invalid(self, text: str = None):
        print('cbinvalid')
        self.widget.setStyleSheet('QCheckBox::indicator { color: red; }')
        self.widget.setEnabled(True)

    def decorate_valid(self):
        print('cbvalid')
        self.widget.setStyleSheet('color: black')
        self.widget.setEnabled(True)

    def compare(self):
        try:
            return int(self.attr.value) == self.widget.isChecked()
        except:
            self.logger.debug('Exception in CheckboBox compare', exc_info=True)
            return False

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
                self.connect_attribute_proxy(self.attr_proxy)
            else:
                self.decorate_error()
