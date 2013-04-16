from collective.megaphone.compat import IAdding
from collective.megaphone.compat import ViewPageTemplateFile
from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.browser.utils import PopupForm
from collective.megaphone.config import ANNOTATION_KEY, RECIPIENT_MAILER_ID, \
    LETTER_MAILTEMPLATE_BODY
from collective.megaphone.interfaces import IRecipientSourceRegistration
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from plone.z3cform.interfaces import IWrappedForm
from z3c.form import field, form, button, widget
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.browser.radio import RadioWidget
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getUtility, queryUtility, getAllUtilitiesRegisteredFor
from zope.event import notify
from zope.interface import Interface, implements
from zope.lifecycleevent import ObjectCreatedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.i18nl10n import utranslate
import uuid


class IRecipientSettings(Interface):
    
    send_email = schema.Bool(
        title = _(u'Send the letter by e-mail to each recipient.'),
        description = _(u'The letters will be sent by e-mail to the recipients you selected above.'),
        default = True,
        )


radio_template = ViewPageTemplateFile('descriptive_radio_input.pt')
def DescriptiveRadioWidget(field, request):
    w = widget.FieldWidget(field, RadioWidget(request))
    w.template = radio_template
    return w


class RecipientSourceChoiceForm(form.Form):
    implements(IWrappedForm)

    _redirect_url = None
    
    @property
    def fields(self):
        terms = []
        for reg in getAllUtilitiesRegisteredFor(IRecipientSourceRegistration):
            if not reg.enabled:
                continue
            terms.append(schema.vocabulary.SimpleTerm(
                value = reg,
                token = reg.name,
                title = reg.title,
                ))
        
        # if only one source, redirect to it
        if len(terms) <= 1:
            self._redirect_url = '%s/@@add-recipient?form.widgets.recipient_type=%s' % (self.context.absolute_url(), terms[0].value.name)
            return field.Fields()
        
        vocab = schema.vocabulary.SimpleVocabulary(terms)
        fields = field.Fields(schema.Choice(
            __name__ = 'recipient_type',
            title = _(u'Recipient type'),
            description = _(u'Select the type of recipient you want to add.'),
            vocabulary = vocab,
            default = vocab.by_token['standard'].value,
            ))
        fields['recipient_type'].widgetFactory = DescriptiveRadioWidget
        return fields
    
    def render(self):
        if self._redirect_url is not None:
            self.request.response.redirect(self._redirect_url)
            return ''
        return super(RecipientSourceChoiceForm, self).render()
    
    @button.buttonAndHandler(_(u'Continue'))
    def handleContinue(self, action):
        data, errors = self.extractData()
        self._redirect_url = '%s/@@add-recipient?form.widgets.recipient_type=%s' % (self.context.absolute_url(), data['recipient_type'].name)


class RecipientSourceAddForm(PopupForm):
    ignoreContext = True

    @property
    def fields(self):
        recipient_type = self.request.form.get('form.widgets.recipient_type')
        if recipient_type is None:
            raise ValueError('No recipient_type found in request.')
        reg = queryUtility(IRecipientSourceRegistration, name=recipient_type, default=None)
        if reg is None:
            raise ValueError('Invalid recipient_type: %s' % recipient_type)
        
        fields = field.Fields(reg.settings_schema)
        # add hidden field to maintain the recipient type
        fields += field.Fields(schema.TextLine(__name__ = 'recipient_type'))
        fields['recipient_type'].mode = HIDDEN_MODE
        return fields

    @button.buttonAndHandler(_(u'Add Recipient'))
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.AddForm.formErrorsMessage
            return
        
        wizard = self.context.form_instance
        wizard.update()
        try:
            item = wizard.currentStep.add(data)
            self._finished = True
        except schema.ValidationError, e:
            self.status = e
        else:
            notify(ObjectCreatedEvent(item))
            self.status = _(u'Recipient added successfully.')


