import types
import simplejson
from decimal import *
import datetime

json_parse = lambda s: simplejson.loads(s.decode("utf-8"))

class DateTimeAwareJSONEncoder(simplejson.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time types
    """
    
    DATE_FORMAT = "%Y-%m-%d" 
    TIME_FORMAT = "%H:%M:%S"
    
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        else:
            return super(DateTimeAwareJSONEncoder, self).default(o)

def json_encode(data,**kwargs):
    """
    The main issues with default json serializer is that properties that
    had been added to a object dynamically are being ignored (and it also has 
    problems with some models).
    """

    def _any(data):
        ret = None
        if type(data) is types.ListType:
            ret = _list(data)
        elif type(data) is types.DictType:
            ret = _dict(data)
        elif isinstance(data, Decimal):
            # simplejson.dumps() cant handle Decimal
            ret = str(data)
        else:
            ret = data
        return ret
    
    def _list(data):
        ret = []
        for v in data:
            ret.append(_any(v))
        return ret
    
    def _dict(data):
        ret = {}
        for k,v in data.items():
            ret[k] = _any(v)
        return ret
    
    ret = _any(data)
    if kwargs.get('nice'):
        return simplejson.dumps(ret, cls=DateTimeAwareJSONEncoder, indent=4, ensure_ascii=False)
    else:
        return simplejson.dumps(ret, cls=DateTimeAwareJSONEncoder, ensure_ascii=False)