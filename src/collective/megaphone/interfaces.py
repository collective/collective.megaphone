from zope.interface import Interface, Attribute
from zope import schema
from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.constraints import is_email

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

class IRecipientSource(Interface):
    """Interface for a (context, request) multi-adapter that looks up letter recipients.
    
    ``context`` is a Megaphone Action providing IMegaphoneAction.
    ``request`` is a Zope 2 request.
    """
    
    settings_schema = Attribute('Schema for the settings shown when adding a '
                                'recipient of this type.')
    
    def lookup():
        """Looks up recipient data based on stored settings and form input.
        
        The stored settings are found in the recipients annotation of the context.
        The form input is found in the request.
        """
    
    def render_form():
        """Return HTML to be included in the main Megaphone form."""
