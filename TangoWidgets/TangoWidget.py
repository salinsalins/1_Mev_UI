# coding: utf-8
'''
Created on Jan 1, 2020

@author: sanin
'''

import sys
import time
import logging

from PyQt5.QtWidgets import QWidget
import tango


class TangoWidget:
    ERROR_TEXT = '****'
    RECONNECT_TIMEOUT = 3.0    # seconds
    DEVICES = {}

    def __init__(self, name: str, widget: QWidget, readonly=True):
        #print('TangoWidgetinitEntry', name)
        # defaults
        self.name = name
        self.widget = widget
        self.widget.tango_widget = self
        self.readonly = readonly
        self.attr = None
        self.config = None
        self.format = None
        self.coeff = 1.0
        self.connected = False
        self.update_dt = 0.0
        self.ex_count = 0
        self.time = time.time()
        # configure logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.hasHandlers():
            self.logger.propagate = False
            self.logger.setLevel(logging.DEBUG)
            f_str = '%(asctime)s,%(msecs)d %(funcName)s(%(lineno)s) ' + \
                    '%(levelname)-7s %(message)s'
            log_formatter = logging.Formatter(f_str, datefmt='%H:%M:%S')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            self.logger.addHandler(console_handler)
        # create attribute proxy
        #print('TangoWidgetinit_1', name)
        self.connect_attribute_proxy(name)
        # update view
        #print('TangoWidgetinit_2', name)
        self.update(decorate_only=False)
        #print('TangoWidgetinitExit', name)

    def disconnect_attribute_proxy(self):
        if not self.connected:
            return
        self.ex_count += 1
        if self.ex_count > 3:
            self.time = time.time()
            self.connected = False
            self.attr_proxy = None
            self.attr = None
            self.config = None
            self.format = None
            self.ex_count = 0
            self.logger.debug('Attribute %s disconnected', self.name)

    def connect_attribute_proxy(self, name: str = None):
        self.time = time.time()
        if name is None:
            name = self.name
        try:
            if isinstance(name, str):
                n = name.rfind('/')
                self.dn = name[:n]
                self.an = name[n+1:]
                self.dp = None
                if self.dn in TangoWidget.DEVICES:
                    self.dp = TangoWidget.DEVICES[self.dn]
                else:
                    self.dp = tango.DeviceProxy(self.dn)
                    TangoWidget.DEVICES[self.dn] = self.dp
                if not self.dp.is_attribute_polled(self.an):
                    self.logger.info('Recommended to swith polling on for %s', name)
                self.attr = self.dp.read_attribute(self.an)
                self.config = self.dp.get_attribute_config_ex(self.an)[0]
                self.format = self.config.format
                try:
                    self.coeff = float(self.config.display_unit)
                except:
                    self.coeff = 1.0
                self.connected = True
                self.time = time.time()
                self.logger.info('Connected to Attribute %s', name)
            else:
                self.logger.warning('<str> required for attribute name')
                self.name = str(name)
                self.dp = None
                self.attr = None
                self.config = None
                self.format = None
                self.connected = False
                self.time = time.time()
        except:
            self.logger.warning('Can not create attribute %s', name)
            self.name = str(name)
            self.dp = None
            self.attr = None
            self.config = None
            self.format = None
            self.connected = False
            self.time = time.time()

    def decorate_error(self, *args, **kwargs):
        if hasattr(self.widget, 'setText'):
            self.widget.setText(TangoWidget.ERROR_TEXT)
        self.widget.setStyleSheet('color: gray')

    def decorate_invalid(self, text: str = None, *args, **kwargs):
        if hasattr(self.widget, 'setText') and text is not None:
            self.widget.setText(text)
        self.widget.setStyleSheet('color: red')

    def decorate_invalid_data_format(self, text: str = None, *args, **kwargs):
        self.decorate_invalid(text, *args, **kwargs)

    def decorate_invalid_quality(self, *args, **kwargs):
        self.decorate_invalid(*args, **kwargs)

    def decorate_valid(self, *args, **kwargs):
        self.widget.setStyleSheet('color: black')

    def read(self, force=False):
        try:
            if not force and self.dp.is_attribute_polled(self.an):
            #if not force and self.attr_proxy.is_polled():
                try:
                    attrib = self.dp.attribute_history(self.an, 1)[0]
                    #attrib = self.attr_proxy.history(1)[0]
                    if attrib.time.tv_sec > self.attr.time.tv_sec or \
                            (attrib.time.tv_sec == self.attr.time.tv_sec and attrib.time.tv_usec > self.attr.time.tv_usec):
                        self.attr = attrib
                except Exception as ex:
                    self.attr = None
                    self.disconnect_attribute_proxy()
                    raise ex
            else:
                #self.attr = self.attr_proxy.read()
                self.attr = self.dp.read_attribute(self.an)
        except Exception as ex:
            self.attr = None
            self.disconnect_attribute_proxy()
            raise ex
        self.ex_count = 0
        return self.attr

    def write(self, value):
        if self.readonly:
            return
        self.dp.write_attribute(self.an, value/self.coeff)
        #self.attr_proxy.write(value/self.coeff)

    def write_read(self, value):
        if self.readonly:
            return None
        self.attr = None
        try:
            self.attr = self.dp.write_read_attribute(self.an, value/self.coeff)
            #self.attr = self.attr_proxy.write_read(value/self.coeff)
        except Exception as ex:
            self.attr = None
            self.disconnect_attribute_proxy()
            raise ex
        self.ex_count = 0
        return self.attr

    # compare widget displayed value and read attribute value
    def compare(self):
        return True

    def set_widget_value(self):
        bs = self.widget.blockSignals(True)
        if hasattr(self.attr, 'value'):
            if hasattr(self.widget, 'setText'):
                if self.format is not None:
                    text = self.format % (self.attr.value * self.coeff)
                else:
                    text = str(self.attr.value)
                self.widget.setText(text)
            elif hasattr(self.widget, 'setValue'):
                self.widget.setValue(self.attr.value * self.coeff)
        self.widget.blockSignals(bs)

    def update(self, decorate_only=False) -> None:
        t0 = time.time()
        try:
            self.read()
            if self.attr.data_format != tango._tango.AttrDataFormat.SCALAR:
                self.logger.debug('Non scalar attribute')
                self.decorate_invalid_data_format()
            else:
                if not decorate_only:
                    self.set_widget_value()
                if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
                    self.logger.debug('%s %s' % (self.attr.quality, self.attr.name))
                    self.decorate_invalid_quality()
                elif not self.compare():
                    self.decorate_invalid()
                else:
                    self.decorate_valid()
        except:
            if self.connected:
                self.logger.debug('Exception updating widget', exc_info=True)
                self.disconnect_attribute_proxy()
            else:
                if (time.time() - self.time) > TangoWidget.RECONNECT_TIMEOUT:
                    self.connect_attribute_proxy()
            self.decorate_error()
        self.update_dt = time.time() - t0
        #print('update', self.attr_proxy, int(self.update_dt*1000.0), 'ms')

    def callback(self, value):
        #self.logger.debug('Callback entry')
        if self.readonly:
            return
        if self.connected:
            try:
                #self.write_read(value)
                self.write(value)
                self.read(True)
                #print('wr', self.attr.value, value)
                if self.attr.quality == tango._tango.AttrQuality.ATTR_VALID:
                    self.decorate_valid()
                else:
                    self.decorate_invalid()
            except:
                self.logger.debug('Exception %s in callback', sys.exc_info()[0])
                self.decorate_error()
        else:
            self.connect_attribute_proxy()
            self.decorate_error()
