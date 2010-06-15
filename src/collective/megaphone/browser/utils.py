from Products.Five import BrowserView

try:
    from plone.app.upgrade import v40
    HAS_PLONE40 = True
except ImportError:
    HAS_PLONE40 = False

class MegaphoneUtils(BrowserView):
    
    def is_plone4(self):
        return HAS_PLONE40
