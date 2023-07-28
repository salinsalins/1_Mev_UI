from PyQt5.QtWidgets import QPushButton
from .TangoLED import TangoLED


class Timer_on_LED(TangoLED):
    def __init__(self, name, widget: QPushButton, number_of_channels=12):
        self.timer_state_channels = ['channel_state'+str(k) for k in range(number_of_channels)]
        self.value = False
        super().__init__(name, widget)

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
        return state
