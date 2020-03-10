from PyQt5.QtWidgets import QPushButton
import tango
from .TangoAttribute import TangoAttribute
from.TangoLED import TangoLED


class RF_ready_LED(TangoLED):
    def __init__(self, name, widget: QPushButton):
        super().__init__(name, widget)
        self.av = TangoAttribute('binp/nbi/adc0/chan16')
        self.cc = TangoAttribute('binp/nbi/adc0/chan22')
        self.pr = TangoAttribute('binp/nbi/timing/di60')

    def set_widget_value(self):
        try:
            self.av.read(True)
            self.cc.read(True)
            self.pr.read(True)
            if not self.av.is_valid() or self.av.value() < 8.0 or \
                    not self.cc.is_valid() or self.cc.value() < 0.1 or \
                    not self.pr.value():
                self.widget.setChecked(False)
            else:
                self.widget.setChecked(True)
        except:
            self.widget.setChecked(False)
        return self.attribute.value()
