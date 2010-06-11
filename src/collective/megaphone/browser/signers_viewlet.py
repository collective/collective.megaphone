from zope.annotation.interfaces import IAnnotations
from plone.app.layout.viewlets.common import ViewletBase
from collective.megaphone.config import ANNOTATION_KEY

class SignersViewlet(ViewletBase):
    
    def __init__(self, *args):
        super(SignersViewlet, self).__init__(*args)
        self.settings = IAnnotations(self.context).get(ANNOTATION_KEY, {}).get('signers', {})
    
    @property
    def enabled(self):
        return self.settings.get('show_signers', False)
