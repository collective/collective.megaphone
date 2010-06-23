from zope.interface import noLongerProvides, alsoProvides, implements
from Products.CMFCore.utils import getToolByName
from Products.CMFQuickInstallerTool.interfaces import INonInstallable
from collective.megaphone.interfaces import IActionLetter, IMegaphone


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

def update_marker_interface(context):
    catalog = getToolByName(context, 'portal_catalog')
    res = catalog.unrestrictedSearchResults(object_provides=IActionLetter.__identifier__)
    for brain in res:
        obj = brain.getObject()
        noLongerProvides(obj, IActionLetter)
        alsoProvides(obj, IMegaphone)

# XXX make sure plone.app.z3cform is installed
