import doctest
import unittest
import email

from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
import collective.megaphone
import Products.salesforcepfgadapter

from Products.SecureMailHost.SecureMailHost import SecureMailHost

try:
    from Products.salesforcebaseconnector.tests import sfconfig
    HAS_SALESFORCE = True
except ImportError:
    HAS_SALESFORCE = False

class MailHostMock(SecureMailHost):
    """
    mock up the send method so that emails do not actually get sent
    during unit tests we can use this to verify that the notification
    process is still working as expected
    """
    def __init__(self, id):
        SecureMailHost.__init__(self, id, smtp_notls=True)
        self.mails = []
    def send(self, mail_text):
        mfile=mail_text.lstrip()
        mo = email.message_from_string(mfile)
        self.mails.append(mo)

ztc.installProduct('PloneFormGen')
ztc.installProduct('salesforcebaseconnector')
ztc.installProduct('salesforcepfgadapter')

@onsetup
def load_zcml():
    zcml.load_config('configure.zcml', collective.megaphone)
    zcml.load_config('configure.zcml', Products.salesforcepfgadapter)
    ztc.installPackage('collective.megaphone')

load_zcml()
ptc.setupPloneSite(products=['salesforcepfgadapter', 'collective.megaphone'])

class MegaphoneFunctionalTestCase(ptc.FunctionalTestCase):
    """Base class for functional integration tests for collective.megaphone.
    This may provide specific set-up and tear-down operations, or provide 
    convenience methods.
    
    Borrowed from PloneGetPaid to set up sessions for use in doc tests.
    """
    
    def afterSetUp(self):
        # Set up sessioning objects
        ztc.utils.setupCoreSessions(self.app)
        
    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        ptc.FunctionalTestCase._setup(self)
        self.app.REQUEST['SESSION'] = self.Session()
        
        self.portal.MailHost = MailHostMock('MailHost')
        self.mailhost = self.portal.MailHost
        
        self.portal.manage_addProduct['salesforcebaseconnector'].manage_addTool('Salesforce Base Connector', None)
        if HAS_SALESFORCE:
            self.portal.portal_salesforcebaseconnector.setCredentials(sfconfig.USERNAME, sfconfig.PASSWORD)
        else:
            print "** SALESFORCE NOT CONFIGURED -- SKIPPING TESTS **"

def test_suite():
    tests = []
    if HAS_SALESFORCE:
        tests.append(
            ztc.FunctionalDocFileSuite(
                'letter.txt', package='collective.megaphone.tests',
                test_class=MegaphoneFunctionalTestCase,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        )
    else:
        tests.append(
            ztc.FunctionalDocFileSuite(
                'letter_no_salesforce.txt', package='collective.megaphone.tests',
                test_class=MegaphoneFunctionalTestCase,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        )
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
