import re
from collective.megaphone.config import ANNOTATION_KEY, RECIPIENT_MAILER_ID, \
    LETTER_MAILTEMPLATE_BODY
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.z3cform.crud import crud
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import Interface
from Products.PloneFormGen.config import DEFAULT_MAILTEMPLATE_BODY

class RecipientsAddForm(crud.AddForm):
    """ Just a normal CRUD add form with a custom template that doesn't nest FORMs.
    """
    label = u'Add a new recipient'
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

class InvalidEmailAddress(schema.ValidationError):
    u"Invalid e-mail address"

check_email = re.compile(r"[a-zA-Z0-9._%-]+@([a-zA-Z0-9-]+\.)*[a-zA-Z]{2,4}").match
def validate_email(value):
    if not check_email(value):
        raise InvalidEmailAddress(value)
    return True

class IRecipient(Interface):
    honorific = schema.TextLine(
        title = u'Honorific',
        required = False,
        missing_value = u'',
        )

    first = schema.TextLine(
        title = u'First Name',
        )

    last = schema.TextLine(
        title = u'Last Name',
        )

    email = schema.TextLine(
        title = u'E-mail Address',
        description = u'If no e-mail is entered, a letter to this recipient will be generated but not sent.',
        required = False,
        constraint = validate_email
        )

    description = schema.TextLine(
        title = u"Description",
        description = u"Any context you'd like to provide? (For example: congressional district, job title)",
        required = False,
        missing_value = u'',
        )

    optional = schema.Bool(
        title = u"Optional?",
        description = u"If this is checked, letter writers may opt to have their letter sent " +\
                      u"to this person. Otherwise, this person will get a copy of all letters sent.",
        required = True,
        default = False,
        )

# these are the content ids for two form fields that come out of the recipients step
REQUIRED_LABEL_ID = "required-recipients"
OPTIONAL_SELECTION_ID = "optional-recipients"

class RecipientsStep(wizard.Step, crud.CrudForm):
    
    template = ViewPageTemplateFile('crud_form.pt')
    prefix = 'recipients'
    label = 'Letter Recipients'
    description = u'Configure the list of people who will (or might) receive your letter. Letter ' + \
                  u'writers may choose from a list of the optional recipients (if any) and ' + \
                  u"they'll also see a list of the non-optional recipients (if any)."
    fields = {}
    update_schema = IRecipient
    addform_factory = RecipientsAddForm
    editform_factory = RecipientsEditForm
    
    @property
    def completed(self):
        """
        Don't allow progressing to the next step unless there's at least one
        recipient.
        """
        if not len([r for r in self._get_recipients()]):
            return False
        return True

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
        required_recipients = []
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
        # XXX set description
        mailer = getattr(pfg, RECIPIENT_MAILER_ID)
        if mailer.getExecCondition != 'request/form/recip_email|nothing':
            mailer.setExecCondition('request/form/recip_email|nothing')
        if not mailer.getRawRecipientOverride():
            mailer.setRecipientOverride('request/form/recip_email|nothing')
        if mailer.getRawBody_pt() == DEFAULT_MAILTEMPLATE_BODY:
            mailer.setBody_pt(LETTER_MAILTEMPLATE_BODY)
        if not pfg.getRawAfterValidationOverride():
            pfg.setAfterValidationOverride('here/@@recipient_multiplexer')
        
        # now create the form fields that show required (label) and optional (selection list) recipients
        for recipient_id, recipient in recipients.items():
            selection_data = {"id": recipient_id,
                              "name": recipient['first'] + ' ' + recipient['last'],
                              "description": recipient['description'],
                              }
            if recipient['optional']:
                optional_recipients.append(selection_data)
            else:
                required_recipients.append(selection_data)
        if required_recipients:
            if REQUIRED_LABEL_ID not in existing_ids:
                pfg.invokeFactory(id=REQUIRED_LABEL_ID, type_name="FormLabelField")
            label = getattr(pfg, REQUIRED_LABEL_ID)
            label.setTitle("""Your letter will be sent to the following people: %s"""
                            % ','.join(["%s %s" % (r['name'], (r['description'] and '(' + r['description'] + ')') or '')
                                            for r in required_recipients]))
        elif REQUIRED_LABEL_ID in existing_ids:
            # this is for RT purposes: delete the label now that there aren't any more req. recips
            pfg.manage_delObjects([REQUIRED_LABEL_ID,])
        if optional_recipients:
            # XXX FIXME
            if OPTIONAL_SELECTION_ID not in existing_ids:
                pfg.invokeFactory(id=OPTIONAL_SELECTION_ID, type_name="FormMultiSelectionField")
            select = getattr(pfg, OPTIONAL_SELECTION_ID)
            select.setFgFormat("checkbox")
            select.setTitle("Choose who you'd like to send your letter to")
            select.setDescription("(Each person will receive a separate copy of your letter.)")
            vocab = ''
            for o in optional_recipients:
                v_option = "%s|%s" % (o['id'], o['name'])
                if o['description']:
                    v_option += " (%s)" % (o['description'] and ('(' + o['description'] + ')') or '')
                vocab += '\n'
            select.setFgVocabulary(vocab)
        elif OPTIONAL_SELECTION_ID in existing_ids:
            # this is for RT purposes: delete the select now that there aren't any more req. recips
            pfg.manage_delObjects([OPTIONAL_SELECTION_ID,])

    def load(self, pfg):
        data = self.getContent()
        data['recipients'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('recipients', {})
