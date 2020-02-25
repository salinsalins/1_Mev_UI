# coding: utf-8
'''
Created on Jan 1, 2020

@author: sanin
'''

import sys
import time

from PyQt5.QtWidgets import QWidget
import tango

from .Utils import *


class TangoWidget:
    ERROR_TEXT = '****'
    RECONNECT_TIMEOUT = 3.0    # seconds
    DEVICES = {}

    def __init__(self, name: str, widget: QWidget, readonly=True, level=logging.DEBUG):
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
        # configure logging
        self.logger = config_logger(level=level)
        # create attribute proxy
        self.dn = ''
        self.an = ''
        self.dp = None
        self.time = time.time()
        self.connect_attribute_proxy(name)
        # update view
        self.update(decorate_only=False)
        #print('TangoWidgetinitExit', name)

    def connect_attribute_proxy(self, name: str = None):
        self.time = time.time()
        if name is None:
            name = self.name
        self.name = str(name)
        try:
            self.dn, self.an = self.split_attribute_name(name)
            self.dp = self.create_device_proxy(self.dn)
            self.attr = self.dp.read_attribute(self.an)
            self.config = self.dp.get_attribute_config_ex(self.an)[0]
            self.format = self.config.format
            try:
                self.coeff = float(self.config.display_unit)
            except:
                self.coeff = 1.0
            self.connected = True
            self.time = time.time()
            self.logger.info('Attribute %s has been connected', name)
        except:
            self.logger.warning('Can not connect attribute %s', name)
            self.logger.debug('Exception connecting attribute %s' % name, exc_info=True)
            self.name = str(name)
            self.dp = None
            self.attr = None
            self.config = None
            self.format = None
            self.coeff = 1.0
            self.connected = False
            self.time = time.time()

    def split_attribute_name(self, name):
        device = ''
        attrib = ''
        splitted = name.split('/')
        if len(splitted) < 4:
            raise IndexError('Incorrect attribute name format')
        n = name.rfind('/')
        if n >= 0:
            attrib = name[n+1:]
            device = name[:n]
        else:
            device = name
        return device, attrib

    def create_device_proxy(self, device_name):
        dp = None
        if device_name in TangoWidget.DEVICES and TangoWidget.DEVICES[device_name] is not None:
            try:
                pt = TangoWidget.DEVICES[device_name].ping()
                dp = TangoWidget.DEVICES[device_name]
                self.logger.debug('Used DeviceProxy %s for %s %d [s]' % (dp, device_name, pt))
            except:
                self.logger.debug('Exception creating device %s' % device_name, exc_info=True)
                dp = None
        if dp is None:
            dp = tango.DeviceProxy(self.dn)
            self.logger.debug('Created DeviceProxy %s for %s' % (dp, device_name))
            TangoWidget.DEVICES[device_name] = dp
        return dp

    def set_attribute_properties(self):
        self.config = self.dp.get_attribute_config_ex(self.an)[0]
        self.format = self.config.format
        try:
            self.coeff = float(self.config.display_unit)
        except:
            self.coeff = 1.0
        self.connected = True

    def disconnect_attribute_proxy(self):
        if not self.connected:
            return
        self.ex_count += 1
        if self.ex_count > 3:
            self.time = time.time()
            self.connected = False
            self.attr = None
            self.config = None
            self.format = None
            self.ex_count = 0
            self.logger.debug('Attribute %s disconnected', self.name)

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

    def decorate_not_equal(self, text: str = None, *args, **kwargs):
        self.decorate_invalid(text, *args, **kwargs)

    def decorate_invalid_quality(self, *args, **kwargs):
        self.decorate_invalid(*args, **kwargs)

    def decorate_valid(self, *args, **kwargs):
        self.widget.setStyleSheet('color: black')

    def read(self, force=False):
        if not self.connected:
            raise ConnectionError('Attribute disconnected')
        try:
            if not force and self.dp.is_attribute_polled(self.an):
                attrib = self.dp.attribute_history(self.an, 1)[0]
                t1 = attrib.time.tv_sec + (1.0e-6 * attrib.time.tv_usec)
                t2 = self.attr.time.tv_sec + (1.0e-6 * self.attr.time.tv_usec)
                if t1 > t2:
                    self.attr = attrib
            else:
                self.attr = self.dp.read_attribute(self.an)
        except Exception as ex:
            #self.logger.debug('Exception in read', exc_info=True)
            self.attr = None
            self.disconnect_attribute_proxy()
            raise
        self.ex_count = 0
        return self.attr

    def write(self, value):
        if self.readonly:
            return
        try:
            self.dp.write_attribute(self.an, value/self.coeff)
        except Exception as ex:
            self.disconnect_attribute_proxy()
            raise ex

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

    # compare widget displayed value and read attribute value
    def compare(self):
        return True

    def set_widget_value(self):
        if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
            # dont set value from invalid attribute
            return
        bs = self.widget.blockSignals(True)
        if hasattr(self.attr, 'value'):
            if hasattr(self.widget, 'setValue'):
                self.widget.setValue(self.attr.value * self.coeff)
            elif hasattr(self.widget, 'setChecked'):
                self.widget.setChecked(bool(self.attr.value))
            elif hasattr(self.widget, 'setText'):
                if self.format is not None:
                    text = self.format % (self.attr.value * self.coeff)
                else:
                    text = str(self.attr.value)
                self.widget.setText(text)
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
                else:
                    if not self.compare():
                        self.decorate_not_equal()
                    else:
                        self.decorate_valid()
        except:
            if self.connected:
                self.logger.debug('Exception updating widget', exc_info=True)
                self.disconnect_attribute_proxy()
            else:
                if (time.time() - self.time) > TangoWidget.RECONNECT_TIMEOUT:
                    self.connect_attribute_proxy()
                if self.connected:
                    if hasattr(self.widget, 'value'):
                        self.write(self.widget.value())
                    elif hasattr(self.widget, 'getChecked'):
                        self.write(self.widget.getChecked())
                    elif hasattr(self.widget, 'getText'):
                        self.write(self.widget.getText())
                    if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
                        self.logger.debug('%s %s' % (self.attr.quality, self.attr.name))
                        self.decorate_invalid_quality()
                    else:
                        self.decorate_valid()
                else:
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
