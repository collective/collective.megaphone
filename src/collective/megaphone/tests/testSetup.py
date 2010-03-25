#
# Test megaphone initialisation and set-up
#
from Products.CMFCore.utils import getToolByName

from base import IntegrationTestCase

class TestInstallation(IntegrationTestCase):
    """Ensure product is properly installed"""

    def testSkinLayersInstalled(self):
        """"Make sure skin is installed"""
        self.failUnless('megaphone' in self.portal.portal_skins.objectIds())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestInstallation))
    return suite
