#! /usr/bin/python
import unittest
import portage_stubs_test
import etcproposals_lib_test

alltests = [portage_stubs_test.alltestssuite, etcproposals_lib_test.alltestssuite]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.TextTestRunner(descriptions=10, verbosity=10).run(alltestssuite)
