from zope.interface import noLongerProvides, alsoProvides, implements
from Products.CMFCore.utils import getToolByName
from Products.CMFQuickInstallerTool.interfaces import INonInstallable
from collective.megaphone.interfaces import IActionLetter, IMegaphone
from collective.megaphone.setuphandlers import set_add_view_expr


class HiddenProducts(object):
    """This hides the upgrade profiles from the quick installer tool."""
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return ['collective.megaphone.upgrades']


def null_upgrade_step(context):
    pass

def upgrade1to2(context):
    context = getToolByName(context, "portal_setup")
    context.runAllImportStepsFromProfile('profile-collective.megaphone.upgrades:1to2', purge_old=False)
    
    update_marker_interface(context)

def update_marker_interface(context):
    catalog = getToolByName(context, 'portal_catalog')
    res = catalog.unrestrictedSearchResults(object_provides=IActionLetter.__identifier__)
    for brain in res:
        obj = brain.getObject()
        noLongerProvides(obj, IActionLetter)
        alsoProvides(obj, IMegaphone)

def install_plone_app_z3cform(context):
    qi = getToolByName(context, 'portal_quickinstaller')
    if qi.isProductInstallable('plone.app.z3cform'):
        qi.installProduct('plone.app.z3cform')

def rename_type(context):
    # delete the Action Letter type
    ttool = getToolByName(context, 'portal_types')
    ttool.manage_delObjects('Action Letter')
    # import the Megaphone action type
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile('profile-collective.megaphone:default', 'typeinfo', run_dependencies=False, purge_old=False)
    set_add_view_expr(context)
    # update properties
    context.runAllImportStepsFromProfile('profile-collective.megaphone.upgrades:2to3', purge_old=False)
    # update instances
    catalog = getToolByName(context, 'portal_catalog')
    res = catalog.unrestrictedSearchResults(object_provides=IMegaphone.__identifier__)
    for brain in res:
        obj = brain.getObject()
        obj.portal_type = 'Megaphone Action'
        obj.reindexObject()

def upgrade2to3(context):
    install_plone_app_z3cform(context)
    rename_type(context)

def upgrade_jquerytools(context):
    qi = getToolByName(context, 'portal_quickinstaller')
    qi.upgradeProduct('plone.app.jquerytools')