class RecipientSourceEditForm(PopupForm, form.EditForm):
    
    @lazy_property
    def wizard(self):
        wizard = self.context.form_instance
        wizard.update()
        return wizard
    
    def getContent(self):
        recipients = self.wizard.currentStep._get_recipients()
        recipient_id = self.request.form.get('form.widgets.recipient_id')
        if recipient_id is None:
            raise ValueError('No recipient_id found in request.')

        return recipients[recipient_id]

    @property
    def fields(self):
        recipient_type = self.getContent().get('recipient_type', u'standard')
        reg = queryUtility(IRecipientSourceRegistration, name=recipient_type, default=None)
        if reg is None:
            raise ValueError('Invalid recipient_type: %s' % recipient_type)
        
        fields = field.Fields(reg.settings_schema)
        # add hidden field to maintain the recipient id
        fields += field.Fields(schema.TextLine(__name__ = 'recipient_id'))
        fields['recipient_id'].mode = HIDDEN_MODE
        return fields
    
    buttons = button.Buttons()
    handlers = button.Handlers()
    
    @button.buttonAndHandler(_(u'Save'))
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return
        
        del data['recipient_id']
        changes = self.applyChanges(data)
        if changes:
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage
        self.wizard.sync()
        self._finished = True

    @button.buttonAndHandler(_(u'Delete'))
    def handleDelete(self, action):
        id = self.widgets['recipient_id'].value
        self.wizard.currentStep.remove((id, None))
        self._finished = True


class RecipientsStep(wizard.Step):
    
    template = ViewPageTemplateFile('recipients_step.pt')
    prefix = 'recipients'
    label = _(u'Recipients')
    description = _(u'Configure the list of people who will (or might) receive your letter. Letter ' +
                    u'writers may choose from a list of the optional recipients (if any) and ' +
                    u"they'll also see a list of the non-optional recipients (if any).")
    fields = field.Fields(IRecipientSettings)
    
    def _get_recipients(self):
        return self.getContent().setdefault('recipients', {})
    
    def get_items(self):
        items = []
        for id, item in self._get_recipients().items():
            recipient_type = item.get('recipient_type', u'standard')
            reg = getUtility(IRecipientSourceRegistration, name=recipient_type)
            items.append({
                'id': id,
                'label': reg.get_label(item),
                })
        return sorted(items, key=lambda x: x['label'])
    
    def add(self, data):
        id = str(uuid.uuid4())
        self._get_recipients()[id] = data
        self.wizard.sync()
        self.request._added_recipient = id
        return data
    
    def remove(self, (id, item)):
        del self._get_recipients()[id]
        self.wizard.sync()

    def apply(self, pfg, initial_finish=True):
        """
        Apply changes to the underlying PloneFormGen form based on the submitted values.
        """
        data = self.getContent()
        existing_ids = pfg.objectIds()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())

        # store the recipient info in an annotation on the form
        annotation['recipients'] = data['recipients']
        
        # create the multiplexing mailer
        if RECIPIENT_MAILER_ID not in existing_ids:
            pfg.invokeFactory(id=RECIPIENT_MAILER_ID, type_name='LetterRecipientMailerAdapter')
            adapters = list(pfg.actionAdapter)
            adapters.remove(RECIPIENT_MAILER_ID)
            pfg.setActionAdapter(adapters)
            mailer = getattr(pfg, RECIPIENT_MAILER_ID)
            mailer.setTitle(utranslate(DOMAIN, _(u'Emails to decision maker(s)'), context=self.request))
        else:
            mailer = getattr(pfg, RECIPIENT_MAILER_ID)
        if mailer.getExecCondition != 'request/form/recip_email|nothing':
            mailer.setExecCondition('request/form/recip_email|nothing')
        if not mailer.getRawRecipientOverride():
            mailer.setRecipientOverride('request/form/recip_email|nothing')
        formgen_tool = getToolByName(pfg, 'formgen_tool')
        if mailer.getRawBody_pt() == formgen_tool.getDefaultMailTemplateBody():
            mailer.setBody_pt(LETTER_MAILTEMPLATE_BODY)
        execCondition = mailer.getRawExecCondition()
        if not execCondition or execCondition in ('request/form/recip_email|nothing', 'python:False'):
            mailer.setExecCondition(data['send_email'] and 'request/form/recip_email|nothing' or 'python:False')

    def load(self, pfg):
        data = self.getContent()
        if IAdding.providedBy(pfg):
            return data
        data['recipients'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('recipients', {})

        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        data['send_email'] = False
        if mailer is not None:
            data['send_email'] = (mailer.getRawExecCondition() != 'python:False')
