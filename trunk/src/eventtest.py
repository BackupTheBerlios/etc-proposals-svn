#!/usr/bin/env python

def signal(signal, *args):
    print 'signal %s' % signal
    print  args
    def eventhandler():
        def handle_event(self, *args, **kws):
            handlersname = 'on_%s' % signal.__name__
            handlers = self.__dict__[handlersname]
            [handler(*args, **kws) for handler in handlers]
        he = handle_event
        he.__signal__ = True
        return he
    return eventhandler()
        

class TestClass(object):
    def __init__(self):
        print 'TestClass.__init__'
    @signal
    def changed(self):
        pass
    @signal
    def moved(self, x, y):
        pass


class TestClass2(object):
    def __init__(self, tc):
        tc.on_moved.append(self.moved)
        
    def moved(self, x, y):
        print 'TC2: %d %d '% (x, y)

def testfunc():
    print 'testfunc'

def movedfunc(x,y):
    print 'moved: %d %d' % (x, y)

t = TestClass()
print 't.init'
print [el for el in TestClass.__dict__]
print TestClass.__dict__['moved'].__dict__
t.on_changed = []
t.on_moved = []
tc2 = TestClass2(t)
print '------'
t.on_changed.append(testfunc)
t.on_moved.append(movedfunc)
t.changed()
t.moved(1,2)
    
print '------'
t.on_changed.append(testfunc)
t.changed()
print '------'
    
