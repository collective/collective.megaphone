from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.browser.utils import PopupForm
from collective.megaphone.config import STATES
from collective.z3cform.wizard import wizard
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.z3cform.crud import crud
from z3c.form import button, form, field
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.app.component.hooks import getSite
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getUtility
from zope.event import notify
from zope.interface import Interface, directlyProvides
from zope.lifecycleevent import ObjectCreatedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.i18nl10n import utranslate
from Products.CMFPlone.utils import safe_unicode
from Products.PloneFormGen.interfaces import IPloneFormGenField

HAS_CAPTCHA = False
try:
    import collective.captcha
except ImportError:
    try:
        import collective.recaptcha
        collective # pyflakes
    except ImportError:
        pass
    else:
        HAS_CAPTCHA = True
else:
    HAS_CAPTCHA = True

field_type_to_portal_type_map = {
    'string': 'FormStringField',
    'text': 'FormTextField',
    'boolean': 'FormBooleanField',
    'selection': 'FormSelectionField',
    'multiselection': 'FormMultiSelectionField',
    'captcha': 'FormCaptchaField',
    'label': 'FormLabelField',
}

class IFormField(Interface):
    field_type = schema.Choice(
        title = _(u'Field type'),
        description = _(u'Select the type of field you would like to add to the form.'),
        vocabulary = SimpleVocabulary.fromItems((
            (_(u'String'), 'string'),
            (_(u'Text'), 'text'),
            (_(u'Yes/No'), 'boolean'),
            (_(u'Dropdown'), 'selection'),
            )),
        required = True,
        default = 'string',
        )
    
    title = schema.TextLine(
        title = _(u'Name of field'),
        )
    
    description = schema.Text(
        title = _(u'Description'),
        description = _(u'Additional instructions to help the user.'),
        required = False,
        missing_value = u'',
        )
    
    required = schema.Bool(
        title = _(u'Is this field required?'),
        required = True,
        default = True,
        )

class IOrdered(Interface):
    order = schema.Int(
        required = False,
        )

class IOrderedFormField(IFormField, IOrdered):
    pass

class IStringFormField(IOrderedFormField):
    default = schema.TextLine(
        title = _(u'Default text'),
        description = _(u'Enter the default text for this form field.'),
        required = False,
        )
    
    validator = schema.Choice(
        title = _(u'Validator'),
        description = _(u"Select a pattern to check this form field's input against."),
        vocabulary = 'collective.megaphone.vocabulary.string_validators',
        required = True,
        )
    
    size = schema.Int(
        title = _(u'Size'),
        description = _(u'Enter how many characters wide this field should be.'),
        required = False,
        default = 30,
        )

class ITextFormField(IOrderedFormField):
    default = schema.Text(
        title = _(u'Default text'),
        description = _(u'Enter the default text for this form field.'),
        required = False,
        )

class IBooleanFormField(IOrderedFormField):
    default = schema.Bool(
        title = _(u'Default value'),
        description = _(u'Select the default value for this form field.'),
        required = False,
        )

class ISelectionFormField(IOrderedFormField):
    vocab = schema.Text(
        title = _(u'Options'),
        description = _(u"Use one line per option. (Note, you may optionally use a 'value|label' format.)"),
        required = True,
        )

field_type_to_schema_map = {
    'string': IStringFormField,
    'text': ITextFormField,
    'boolean': IBooleanFormField,
    'selection': ISelectionFormField,
    'multiselection': ISelectionFormField,
}

def StringValidatorVocabularyFactory(context):
    site = getSite()
    fgt = getToolByName(site, 'formgen_tool')
    items = [(label, value) for (value, label) in fgt.getStringValidatorsDL().items()]
    return SimpleVocabulary.fromItems(items)
directlyProvides(StringValidatorVocabularyFactory, IVocabularyFactory)


