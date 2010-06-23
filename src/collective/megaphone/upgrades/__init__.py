from zope.interface import noLongerProvides, alsoProvides
from Products.CMFCore.utils import getToolByName
from collective.megaphone.interfaces import IActionLetter, IMegaphone

def null_upgrade_step(context):
    pass

def upgrade1to2(context):
    context = getToolByName(context, "portal_setup")
    context.runAllImportStepsFromProfile('collective.megaphone.upgrades:1to2', purge_old=False)

def update_marker_interface(context):
    catalog = getToolByName(context, 'portal_catalog')
    res = catalog.unrestrictedSearchResults(object_provides=IActionLetter.__identifier__)
    for brain in res:
        obj = brain.getObject()
        noLongerProvides(obj, IActionLetter)
        alsoProvides(obj, IMegaphone)

# XXX make sure plone.app.z3cform is installed
