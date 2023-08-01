# coding: utf-8
'''
Created on Jan 1, 2020

@author: sanin
'''
from PyQt5.QtWidgets import QPushButton
from TangoWidgets.TangoWidget import TangoWidget


class TangoLED(TangoWidget):
    def __init__(self, name, widget: QPushButton, **kwargs):
        super().__init__(name, widget, **kwargs)
        self.widget.clicked.connect(self.callback)
        # except:
        #     msg = '%s creation error.' % name
        #     self.logger.info(msg)
        #     self.logger.debug('Exception:', exc_info=True)

    def set_widget_value(self):
        self.widget.setChecked(bool(self.attribute.value()))
        return bool(self.attribute.value())

    def decorate_error(self):
        self.widget.setDisabled(True)

    def decorate_invalid(self, text: str = None, *args, **kwargs):
        self.widget.setDisabled(True)

    def decorate_valid(self):
        self.widget.setDisabled(False)

    def callback(self, value=None):
        self.logger.debug('********************')
        self.set_widget_value()
