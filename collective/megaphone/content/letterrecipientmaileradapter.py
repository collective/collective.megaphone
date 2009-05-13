"""Sub-class of PloneFormGen's FormMailerAdapter
"""
from zope.interface import implements
from zope.app.component.hooks import getSite
from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes import atapi

from Products.PloneFormGen.content.formMailerAdapter import formMailerAdapterSchema
from Products.PloneFormGen.content.formMailerAdapter import FormMailerAdapter

from collective.megaphone.config import PROJECTNAME
from collective.megaphone.browser.recipient_multiplexer import IMultiplexedActionAdapter

schema = formMailerAdapterSchema.copy()

# we're removing the single recip name field to be replaced by a property that gets the name
# built from the individual fields listed above
del schema['recipient_name']

# hide some fields
for h in ("to_field",       # allows you to extract the recip's value from the form
          "cc_recipients",
          "bcc_recipients",
          "subject_field",  # ditto the subject line
          "showAll", "showFields", "includeEmpties", # fields for auto-generated email bodies
          "senderOverride", "recipientOverride","bccOverride","subjectOverride"
          ):
    schema[h].widget.visible = {'view':'invisible', 'edit':'invisible'}

class LetterRecipientMailerAdapter(FormMailerAdapter):
    """Subclass of FormMailerAdapter that contains extra fields for letter recipient data"""
    implements(IMultiplexedActionAdapter)
    
    meta_type = portal_type = "LetterRecipientMailerAdapter"
    archetype_name = "Letter Recipient Mailer"
    schema = schema
    security = ClassSecurityInfo()

    security.declareProtected(View, 'getRecipient_name')
    def getRecipient_name(self):
        """Return concatenation of honorific, first, last names"""
        request = getSite().REQUEST
        honorific = request.form.get('recip_honorific', '')
        first = request.form.get('recip_first', '')
        last = request.form.get('recip_last', '')
        fields = (honorific, first, last)
        return " ".join([w for w in fields if w])

    recipient_name = property(getRecipient_name)

atapi.registerType(LetterRecipientMailerAdapter, PROJECTNAME)
