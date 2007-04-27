#!/usr/bin/env python

from inspect import *

class Wrapper(object):
    def __call__(self, *args, **kws):
        print args
        print kws
        print 'Wrapper'
        print type(self)


def dec(fn):
    def wrapper(*args, **kws):
        print 'dec.wrapper'
        fn(*args,**kws)
    return Wrapper()

@dec
def testf(a):
    print 'testfunc'
    print a


class TC(object):
    @dec
    def testf(self):
        pass

testf(1)
tc = TC()
tc.testf(1)
print type(tc.testf)
