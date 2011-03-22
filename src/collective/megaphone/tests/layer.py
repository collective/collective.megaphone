from Testing import ZopeTestCase as ztc
from Testing.ZopeTestCase import app, close, installProduct, installPackage
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.layer import PloneSite
from Products.CMFPlone.tests.utils import MockMailHost
from zope.app.component.hooks import setSite, setHooks
from transaction import commit

try:
    from Products.salesforcebaseconnector.tests import sfconfig
    HAS_SALESFORCE = True
except ImportError:
    HAS_SALESFORCE = False

# BBB Zope 2.12
try:
    from Zope2.App import zcml
    from OFS import metaconfigure
    zcml # pyflakes
    metaconfigure
except ImportError:
    from Products.Five import zcml
    from Products.Five import fiveconfigure as metaconfigure


installProduct('PloneFormGen')
installProduct('salesforcebaseconnector')
installProduct('salesforcepfgadapter')


class Session(dict):
    def set(self, key, value):
        self[key] = value


class MegaphoneLayer(PloneSite):
    
    @classmethod
    def setUp(cls):
        metaconfigure.debug_mode = True
        import collective.megaphone
        zcml.load_config('configure.zcml', collective.megaphone)
        if HAS_SALESFORCE:
            import Products.salesforcepfgadapter
            zcml.load_config('configure.zcml', Products.salesforcepfgadapter)
        metaconfigure.debug_mode = False

        installPackage('plone.app.z3cform')
        installPackage('collective.megaphone')

        root = app()
        portal = root.plone
        
        # set up sessions
        ztc.utils.setupCoreSessions(root)
        root.REQUEST.SESSION = Session()
        
        # add Salesforce base connector
        if HAS_SALESFORCE:
            portal.manage_addProduct['salesforcebaseconnector'].manage_addTool('Salesforce Base Connector', None)
            portal.portal_salesforcebaseconnector.setCredentials(sfconfig.USERNAME, sfconfig.PASSWORD)
        
        # add root user
        root.acl_users.userFolderAddUser('root', 'secret', ['Manager'], [])
        
        # import profiles
        setHooks()
        setSite(portal)
        tool = getToolByName(portal, 'portal_setup')
        tool.runAllImportStepsFromProfile('profile-collective.megaphone:default', purge_old=False)
        if HAS_SALESFORCE:
            tool.runAllImportStepsFromProfile('profile-Products.salesforcepfgadapter:default', purge_old=False)
        setSite(None)

        # use mock mailhost
        portal.MailHost = MockMailHost('MailHost')
        portal.email_from_address = 'test@example.com'

        # and commit the changes
        commit()
        close(root)


    @classmethod
    def tearDown(cls):
        pass
