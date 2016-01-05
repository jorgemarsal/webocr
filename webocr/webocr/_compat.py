import sys

PY2 = sys.version_info[0] == 2
_identity = lambda x: x

if not PY2:
    text_type = str
    string_types = (str,)
    integer_types = (int,)

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    implements_to_string = _identity

else:
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls


def to_bytes(bytes_or_str, encoding='utf-8'):
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode(encoding)
    else:
        value = bytes_or_str
    return value


def to_string(bytes_or_str, encoding='utf-8'):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode(encoding)
    else:
        value = bytes_or_str
    return value