class FieldChoiceForm(PopupForm):
    label = _(u'Add a new field')
    
    ignoreContext = True

    _redirect_url = None
    
    fields = field.Fields(IFormField).select('field_type')
    fields['field_type'].widgetFactory = RadioFieldWidget

    def render(self):
        if self._redirect_url is not None:
            self.request.response.redirect(self._redirect_url)
            return ''
        return super(FieldChoiceForm, self).render()
    
    @button.buttonAndHandler(_(u'Continue'))
    def handleContinue(self, action):
        data, errors = self.extractData()
        field_type = IFormField['field_type'].vocabulary.by_value[data['field_type']].token
        self._redirect_url = '%s/@@add-field?form.widgets.field_type:list=%s' % (self.context.absolute_url(), field_type)
    
    
class FieldAddForm(PopupForm):
    label = _(u'Add a new field')
    ignoreContext = True
    
    @property
    def label(self):
        return _(u"Add Field: ${field_type}",
                 mapping={u'field_type': self.field_type.token})

    @property
    def field_type(self):
        field_type = self.request.form.get('form.widgets.field_type')
        if field_type is None:
            raise ValueError('No field_type found in request.')
        field_type = IFormField['field_type'].vocabulary.by_token.get(field_type[0])
        return field_type

    @property
    def fields(self):
        field_type = self.field_type.value
        field_schema = field_type_to_schema_map.get(field_type, IOrderedFormField)
        fields = field.Fields(field_schema).omit('order')
        fields['field_type'].mode = HIDDEN_MODE
        return fields

    @button.buttonAndHandler(_(u'Add Field'))
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
            self.status = _(u'Field added successfully.')


class FieldEditForm(PopupForm, form.EditForm):
    
    @property
    def label(self):
        return _(u"Edit Field: ${field}",
                 mapping={u'field': self.getContent()['title']})
    
    @lazy_property
    def wizard(self):
        wizard = self.context.form_instance
        wizard.update()
        return wizard
    
    def getContent(self):
        fields = self.wizard.currentStep._get_fields()
        field_id = self.request.form.get('form.widgets.field_id')
        if field_id is None:
            raise ValueError('No field_id found in request.')
        return fields[field_id]

    @property
    def fields(self):
        field_type = self.getContent().get('field_type', 'string')
        field_schema = field_type_to_schema_map.get(field_type, IOrderedFormField)
        fields = field.Fields(field_schema)
        fields['order'].mode = HIDDEN_MODE
        fields['field_type'].mode = HIDDEN_MODE
        # add hidden field to maintain the recipient id
        fields += field.Fields(schema.TextLine(__name__ = 'field_id'))
        fields['field_id'].mode = HIDDEN_MODE
        return fields
    
    def updateWidgets(self):
        super(FieldEditForm, self).updateWidgets()
        if self.getContent().get('field_type', 'string') == 'text':
            self.widgets['default'].rows = 8
    
    buttons = button.Buttons()
    handlers = button.Handlers()
    
    @button.buttonAndHandler(_(u'Save'))
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return
        
        del data['field_id']
        content = self.getContent()
        changes = wizard.applyChanges(self, content, data)
        if changes:
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage
        self.wizard.sync()
        self._finished = True


class FieldEditSubForm(crud.EditSubForm):

    template = ViewPageTemplateFile('crud_orderable_edit_subform.pt')

    @property
    def label(self):
        return self.content['title']

    @property
    def fields(self):
        fields = field.Fields(self._select_field()) + field.Fields(IOrdered)
        fields['order'].mode = HIDDEN_MODE
        return fields

    @property
    def field_fti(self):
        ttool = getToolByName(self.context.context.context, 'portal_types')
        field_type = self.content.get('field_type', 'string')
        if field_type is not None:
            fti_id = field_type_to_portal_type_map.get(field_type, None)
            if fti_id is not None:
                return getattr(ttool, fti_id, None)

    def applyChanges(self, data):
        content = self.getContent()
        return wizard.applyChanges(self, content, data)


