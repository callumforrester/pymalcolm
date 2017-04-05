from malcolm.core import Error, Return, Put
from malcolm.gui.baseitem import BaseItem


class AttributeItem(BaseItem):

    def get_value(self):
        return str(self.ref.value)

    def get_writeable(self):
        return self.ref.meta.writeable

    def set_value(self, value):
        self._state = self.RUNNING
        request = Put(path=self.endpoint + ("value",), value=str(value))
        return request

    def handle_response(self, response):
        if isinstance(response, Error):
            self._state = self.ERROR
        elif isinstance(response, Return):
            self._state = self.IDLE
        else:
            raise TypeError(type(response))
