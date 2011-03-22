from persistent import Persistent
from zope.app.component.hooks import getSite
from zope.i18nmessageid import MessageFactory

DOMAIN = 'collective.megaphone'
MegaphoneMessageFactory = MessageFactory(DOMAIN)

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


class MegaphoneSettings(Persistent):
    def __init__(self, base={}):
        data = {}
        data.update(base)
        if 'step' in data:
            del data['step']
        self.data = data


def get_megaphone_defaults():
    return getattr(getSite(), '_megaphone_defaults', MegaphoneSettings()).data

def set_megaphone_defaults(defaults):
    getSite()._megaphone_defaults = MegaphoneSettings(defaults)
