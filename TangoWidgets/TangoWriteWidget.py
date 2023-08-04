# coding: utf-8
"""
Created on Jan 17, 2020

@author: sanin
"""
from PyQt5.QtWidgets import QWidget
from TangoWidgets.TangoWidget import TangoWidget


class TangoWriteWidget(TangoWidget):
    def __init__(self, name, widget: QWidget, readonly=False):
        super().__init__(name, widget, readonly)
        self.attribute.read_result = self.attribute.device_proxy.read_attribute(self.attribute.attribute_name)
        self.update(decorate_only=False)

    def decorate_error(self):
        self.widget.setStyleSheet('color: gray')
        self.widget.setEnabled(False)

    def decorate_invalid(self, text: str = None, *args, **kwargs):
        # self.widget.setStyleSheet('color: red; selection-color: red')
        self.widget.setStyleSheet('color: red')
        self.widget.setEnabled(True)

    def decorate_valid(self):
        self.widget.setStyleSheet('')
        self.widget.setEnabled(True)

    def update(self, decorate_only=True):
        super().update(decorate_only)

    # compare widget displayed value and read attribute value
    def compare(self):
        if self.attribute.is_readonly():
            return True
        else:
            try:
                v = self.attribute.valid_value()
                if v is None:
                    return False
                if isinstance(v, bool):
                    return self.attribute.value() == self.widget.value()
                elif isinstance(v, int):
                    v1 = int(self.widget.value())
                    if abs(v - v1) > 1:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                elif isinstance(v, float):
                    v1 = float(self.widget.value())
                    if abs(v - v1) > abs(v * 1e-3):
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                elif isinstance(v, str):
                    v1 = str(self.widget.value())
                    if v != v1:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                else:
                    self.logger.debug('Unknown %s value %s', self.attribute.full_name, v)
                    return False
                return True
            except KeyboardInterrupt:
               raise
            except:
                self.logger.debug('%s Exception in compare' % self.attribute.full_name, exc_info=True)
                return False