class FieldListingForm(crud.EditForm):
    """ Just a normal CRUD edit form with a custom template that doesn't nest FORMs.
    """
    editsubform_factory = FieldEditSubForm
    template = ViewPageTemplateFile('crud_orderable_edit_form.pt')

    def update(self):
        res = super(FieldListingForm, self).update()
        self._update_subforms() # in case order changed
        return res

FieldListingForm.buttons['edit'].title = _(u'Save order')


class FormFieldsStep(wizard.Step, crud.CrudForm):
    template = ViewPageTemplateFile('crud_orderable_form.pt')
    prefix = 'formfields'
    label = _(u'Form Fields')
    description = _(u'Configure the fields that will be collected. Default options are ' +
                    u'provided below, but you may remove or alter them, or add new ones.')

    fields = {}
    update_schema = IOrdered
    addform_factory = crud.NullForm
    editform_factory = FieldListingForm

    def _get_fields(self):
        data = self.getContent()
        if 'fields' in data:
            return data['fields']
        
        # initialize fields
        fields = {
            'body': {
                'field_type': 'text',
                'title': utranslate(DOMAIN, _(u'Letter Body'), context=self.request),
                'description': utranslate(DOMAIN, _(u'A salutation and signature will be added automatically.'), context=self.request),
                'default': utranslate(DOMAIN, _(u'Enter the body of your letter here.  A salutation and signature will be added automatically.'), context=self.request),
                'required': True,
                'order': 0,
                },
            'sincerely': {
                'field_type': 'label',
                'title': utranslate(DOMAIN, _(u'Sincerely,'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': False,
                'order': 1,
                },
            'first': {
                'title': utranslate(DOMAIN, _(u'First Name'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': True,
                'order': 2,
                },
            'last': {
                'title': utranslate(DOMAIN, _(u'Last Name'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': True,
                'order': 3,
                },
            'email': {
                'title': utranslate(DOMAIN, _(u'E-mail Address'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': True,
                'validator': 'isEmail',
                'order': 4,
                },
            'street': {
                'title': utranslate(DOMAIN, _(u'Street Address'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': False,
                'order': 5,
                },
            'city': {
                'title': utranslate(DOMAIN, _(u'City'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': False,
                'order': 6,
                },
            'state': {
                'field_type': 'selection',
                'title': utranslate(DOMAIN, _(u'State'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': False,
                'vocab': STATES,
                'order': 7,
                },
            'zip': {
                'title': utranslate(DOMAIN, _(u'Postal Code'), context=self.request),
                'description': utranslate(DOMAIN, _(u''), context=self.request),
                'required': False,
                'validator': 'isZipCode',
                'order': 8,
                'size': 10,
                },
            }
        if HAS_CAPTCHA:
            fields['captcha'] = {
                'field_type': 'captcha',
                'title': utranslate(DOMAIN, _(u'Please enter this text.'), context=self.request),
                'description': utranslate(DOMAIN, _(u'This helps prevent spammers from using this form.'), context=self.request),
                'required': True,
                'order': 9,
                }
        if 'intro' in self.wizard.session.keys() and self.wizard.session['intro']['megaphone_type'] == 'petition':
            del fields['sincerely']
            fields['body']['title'] = utranslate(DOMAIN, _(u'Additional Comment'), context=self.request)
            fields['body']['description'] = u''
            fields['body']['default'] = u''
        return self.getContent().setdefault('fields', fields)

    def get_items(self):
        return sorted(self._get_fields().items(), key=lambda x: x[1]['order'])

    def add(self, data):
        data['order'] = len(self._get_fields())
        id = getUtility(IIDNormalizer).normalize(data['title'])

        if id in self._get_fields().keys() or id in self.context.objectIds():
            raise schema.ValidationError, _(u'You selected a field name that is already in use. Please use a different name.')

        self._get_fields()[id] = data
        self.wizard.sync()
        self.request._added_field = id
        return data

    def remove(self, (id, item)):
        del self._get_fields()[id]
        self.wizard.sync()

    def apply(self, pfg, initial_finish=True):
        """
        Apply changes to the underlying PloneFormGen form based on the submitted values.
        """
        data = self.getContent()

        existing_fields = [f.getId() for f in pfg.objectValues() if IPloneFormGenField.providedBy(f) and not f.getServerSide()]
        fields = data['fields']
        for field_id, field_attrs in sorted(fields.items(), key=lambda x: x[1]['order']):
            if 'field_type' in field_attrs:
                field_type = field_attrs['field_type']
            else:
                field_type = 'string'

            f_portal_type = field_type_to_portal_type_map.get(field_type, 'FormStringField')
            if field_id not in existing_fields:
                pfg.invokeFactory(id=field_id, type_name=f_portal_type)
            field = getattr(pfg, field_id)
            field.setTitle(field_attrs['title'])
            field.setDescription(field_attrs['description'])
            field.setRequired(field_attrs.get('required', False))
            if 'default' in field_attrs:
                field.setFgDefault(field_attrs['default'])
            if 'validator' in field_attrs:
                field.setFgStringValidator(field_attrs['validator'])
            if 'vocab' in field_attrs:
                field.setFgVocabulary(field_attrs['vocab'])
            if 'size' in field_attrs:
                field.setFgsize(field_attrs['size'])
            if field_type == 'text':
                field.setValidateNoLinkSpam(True)

        # sync removed fields
        to_delete = []
        for f in existing_fields:
            if f not in fields:
                to_delete.append(f)
        pfg.manage_delObjects(to_delete)

        # adjust order
        if not initial_finish:
            sorted_field_ids = [k for k, v in sorted(fields.items(), key=lambda x: x[1]['order'])]
            pfg.moveObjectsByDelta(sorted_field_ids, -len(sorted_field_ids))
        
        # reindex fields
        for f in pfg.objectValues():
            f.reindexObject()

    def load(self, pfg):
        data = self.getContent()

        fields = data.setdefault('fields', {})
        i = 0
        for f in pfg.objectValues():
            if IPloneFormGenField.providedBy(f):
                if f.getServerSide():
                    continue
                fieldinfo = {
                    'field_type': None,
                    'title': safe_unicode(f.Title()),
                    'description': safe_unicode(f.Description()),
                    'required': f.getRequired(),
                    'order': i,
                }
                if hasattr(f, 'getFgDefault'):
                    fieldinfo['default'] = safe_unicode(f.getFgDefault())
                if f.portal_type == 'FormStringField':
                    fieldinfo['field_type'] = 'string'
                    fieldinfo['validator'] = f.getFgStringValidator()
                    if not fieldinfo['validator']:
                        fieldinfo['validator'] = 'vocabulary_none_text'
                    try:
                        fieldinfo['size'] = int(f.getFgsize())
                    except TypeError:
                        fieldinfo['size'] = 30
                if f.portal_type == 'FormTextField':
                    fieldinfo['field_type'] = 'text'
                if f.portal_type == 'FormBooleanField':
                    fieldinfo['field_type'] = 'boolean'
                    # make sure we match one of the vocab terms
                    if fieldinfo['default'] is not True:
                        fieldinfo['default'] = False
                if f.portal_type == 'FormSelectionField':
                    fieldinfo['field_type'] = 'selection'
                    fieldinfo['vocab'] = safe_unicode("\n".join(f.getFgVocabulary()))
                if f.portal_type == 'FormMultiSelectionField':
                    fieldinfo['field_type'] = 'multiselection'
                    fieldinfo['vocab'] = safe_unicode("\n".join(f.getFgVocabulary()))
                if f.portal_type == 'FormCaptchaField':
                    fieldinfo['field_type'] = 'captcha'
                fields[f.getId()] = fieldinfo
                i += 1
