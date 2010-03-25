#
# Test megaphone initialisation and set-up
#
from Products.CMFCore.utils import getToolByName

from base import IntegrationTestCase

class TestInstallation(IntegrationTestCase):
    """Ensure product is properly installed"""

    def testCssInstalled(self):
        assert 'wizard.css' in self.portal.portal_css.getResourceIds()

    def testJsInstalled(self):
        assert 'wizard.js' in self.portal.portal_javascripts.getResourceIds()

    def testSkinLayersInstalled(self):
        """"Make sure skin is installed"""
        assert 'megaphone' in self.portal.portal_skins.objectIds()
        assert 'wizard.css' in self.portal.portal_skins['megaphone'].objectIds()

    def testMetaTypesNotToList(self):
        assert 'LetterRecipientMailerAdapter' in self.portal.portal_properties.navtree_properties.metaTypesNotToList

    def testTypesInstalled(self):
        assert 'Action Letter' in self.portal.portal_types.objectIds()
        assert 'LetterRecipientMailerAdapter' in self.portal.portal_types.objectIds()

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestInstallation))
    return suite
