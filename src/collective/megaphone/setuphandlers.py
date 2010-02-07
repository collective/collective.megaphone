from Products.CMFCore.utils import getToolByName
from collective.megaphone import HAS_PLONE40

def set_add_view_expr(gscontext):
    # in Plone 4, the Action Letter FTI needs to have the add_view_expr set.
    if HAS_PLONE40:
        ttool = getToolByName(gscontext, 'portal_types')
        ttool['Action Letter']._updateProperty(
            'add_view_expr',
            'string:${folder_url}/+/addActionLetter'
            )

def importVarious(gscontext):
    # don't run as a step for other profiles
    if gscontext.readDataFile('is_megaphone_profile.txt') is None:
        return
    
    set_add_view_expr(gscontext)
