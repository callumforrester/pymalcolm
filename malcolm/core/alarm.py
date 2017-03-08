from malcolm.compat import str_
from .serializable import Serializable, deserialize_object


def sort_names(d):
    return list(sorted(d, key=d.__getitem__))


class AlarmSeverity(object):
    NO_ALARM, MINOR_ALARM, MAJOR_ALARM, INVALID_ALARM, UNDEFINED_ALARM = \
        range(5)
    names = sort_names(locals())


class AlarmStatus(object):
    NO_STATUS, DEVICE_STATUS, DRIVER_STATUS, RECORD_STATUS, DB_STATUS, \
        CONF_STATUS, UNDEFINED_STATUS, CLIENT_STATUS = range(8)
    names = sort_names(locals())


@Serializable.register_subclass("alarm_t")
class Alarm(Serializable):

    endpoints = ["severity", "status", "message"]

    def __init__(self, severity=AlarmSeverity.NO_ALARM,
                 status=AlarmStatus.NO_STATUS, message=""):
        # Set initial values
        assert severity in range(len(AlarmSeverity.names)), \
            "Expected AlarmSeverity.*_ALARM, got %r" % severity
        self.severity = severity
        assert status in range(len(AlarmStatus.names)), \
            "Expected AlarmStatus.*_STATUS, got %r" % status
        self.status = status
        self.message = deserialize_object(message, str_)
