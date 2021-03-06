# coding: utf-8
"""
Created on Feb 4, 2020

@author: sanin
"""

import sys
import time

from PyQt5.QtWidgets import QWidget
import tango
from tango import DeviceProxy, GreenMode

from .Utils import *


class TangoAttributeConnectionFailed(tango.ConnectionFailed):
    pass


class TangoAttribute:
    devices = {}
    attributes = {}
    reconnect_timeout = 5.0

    # def __new__(cls, name, *args, **kwargs):
    #     if name in TangoAttribute.attributes:
    #         return TangoAttribute.attributes[name]
    #     return super(TangoAttribute, cls).__new__(cls)

    def __init__(self, name: str, level=logging.DEBUG, readonly=False, use_history=True):
        self.full_name = str(name)
        self.use_history = use_history
        self.device_name, self.attribute_name = split_attribute_name(self.full_name)
        self.device_proxy = None
        self.read_result = None
        self.config = None
        self.format = None
        self.coeff = 1.0
        self.connected = False
        self.readonly = readonly
        # configure logging
        self.logger = config_logger(level=level)
        # connect attribute
        self.connect()
        self.time = time.time()
        # async operation vars
        self.read_call_id = None
        self.write_call_id = None
        self.read_time = 0.0
        self.write_time = 0.0
        self.read_timeout = 5.0
        self.write_timeout = 5.0
        self.timeout_count = 0
        self.timeout_count_limit = 3
        self.force_read = False
        self.sync_read = False
        self.sync_write = True
        TangoAttribute.attributes[self.full_name] = self

    def connect(self):
        try:
            self.device_proxy = self.create_device_proxy()
            self.set_config()
            self.read_result = self.device_proxy.read_attribute(self.attribute_name)
            self.connected = True
            self.time = 0.0
            self.logger.info('Attribute %s has been connected' % self.full_name)
        except:
            self.disconnect()
            self.logger.warning('Can not connect attribute %s' % self.full_name)
            self.logger.debug('Exception connecting attribute %s' % self.full_name, exc_info=True)

    def disconnect(self):
        self.time = time.time()
        if not self.connected:
            return
        self.connected = False
        #self.device_proxy = None
        self.logger.debug('Attribute %s has been disconnected', self.full_name)

    def reconnect(self):
        if self.device_name in TangoAttribute.devices and TangoAttribute.devices[self.device_name] is not self.device_proxy:
            self.logger.debug('Device proxy changed for %s' % self.full_name)
            if time.time() - self.time > self.reconnect_timeout:
                self.connect()
        if self.connected:
            return
        if time.time() - self.time > self.reconnect_timeout:
            self.logger.debug('Reconnection timeout exceeded for %s' % self.full_name)
            self.connect()

    def create_device_proxy(self):
        dp = None
        if self.device_name in TangoAttribute.devices and TangoAttribute.devices[self.device_name] is not None:
            try:
                # check if device is alive
                pt = TangoAttribute.devices[self.device_name].ping()
                dp = TangoAttribute.devices[self.device_name]
                self.logger.debug('Device %s for %s exists, ping=%ds' % (self.device_name, self.attribute_name, pt))
            except:
                self.logger.warning('Exception %s connecting to %s' % (sys.exc_info()[0], self.device_name))
                self.logger.debug('Exception:', exc_info=True)
                dp = None
                TangoAttribute.devices[self.device_name] = dp
        if dp is None:
            try:
                dp = tango.DeviceProxy(self.device_name)
                dp.ping()
                self.logger.info('Device proxy for %s has been created' % self.device_name)
            except:
                self.logger.warning('Device %s creation exception' % self.device_name)
                dp = None
            TangoAttribute.devices[self.device_name] = dp
        return dp

    def set_config(self):
        self.config = self.device_proxy.get_attribute_config_ex(self.attribute_name)[0]
        self.format = self.config.format
        try:
            self.coeff = float(self.config.display_unit)
        except:
            self.coeff = 1.0
        self.readonly = self.readonly or self.is_readonly()

    def is_readonly(self):
        if self.config is not None:
            return self.config.writable == tango.AttrWriteType.READ
        else:
            return True

    def is_valid(self):
        return self.connected and self.read_result.quality == tango._tango.AttrQuality.ATTR_VALID

    def is_boolean(self):
        if not self.connected:
            return False
        return isinstance(self.read_result.value, bool)

    def is_scalar(self):
        if not self.connected:
            return False
        return self.config.data_format == tango._tango.AttrDataFormat.SCALAR

    def test_connection(self):
        if not self.connected:
            msg = 'Attribute %s is not connected' % self.full_name
            self.logger.debug(msg)
            raise TangoAttributeConnectionFailed(msg)

    def read(self, force=None, sync=None):
        if force is None:
            force = self.force_read
        if sync is None:
            sync = self.sync_read
        try:
            self.reconnect()
            self.test_connection()
            if force or sync:
                self.read_sync(force)
            else:
                self.read_async()
            self.timeout_count = 0
        except tango.AsynReplyNotArrived:
            # msg = 'AsynReplyNotArrived for %s' % self.full_name
            # self.logger.debug(msg)
            if time.time() - self.read_time > self.read_timeout:
                msg = 'Timeout reading %s' % self.full_name
                self.logger.warning(msg)
                self.read_time = time.time()
                self.timeout_count += 1
                if self.timeout_count >= self.timeout_count_limit:
                    self.read_call_id = None
                    self.disconnect()
                    self.timeout_count = 0
                raise
        except TangoAttributeConnectionFailed:
            self.read_call_id = None
            msg = 'Attribute %s read TangoAttributeConnectionFailed' % self.full_name
            self.logger.info(msg)
            raise
        except:
            msg = 'Attribute %s read Exception %s' % (self.full_name, sys.exc_info()[0])
            self.logger.info(msg)
            self.logger.debug('Exception:', exc_info=True)
            self.read_call_id = None
            self.read_result = None
            self.disconnect()
            raise
        return self.value()

    def read_sync(self, force=False):
        if self.use_history and not force and self.device_proxy.is_attribute_polled(self.attribute_name):
            at = self.device_proxy.attribute_history(self.attribute_name, 1)[0]
            if at.time.totime() > self.read_result.time.totime():
                self.read_result = at
        else:
            self.read_result = self.device_proxy.read_attribute(self.attribute_name)
        # cancel waited async requests
        self.read_call_id = None

    def read_async(self):
        if self.read_call_id is None:
            # no read request before, so send it
            self.read_call_id = self.device_proxy.read_attribute_asynch(self.attribute_name)
            self.read_time = time.time()
            # use previously read result and return
            return
        # check for read request complete (Exception if not completed or error)
        self.read_result = self.device_proxy.read_attribute_reply(self.read_call_id)
        # new read request
        self.read_call_id = self.device_proxy.read_attribute_asynch(self.attribute_name)
        self.read_time = time.time()
        msg = '%s read in %fs' % (self.full_name, time.time() - self.read_time)
        # self.logger.debug(msg)

    def write(self, value, sync=None):
        if self.readonly:
            return
        if sync is None:
            sync = self.sync_write
        try:
            self.reconnect()
            self.test_connection()
            wvalue = self.write_value(value)
            if sync:
                self.write_sync(wvalue)
            else:
                self.write_async(wvalue)
        except tango.AsynReplyNotArrived:
            # msg = 'AsynReplyNotArrived for %s' % self.full_name
            # self.logger.debug(msg)
            if time.time() - self.write_time > self.write_timeout:
                msg = 'Timeout writing %s' % self.full_name
                self.logger.warning(msg)
                self.write_time = time.time()
                self.timeout_count += 1
                if self.timeout_count >= self.timeout_count_limit:
                    self.write_call_id = None
                    self.disconnect()
                    self.timeout_count = 0
                raise
        except TangoAttributeConnectionFailed:
            msg = 'Attribute %s write TangoAttributeConnectionFailed' % self.full_name
            self.logger.info(msg)
            raise
        except:
            msg = 'Attribute %s write Exception %s' % (self.full_name, sys.exc_info()[0])
            self.logger.info(msg)
            self.logger.debug('Exception:', exc_info=True)
            self.disconnect()
            raise

    def write_sync(self, value):
        self.device_proxy.write_attribute(self.attribute_name, value)

    def write_async(self, value):
        if self.write_call_id is None:
            # no request before, so send it
            self.write_call_id = self.device_proxy.write_attribute_asynch(self.attribute_name, value)
        # check for request complete
        self.device_proxy.write_attribute_reply(self.write_call_id)
        # clear call id
        self.write_call_id = None
        msg = '%s write in %fs' % (self.full_name, time.time() - self.read_time)
        # self.logger.debug(msg)

    def value(self):
        if self.read_result is None:
            return None
        if self.is_boolean() or self.read_result.value is None:
            return self.read_result.value
        return self.read_result.value * self.coeff

    def write_value(self, value):
        if self.is_boolean():
            return bool(value)
        return value / self.coeff

    def text(self):
        try:
            txt = self.format % self.value()
        except:
            txt = str(self.value())
        return txt
