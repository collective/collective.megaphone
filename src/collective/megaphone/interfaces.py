from zope.interface import Interface
from zope import schema
from collective.megaphone.utils import MegaphoneMessageFactory as _
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


class IRecipientSourceRegistration(Interface):
    """Interface for a utility that provides information about a recipient source."""
    
    name = schema.ASCIILine(
        title = _(u'Name'),
        description = _(u"The name of the source's adapter registration"),
        )

    title = schema.TextLine(title = _(u'Title'), )
    description = schema.TextLine(title = _(u'Description'))

    enabled = schema.Bool(
        title = _(u'Enabled'),
        )

    settings_schema = schema.Object(
        title = _(u'Settings schema'),
        description = _(u'Schema for the settings shown when adding a recipient of this type.'),
        schema = Interface,
        )

    def get_label(settings):
        """Return a label for this recipient source with the given settings.
        
        Used for display in the recipient wizard step.
        """

class IRecipientSource(Interface):
    """Interface for a (context, request) multi-adapter that looks up letter recipients.
    
    ``context`` is a Megaphone Action providing IMegaphoneAction.
    ``request`` is a Zope 2 request.
    """
    
    def lookup():
        """Looks up recipient data based on stored settings and form input.
        
        The stored settings are found in the recipients annotation of the context.
        The form input is found in the request.
        """
    
    def render_form():
        """Return HTML to be included in the main Megaphone form."""
