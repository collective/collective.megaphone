from zope.interface import implements, Interface
from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.interfaces import IRecipientSource, IRecipientSourceRegistration

class TestRecipientSource(object):
    implements(IRecipientSource)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def lookup(self):
        return []
    
    def render_form(self):
        return ''


class TestRecipientSourceRegistration(object):
    implements(IRecipientSourceRegistration)
    
    name = 'test'
    title = _(u'Dummy recipient lookup')
    description = _(u"Doesn't do a darned thing.")
    settings_schema = Interface

    def get_label(self, settings):
        return u'Dummy Recipient lookup'
