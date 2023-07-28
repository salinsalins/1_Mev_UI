from PyQt5.QtWidgets import QPushButton

from TangoAttribute import TangoAttribute
from log_exception import log_exception
from .TangoLED import TangoLED


class Timer_on_LED(TangoLED):
    def __init__(self, name, widget: QPushButton, number_of_channels=12):
        self.timer_state_channels = ['channel_state' + str(k) for k in range(number_of_channels)]
        self.value = False
        self.use_state = False
        self.elapsed = TangoAttribute('binp/nbi/adc0/Elapsed')
        self.enable = []
        self.stop = []
        super().__init__(name, widget)
        al = self.attribute.device_proxy.get_attribute_list()
        al = list(al)
        al.sort()
        if 'channel_state0' in al:
            self.use_state = True
            # self.elapsed = None
            self.enable = []
            self.stop = []
        else:
            self.use_state = False
            # self.elapsed = TangoAttribute('binp/nbi/adc0/Elapsed')
            self.enable = [TangoAttribute('binp/nbi/timing/' + i) for i in al if 'channel_enable' in i]
            self.stop = [TangoAttribute('binp/nbi/timing/' + i) for i in al if 'pulse_stop' in i]

    def read(self, force=False):
        self.value = self.check_state()
        return self.value

    def set_widget_value(self):
        self.widget.setEnabled(self.value)
        return self.widget.isEnabled()

    def decorate(self):
        self.set_widget_value()

    def check_state(self):
        timer_device = self.attribute.device_proxy
        if timer_device is None:
            return False
        if self.use_state:
            avs = []
            try:
                avs = timer_device.read_attributes(self.timer_state_channels)
            except KeyboardInterrupt:
                raise
            except:
                pass
            state = False
            for av in avs:
                state = bool(av.value) or state
            self.logger.debug('%s %s', state)
            return state
        else:
            # return False
            max_time = 0.0
            try:
                for i in range(len(self.enable)):
                    self.enable[i].read_sync(True)
                    if self.enable[i].value():
                        self.stop[i].read_sync(True)
                        max_time = max(max_time, self.stop[i].value())
                # during pulse
                # if self.timer_on_led.value:   # pulse is on
                # self.logger.debug('%s %s', self.elapsed.value(), max_time)
                if self.elapsed.value() < max_time / 1000.0:
                    return True
                else:  # pulse is off
                    return False
            except KeyboardInterrupt:
                raise
            except:
                # log_exception('********')
                return False

    def update(self, decorate_only=False) -> None:
        return
