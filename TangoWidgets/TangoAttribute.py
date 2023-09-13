# coding: utf-8
"""
Created on Feb 4, 2020

@author: sanin
"""
import logging
import sys
import time

import tango
from tango import DevFailed, DevLong

from TangoUtils import split_attribute_name
from config_logger import config_logger
from log_exception import log_exception


# from .Utils import *


class TangoAttributeConnectionFailed(tango.ConnectionFailed):
    pass


class TangoAttribute:
    devices = {}

    def __init__(self, name: str, level=logging.DEBUG, readonly=False, use_history=True, **kwargs):
        # configure logging
        self.logger = kwargs.get('logger', config_logger(level=level))
        self.time = time.time()
        self.full_name = str(name)
        self.device_name, self.attribute_name = split_attribute_name(self.full_name)
        self.device_proxy = None
        self.connected = False
        self.reconnect_timeout = 5.0
        self.read_result = None
        self.config = None
        self.format = None
        self.coeff = 1.0
        self.readonly = readonly
        self.force_read = False
        self.use_history = use_history
        self.history_valid_time = kwargs.get('history_valid_time', 0.3)
        self.attribute_polled = False
        # async operation vars
        self.sync_read = False
        self.sync_write = True
        self.read_call_id = None
        self.write_call_id = None
        self.read_timeout = 3.5
        self.write_timeout = 3.5
        self.read_time = 0.0
        self.write_time = 0.0
        # connect attribute
        self.connect()

    def connect(self):
        self.time = time.time()
        try:
            self.device_proxy = self.create_device_proxy()
            if self.device_proxy is None:
                self.disconnect()
                return False
            if hasattr(self.device_proxy, 'device_type') and self.device_proxy.device_type == "Uninitialized":
                self.disconnect()
                return False
            if not self.attribute_name:
                self.connected = True
                self.logger.debug('%s has been connected for device only' % self.full_name)
                return True
            self.set_config()
            # t0 = time.time()
            # try:
            #     self.read_async()
            # while self.read_call_id is not None and time.time() - t0 < 0.1:
            #     self.read_async()
            # if self.read_call_id is not None:
            #     self.read_result = DeviceAttribute()
            #     self.read_result.value = None
            # self.read_result = self.device_proxy.read_attribute(self.attribute_name)
            # self.read_result = DeviceAttribute()
            # self.read_result.value = None
            # self.read_async()
            self.connected = True
            self.logger.debug('Attribute %s has been connected' % self.full_name)
            return True
        except KeyboardInterrupt:
            raise
        except DevFailed:
            log_exception('Can not connect attribute %s' % self.full_name, no_info=True)
            self.disconnect()
            return False

    def disconnect(self):
        if not self.connected:
            return
        self.connected = False
        # self.device_proxy = None
        self.logger.debug('Attribute %s has been disconnected', self.full_name)

    def reconnect(self):
        if self.connected:
            return True
        if self.device_name in TangoAttribute.devices and TangoAttribute.devices[
            self.device_name] is not self.device_proxy:
            self.logger.debug('Device proxy changed for %s' % self.full_name)
            self.disconnect()
            if time.time() - self.time > self.reconnect_timeout:
                self.connect()
        if self.connected:
            return True
        if time.time() - self.time > self.reconnect_timeout:
            self.logger.debug('Reconnection timeout exceeded for %s' % self.full_name)
            self.connect()
        return self.connected

    def create_device_proxy(self):
        if self.device_name in TangoAttribute.devices:
            try:
                # check if device is alive
                pt = TangoAttribute.devices[self.device_name].ping()
                # self.logger.debug('Device %s for %s exists', self.device_name, self.attribute_name)
            except KeyboardInterrupt:
                raise
            except DevFailed:
                self.logger.info('Device %s can not be reached', self.device_name)
            return TangoAttribute.devices[self.device_name]
        try:
            dp = tango.DeviceProxy(self.device_name)
            TangoAttribute.devices[self.device_name] = dp
            self.logger.info('Device proxy for %s has been created' % self.device_name)
            return dp
        # except KeyboardInterrupt:
        #     raise
        except DevFailed:
            log_exception('Device %s creation exception: ' % self.device_name, no_info=True)
            return None

    def set_config(self):
        self.coeff = 1.0
        self.config = None
        self.format = None
        self.readonly = None
        self.attribute_polled = None
        if self.device_proxy is None:
            return
        self.config = self.device_proxy.get_attribute_config_ex(self.attribute_name)[0]
        self.format = self.config.format
        try:
            self.coeff = float(self.config.display_unit)
        except KeyboardInterrupt:
            raise
        except:
            self.coeff = 1.0
        self.readonly = self.readonly or self.is_readonly()
        self.attribute_polled = self.device_proxy.is_attribute_polled(self.attribute_name)

    def is_readonly(self):
        try:
            return self.config.writable == tango.AttrWriteType.READ
        except KeyboardInterrupt:
            raise
        except:
            return True

    def is_valid(self):
        try:
            return self.connected and self.read_result.quality == tango.AttrQuality.ATTR_VALID
        except KeyboardInterrupt:
            raise
        except:
            return False

    def is_boolean(self):
        try:
            return self.connected and isinstance(self.read_result.value, bool)
        except KeyboardInterrupt:
            raise
        except:
            return False

    def is_scalar(self):
        try:
            return self.connected and self.config.data_format == tango.AttrDataFormat.SCALAR
        except KeyboardInterrupt:
            raise
        except:
            return False

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
            if not self.connected:
                raise TangoAttributeConnectionFailed('Attribute is not connected')
            if force or sync:
                self.read_sync(True)
            else:
                self.read_async()
        except tango.AsynReplyNotArrived:
            if time.time() - self.read_time > self.read_timeout:
                self.logger.warning('Timeout reading %s', self.full_name)
                self.cancel_asynch_request(self.read_call_id)
                self.read_result = None
                # self.disconnect()
                raise
        except TangoAttributeConnectionFailed:
            # self.logger.info('Attribute %s read Connection Failed' % self.full_name)
            self.cancel_asynch_request(self.read_call_id)
            self.read_result = None
            self.disconnect()
            raise
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger, 'Attribute %s read Exception:', self.full_name)
            self.cancel_asynch_request(self.read_call_id)
            self.read_result = None
            self.disconnect()
            raise
        return self.value()

    def cancel_asynch_request(self, read_call_id=None):
        if read_call_id is None:
            read_call_id = self.read_call_id
        if read_call_id is None:
            return
        try:
            self.device_proxy.cancel_asynch_request(read_call_id)
        except KeyboardInterrupt:
            raise
        except:
            log_exception()
        self.read_call_id = None

    def read_sync(self, force=False):
        self.read_result = None
        # process waited async requests
        if self.read_call_id is not None:
            try:
                self.read_result = self.device_proxy.read_attribute_reply(self.read_call_id)
                self.read_call_id = None
                return
            except KeyboardInterrupt:
                raise
            except tango.AsynReplyNotArrived:
                self.cancel_asynch_request(self.read_call_id)
        if self.use_history and not force and self.attribute_polled:
            at = self.device_proxy.attribute_history(self.attribute_name, 1)[0]
            t = at.time.totime()
            if t > self.read_result.time.totime() and t >= (time.time() - self.history_valid_time):
                self.read_result = at
        else:
            self.read_result = self.device_proxy.read_attribute(self.attribute_name)

    def read_async(self):
        if self.read_call_id is not None:
            # check if read request complete (Exception if not completed or error)
            self.read_result = self.device_proxy.read_attribute_reply(self.read_call_id)
            self.read_call_id = None
        # new read request
        self.read_call_id = self.device_proxy.read_attribute_asynch(self.attribute_name)
        self.read_time = time.time()

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
            if time.time() - self.write_time > self.write_timeout:
                msg = 'Timeout writing %s' % self.full_name
                self.logger.warning(msg)
                if self.write_call_id is not None:
                    self.device_proxy.cancel_asynch_request(self.write_call_id)
                self.write_call_id = None
                self.disconnect()
                raise
        except TangoAttributeConnectionFailed:
            msg = 'Attribute %s write TangoAttributeConnectionFailed' % self.full_name
            self.logger.info(msg)
            raise
        except KeyboardInterrupt:
            raise
        except:
            msg = 'Attribute %s write Exception %s' % (self.full_name, sys.exc_info()[0])
            self.logger.info(msg)
            self.logger.debug('Exception:', exc_info=True)
            if self.write_call_id is not None:
                self.device_proxy.cancel_asynch_request(self.write_call_id)
            self.write_call_id = None
            self.disconnect()
            raise

    def write_sync(self, value):
        v = value
        if self.read_result.type == DevLong:
            v = int(value)
        self.device_proxy.write_attribute(self.attribute_name, v)

    def write_async(self, value):
        if self.write_call_id is None:
            # no request before, so send it
            self.write_call_id = self.device_proxy.write_attribute_asynch(self.attribute_name, value)
            self.write_time = time.time()
        # check for request complete
        self.device_proxy.write_attribute_reply(self.write_call_id)
        # clear call id
        self.write_call_id = None
        # msg = '%s write in %fs' % (self.full_name, time.time() - self.read_time)
        # self.logger.debug(msg)

    def value(self):
        v = None
        try:
            v = self.read_result.value
            v *= self.coeff
        except KeyboardInterrupt:
            raise
        except:
            pass
        return v
        # try:
        #     return self.read_result.value
        # except KeyboardInterrupt:
        #     raise
        # except:
        #     return None

    def valid_value(self):
        v = self.value()
        if v is None or not self.is_valid():
            return None
        return v

    def write_value(self, value):
        if self.is_boolean():
            return bool(value)
        return value / self.coeff

    def text(self):
        try:
            txt = self.format % self.value()
        except KeyboardInterrupt:
            raise
        except:
            txt = str(self.value())
        return txt


if __name__ == '__main__':
    an = 'sys/test/1/double_scalar'
    attr = TangoAttribute(an)
    attr.read()
