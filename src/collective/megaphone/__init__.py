from zope.i18nmessageid import MessageFactory
from Products.CMFCore import utils
from Products.Archetypes import atapi
from collective.megaphone import config

DOMAIN = 'collective.megaphone'
MegaphoneMessageFactory = MessageFactory(DOMAIN)

def initialize(context):

    from collective.megaphone.content import letterrecipientmaileradapter

    content_types, constructors, ftis = atapi.process_types(
        atapi.listTypes(config.PROJECTNAME),
        config.PROJECTNAME)

    for atype, constructor in zip(content_types, constructors):
        utils.ContentInit('%s: %s' % (config.PROJECTNAME, atype.portal_type),
            content_types      = (atype,),
            permission         = config.ADD_PERMISSIONS[atype.portal_type],
            extra_constructors = (constructor,),
            ).initialize(context)

try:
    from plone.app.upgrade import v40
    v40 # shut up pyflakes
    HAS_PLONE40 = True
except ImportError:
    HAS_PLONE40 = False

# BBB for Z2 vs Z3 interfaces checks
def implementedOrProvidedBy(anInterface, anObject):
    if HAS_PLONE40:
        return anInterface.providedBy(anObject)
    else:
        return anInterface.isImplementedBy(anObject)
