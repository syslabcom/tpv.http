from __future__ import absolute_import

import json
import os
import sys
import traceback

from pyramid.config import Configurator
from webtest import TestApp

from tpv.testing import unittest

from .pyramid import Integration


# optional environment variables
DEBUG = bool(os.environ.get('DEBUG'))
KEEP_FAILED = bool(os.environ.get('KEEP_FAILED'))


class TestCase(unittest.TestCase):
    def setUp(self):
        try:
            self._setUp()
        except Exception, e:
            # XXX: working around nose to get immediate exception
            # output, instead of collected after all tests are run
            sys.stderr.write("""
======================================================================
Error setting up testcase: %s
----------------------------------------------------------------------
%s
""" % (str(e), traceback.format_exc()))
            self.tearDown()
            raise e

    def _setUp(self):
        """start pyramid server with ordereddict backend

        XXX: switch to nodes that serialize to disk
        """
        # self.basedir = '/'.join(['var', self.id()])
        # os.mkdir(self.basedir)

        # datadir = '/'.join([self.basedir, 'data'])
        # os.mkdir(datadir)
        if not hasattr(self, 'APP'):
            return

        self.pyramid_config = Configurator()
        self.pyramid_config.add_notfound_view(Integration(self.APP))
        self.app = TestApp(self.pyramid_config.make_wsgi_app())

    def test_declarative(self):
        # XXX: turn this into tests that show up individually
        specs = getattr(self, 'SPECS', ())
        for spec in specs:
            resp = getattr(self.app, spec.method.lower())(spec.url)
            name = '%s %s' % (spec.method, spec.url)
            expected_json = json.dumps(spec.response)
            self.assertEqual(resp.body, expected_json, msg=name)

    # def tearDown(self):
    #     successful = sys.exc_info() == (None, None, None)
    #     if successful or not KEEP_FAILED:
    #         shutil.rmtree(self.basedir)
