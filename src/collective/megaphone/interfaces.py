from zope.interface import Interface, Attribute
from zope import schema
from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.utils import is_email

class IMegaphone(Interface):
    """A PloneFormGen form masquerading as a Megaphone action letter or petition.
    """
# deprecated
IActionLetter = IMegaphone

class IRecipientData(Interface):
    
    honorific = schema.TextLine(
        title = _(u'Honorific'),
        required = False,
        missing_value = u'',
        )

    first = schema.TextLine(
        title = _(u'First Name'),
        )

    last = schema.TextLine(
        title = _(u'Last Name'),
        )

    email = schema.TextLine(
        title = _(u'E-mail Address'),
        description = _(u'If no e-mail is entered, a letter to this recipient will be generated but not sent.'),
        required = False,
        constraint = is_email
        )

    description = schema.TextLine(
        title = _(u"Description"),
        description = _(u"Any context you'd like to provide? (For example: congressional district, job title)"),
        required = False,
        missing_value = u'',
        )

class IRecipientType(Interface):
    """Interface for a component that 
    """
    
    settings_schema = Attribute('Schema for the settings shown when adding a recipient of this type.')
    
    def lookup(settings, form_data):
        """Returns a list of dictionaries of recipient data, given the dictionary of form input from a Megaphone form."""
    
    def render_form(settings):
        """Return HTML to be included in the main Megaphone form."""
