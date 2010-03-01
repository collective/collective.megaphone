from collective.megaphone import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import STATES
from collective.z3cform.wizard import wizard
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.z3cform.crud import crud
from z3c.form import field
from z3c.form.interfaces import HIDDEN_MODE
from zope import schema
from zope.app.component.hooks import getSite
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import Interface, directlyProvides
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
        description = _(u'Select the type of field you would like to add to the letter.'),
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
        description = _(u'Additional instructions to help the user creating the letter.'),
        required = False,
        missing_value = u'',
        )
    
    required = schema.Bool(
        title = _(u'Is this field required?'),
        required = True,
        default = True,
        )

class IOrderedFormField(IFormField):
    order = schema.Int(
        required = False,
        )

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
        description = _(u'Use one line per option. (Note, you may optionally use a "value|label" format.)'),
        required = True,
        )

def StringValidatorVocabularyFactory(context):
    site = getSite()
    fgt = getToolByName(site, 'formgen_tool')
    items = [(label, value) for (value, label) in fgt.getStringValidatorsDL().items()]
    return SimpleVocabulary.fromItems(items)
directlyProvides(StringValidatorVocabularyFactory, IVocabularyFactory)

class FieldAddForm(crud.AddForm):
    """ Just a normal CRUD add form with a custom template that doesn't nest FORMs.
    """
    label = _(u'Add a new field')
    template = ViewPageTemplateFile('crud_add_form.pt')

    @property
    def no_items_yet(self):
        return not len(self.context.get_items())

class FieldEditSubForm(crud.EditSubForm):

    template = ViewPageTemplateFile('crud_orderable_edit_subform.pt')

    @property
    def label(self):
        return self.widgets['title'].value

    @property
    def just_added(self):
        """
        True if this recipient was just added on this request.
        """
        return getattr(self.request, '_added_field', None) == self.content_id

    @property
    def fields(self):
        if 'field_type' not in self.content:
            self.content['field_type'] = 'string'
        field_type_map = {
            'string': IStringFormField,
            'text': ITextFormField,
            'boolean': IBooleanFormField,
            'selection': ISelectionFormField,
            'multiselection': ISelectionFormField,
        }
        field_schema = field_type_map.get(self.content['field_type'], IOrderedFormField)

        fields = field.Fields(self._select_field()) + field.Fields(field_schema).omit('field_type')
        fields['order'].mode = HIDDEN_MODE
        return fields

    def updateWidgets(self):
        super(FieldEditSubForm, self).updateWidgets()
        if self.content['field_type'] == 'text':
            self.widgets['default'].rows = 8
    
    @property
    def field_fti(self):
        ttool = getToolByName(self.context.context.context, 'portal_types')
        field_type = self.content.get('field_type', None)
        if field_type is not None:
            fti_id = field_type_to_portal_type_map.get(field_type, None)
            if fti_id is not None:
                return getattr(ttool, fti_id, None)

    def applyChanges(self, data):
        content = self.getContent()
        return wizard.applyChanges(self, content, data)

class FieldEditForm(crud.EditForm):
    """ Just a normal CRUD edit form with a custom template that doesn't nest FORMs.
    """
    editsubform_factory = FieldEditSubForm
    
    template = ViewPageTemplateFile('crud_orderable_edit_form.pt')

class FormFieldsStep(wizard.Step, crud.CrudForm):
    template = ViewPageTemplateFile('crud_orderable_form.pt')
    prefix = 'formfields'
    label = _(u'Form Fields')
    description = _(u'Configure the fields that will comprise your letter. Default options are ' +
                    u'provided below, but you may remove or alter them, or add new ones.')

    fields = {}
    add_schema = IFormField
    update_schema = IOrderedFormField
    addform_factory = FieldAddForm
    editform_factory = FieldEditForm

    def _get_fields(self):
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
                    'title': f.Title(),
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
