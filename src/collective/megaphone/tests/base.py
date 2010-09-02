import email
from Testing import ZopeTestCase as ztc
from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Products.Five.testbrowser import Browser

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

# Let Zope know about the two products we require above-and-beyond a basic
# Plone install (PloneTestCase takes care of these).
ztc.installProduct('PloneFormGen')
ztc.installProduct('salesforcebaseconnector')
ztc.installProduct('salesforcepfgadapter')
ztc.installProduct('collective.megaphone')

@onsetup
def load_zcml():
    import collective.megaphone
    zcml.load_config('configure.zcml', collective.megaphone)
    if HAS_SALESFORCE:
        import Products.salesforcepfgadapter
        zcml.load_config('configure.zcml', Products.salesforcepfgadapter)
    
    ztc.installPackage('plone.app.z3cform')
    ztc.installPackage('collective.megaphone')

load_zcml()
ptc.setupPloneSite(products=['salesforcepfgadapter', 'collective.megaphone'])

class MegaphoneTestCase(ptc.FunctionalTestCase):
    """Base class for functional integration tests for collective.megaphone.
    This may provide specific set-up and tear-down operations, or provide 
    convenience methods.

    Borrowed from PloneGetPaid to set up sessions for use in doc tests.
    """

    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        ptc.FunctionalTestCase._setup(self)
        ztc.utils.setupCoreSessions(self.app)
        self.app.REQUEST['SESSION'] = self.Session()

        self.portal.MailHost = MailHostMock('MailHost')
        self.mailhost = self.portal.MailHost
        self.portal.email_from_address = 'test@example.com'

        if HAS_SALESFORCE:
            self.portal.manage_addProduct['salesforcebaseconnector'].manage_addTool('Salesforce Base Connector', None)
            self.portal.portal_salesforcebaseconnector.setCredentials(sfconfig.USERNAME, sfconfig.PASSWORD)
        
        self.app.acl_users.userFolderAddUser('root', 'secret', ['Manager'], [])

    def _create_megaphone(self, type='letter'):
        browser = Browser()
        browser.handleErrors = False
        browser.addHeader('Authorization', 'Basic root:secret')
        browser.open('http://nohost/plone')
        browser.getLink('Megaphone Action').click()
        browser.getControl(name='intro.widgets.megaphone_type:list').value = [type]
        browser.getControl('Continue').click()
        browser.getControl('Title').value = 'Megaphone'
        browser.getControl('Continue').click()
        browser.getControl(name='crud-edit.captcha.widgets.select:list').value = ['true']
        browser.getControl('Delete').click()
        while 1:
            try:
                browser.getControl('Continue').click()
            except LookupError:
                break
        browser.getControl('Finish').click()
        browser.open('http://nohost/plone/megaphone')
        browser.getLink('Publish').click()

class MegaphoneFunctionalTestCase(MegaphoneTestCase):
    # We need a separate class for use with FunctionalDocFileSuite, or else
    # the default test loader finds the dummy runTest method it adds
    # when the case is subsequently used by another sort of test suite. o.O
    pass
