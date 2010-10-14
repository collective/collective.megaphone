from z3c.form import form, field
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.interface import implements
from zope import schema
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from collective.megaphone.utils import MegaphoneMessageFactory as _
from collective.megaphone.interfaces import IRecipientSource, IRecipientData, IRecipientSourceRegistration
from collective.megaphone.recipients import recipient_label, get_recipient_settings

class IStandardRecipient(IRecipientData):
    
    optional = schema.Bool(
        title = _(u"Optional?"),
        description = _(u"If this is checked, letter writers may opt to have their letter sent " +
                        u"to this person. Otherwise, this person will get a copy of all letters sent."),
        required = True,
        default = False,
        )


class StandardRecipientSource(object):
    implements(IRecipientSource)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.settings = get_recipient_settings(context, 'standard')
        self.form = StandardRecipientSourceForm(context, request, self.settings)
        self.form.update()

    def lookup(self):
        for id, r in self.settings:
            if not r['optional'] or id in self.form.widgets['optional-recipients'].value:
                yield r
    
    def render_form(self):
        return self.form.render()


class StandardRecipientSourceForm(form.Form):
    template = ViewPageTemplateFile('standard.pt')
    ignoreContext = True

    def __init__(self, context, request, settings):
        super(StandardRecipientSourceForm, self).__init__(context, request)

        self.required = []
        self.optional = []
        for id, r in settings:
            s = recipient_label(r)
            if r['optional']:
                self.optional.append((id, s))
            else:
                self.required.append(s)

    @property
    def fields(self):
        if not self.optional:
            return field.Fields()
        
        if self.required:
            title = _(u"You may also choose from the following recipients:")
        else:
            title = _(u"You may choose from the following recipients:")
        fields = field.Fields(
            schema.Set(
                __name__ = 'optional-recipients',
                title = title,
                description = _(u"(Each person will receive a separate copy of your letter.)"),
                value_type = schema.Choice(
                    vocabulary = schema.vocabulary.SimpleVocabulary(
                        [schema.vocabulary.SimpleTerm(value, title=title) for value, title in self.optional]
                        ),
                    ),
                required = False,
                )
            )
        fields['optional-recipients'].widgetFactory = CheckBoxFieldWidget
        return fields

    def update(self):
        # preserve original request form; PFG doesn't like it to be decoded
        orig_form = self.request.form.copy()
        super(StandardRecipientSourceForm, self).update()
        self.request.form = orig_form


class StandardRecipientSourceRegistration(object):
    implements(IRecipientSourceRegistration)
    
    name = 'standard'
    title = _(u'Standard recipient')
    description = _(u'Add a required or optional recipient.')
    settings_schema = IStandardRecipient
    enabled = True

    def get_label(self, settings):
        label = u''
        label = recipient_label(settings)
        if settings['optional']:
            label += u' (optional)'
        return label

