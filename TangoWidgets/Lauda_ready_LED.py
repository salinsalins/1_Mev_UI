from PyQt5.QtWidgets import QPushButton
from .TangoAttribute import TangoAttribute
from.TangoLED import TangoLED


class Lauda_ready_LED(TangoLED):
    def __init__(self, name, widget, valve='valve_state', pump='pump'):
        self.value = False
        if not name.endswith('/'):
            name += '/'
        if '/' in valve:
            valve_name = valve
        else:
            valve_name = name + valve
        if '/' in pump:
            pump_name = pump
        else:
            pump_name = name + pump
        self.valve = TangoAttribute(valve_name)  # output valve
        self.motor = TangoAttribute(pump_name)  # pump motor
        super().__init__(pump_name, widget)
        # self.motor = self.attribute  # Lauda pump motor

    def read(self, force=True):
        self.value = self.motor.read(force) and self.valve.read(force)
        return self.value

    def decorate(self):
        self.set_widget_value()

    def set_widget_value(self):
        try:
            if self.valve.is_valid() and self.motor.is_valid() and self.value:
                self.widget.setChecked(True)
            else:
                self.widget.setChecked(False)
        except KeyboardInterrupt:
           raise
        except:
            self.widget.setChecked(False)
        return self.widget.isChecked()
