from Products.CMFCore.utils import getToolByName
from collective.megaphone import HAS_PLONE40

def set_add_view_expr(context):
    # in Plone 4, the Megaphone Action FTI needs to have the add_view_expr set.
    if HAS_PLONE40:
        ttool = getToolByName(context, 'portal_types')
        ttool['Megaphone Action']._updateProperty(
            'add_view_expr',
            'string:${folder_url}/+/addMegaphoneAction'
            )

def importVarious(gscontext):
    # don't run as a step for other profiles
    if gscontext.readDataFile('is_megaphone_profile.txt') is None:
        return
    
    site = gscontext.getSite()
    set_add_view_expr(site)
