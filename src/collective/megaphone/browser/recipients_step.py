from collective.megaphone import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import ANNOTATION_KEY, RECIPIENT_MAILER_ID, \
    LETTER_MAILTEMPLATE_BODY
from collective.megaphone.interfaces import IRecipient
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.z3cform.crud import crud
from z3c.form import field
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.i18nl10n import utranslate

class IRecipientSettings(Interface):
    
    send_email = schema.Bool(
        title = _(u'Send the letter by e-mail to each recipient.'),
        description = _(u'The letters will be sent to the e-mail addresses you enter below.'),
        default = True,
        )

class RecipientsAddForm(crud.AddForm):
    """ Just a normal CRUD add form with a custom template that doesn't nest FORMs.
    """
    label = _(u'Add a new recipient')
    template = ViewPageTemplateFile('crud_add_form.pt')
    
    @property
    def no_items_yet(self):
        return not len(self.context.get_items())

class RecipientsEditSubForm(crud.EditSubForm):
    template = ViewPageTemplateFile('crud_edit_subform.pt')
    
    @property
    def label(self):
        return self.widgets['first'].value + ' ' + self.widgets['last'].value
    
    @property
    def just_added(self):
        """
        True if this recipient was just added on this request.
        """
        return getattr(self.request, '_added_recipient', None) == self.content_id

class RecipientsEditForm(crud.EditForm):
    """ Just a normal CRUD edit form with a custom template that doesn't nest FORMs.
    """
    template = ViewPageTemplateFile('crud_edit_form.pt')
    editsubform_factory = RecipientsEditSubForm


    # 
    # optional = schema.Bool(
    #     title = _(u"Optional?"),
    #     description = _(u"If this is checked, letter writers may opt to have their letter sent " +
    #                     u"to this person. Otherwise, this person will get a copy of all letters sent."),
    #     required = True,
    #     default = False,
    #     )

# these are the content ids for two form fields that come out of the recipients step
REQUIRED_LABEL_ID = "required-recipients"
OPTIONAL_SELECTION_ID = "optional-recipients"

class RecipientsStep(wizard.Step, crud.CrudForm):
    
    template = ViewPageTemplateFile('crud_form.pt')
    prefix = 'recipients'
    label = _(u'Recipients')
    description = _(u'Configure the list of people who will (or might) receive your letter. Letter ' +
                    u'writers may choose from a list of the optional recipients (if any) and ' +
                    u"they'll also see a list of the non-optional recipients (if any).")
    fields = field.Fields(IRecipientSettings)
    update_schema = IRecipient
    addform_factory = RecipientsAddForm
    editform_factory = RecipientsEditForm
    
    def _get_recipients(self):
        return self.getContent().setdefault('recipients', {})
    
    def get_items(self):
        return sorted(self._get_recipients().items(), key=lambda x: x[1]['last'])
    
    def add(self, data):
        id = getUtility(IIDNormalizer).normalize("%s %s" % (data['first'], data['last']))
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
        recipients = data['recipients']
        optional_recipients = []
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
        
        # now create the form fields that show required (label) and optional (selection list) recipients
        for recipient_id, recipient in recipients.items():
            selection_data = {"id": recipient_id,
                              "name": (recipient['honorific'] and (recipient['honorific'] + ' ') or '') + recipient['first'] + ' ' + recipient['last'],
                              "description": recipient['description'],
                              }
            if recipient['optional']:
                optional_recipients.append(selection_data)
        if optional_recipients:
            if OPTIONAL_SELECTION_ID not in existing_ids:
                pfg.invokeFactory(id=OPTIONAL_SELECTION_ID, type_name="FormMultiSelectionField")
                pfg.moveObjectsToTop([OPTIONAL_SELECTION_ID])
            select = getattr(pfg, OPTIONAL_SELECTION_ID)
            select.setFgFormat("checkbox")
            select.setTitle(utranslate(DOMAIN, _(u"Choose who you'd like to send your letter to"), context=self.request))
            select.setDescription(utranslate(DOMAIN, _(u"(Each person will receive a separate copy of your letter.)"), context=self.request))
            vocab = ''
            for o in optional_recipients:
                vocab += "%s|%s" % (o['id'], o['name'])
                if o['description']:
                    vocab += ' (' + o['description'] + ')'
                vocab += '\n'
            select.setFgVocabulary(vocab)
        elif OPTIONAL_SELECTION_ID in existing_ids:
            # this is for RT purposes: delete the select now that there aren't any more req. recips
            pfg.manage_delObjects([OPTIONAL_SELECTION_ID,])

    def load(self, pfg):
        data = self.getContent()
        data['recipients'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('recipients', {})

        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        data['send_email'] = False
        if mailer is not None:
            data['send_email'] = (mailer.getRawExecCondition() != 'python:False')
