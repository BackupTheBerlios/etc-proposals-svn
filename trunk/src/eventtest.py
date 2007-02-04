#!/usr/bin/env python

def eventhandler(f, *args, **kws):
    handlersname = 'on_%s' % f.__name__
    def wrapper(*args, **kws):
        handlers = [None]
        if args[0].__dict__.has_key(handlersname):
            handlers = list(args[0].__dict__[handlersname])
        if handlers.count(None) == 0:
            handlers.insert(0, None)
        for handler in handlers:
            if handler == None:
                result = f(*args, **kws)
            else:
                handler(*args, **kws)
        return result
    return wrapper

class TestClass(object):
    @eventhandler
    def changed(self):
        print 'TestClass.on_changed'

def testfunc(sender):
    print 'testfunc'

t = TestClass()
print '------'
t.changed()
print '------'
t.on_changed = [testfunc, testfunc]
t.changed()
print '------'
t.on_changed = [testfunc, None, None, testfunc]
t.changed()
print '------'
    
