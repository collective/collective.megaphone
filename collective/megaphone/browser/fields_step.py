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
from Products.PloneFormGen.interfaces import IPloneFormGenField

class IFormField(Interface):
    field_type = schema.Choice(
        title = u'Field type',
        description = u'Select the type of field you would like to add to the letter.',
        vocabulary = SimpleVocabulary.fromItems((
            ('String', 'string'),
            ('Text', 'text'),
            ('Yes/No', 'boolean'),
            )),
        required = True,
        default = 'string',
        )
    
    title = schema.TextLine(
        title = u'Name of field',
        )
    
    description = schema.Text(
        title = u'Description',
        description = u'Additional instructions to help the user creating the letter.',
        required = False,
        missing_value = u'',
        )
    
    required = schema.Bool(
        title = u'Is this field required?',
        required = True,
        default = True,
        )

class IOrderedFormField(IFormField):
    order = schema.Int(
        required = False,
        )

class IStringFormField(IOrderedFormField):
    default = schema.TextLine(
        title = u'Default value',
        description = u'Enter a default value for this form field.',
        required = False,
        )
    
    validator = schema.Choice(
        title = u'Validator',
        description = u"Select a pattern to check this form field's input against.",
        vocabulary = 'collective.megaphone.vocabulary.string_validators',
        required = True,
        )

class ITextFormField(IOrderedFormField):
    default = schema.Text(
        title = u'Default value',
        description = u'Enter a default value for this form field.',
        required = False,
        )

class IBooleanFormField(IOrderedFormField):
    default = schema.Bool(
        title = u'Default value',
        description = u'Select the default value for this form field.',
        required = False,
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
    label = u'Add a new field'
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
        }
        field_schema = field_type_map.get(self.content['field_type'], IOrderedFormField)

        fields = field.Fields(self._select_field()) + field.Fields(field_schema).omit('field_type')
        fields['order'].mode = HIDDEN_MODE
        return fields
    
    def applyChanges(self, data):
        content = self.getContent()
        wizard.applyChanges(self, content, data)

class FieldEditForm(crud.EditForm):
    """ Just a normal CRUD edit form with a custom template that doesn't nest FORMs.
    """
    editsubform_factory = FieldEditSubForm
    
    template = ViewPageTemplateFile('crud_orderable_edit_form.pt')

class FormFieldsStep(wizard.Step, crud.CrudForm):
    template = ViewPageTemplateFile('crud_orderable_form.pt')
    prefix = 'formfields'
    label = 'Form Fields'
    description = u'Configure the fields that will comprise your letter. Default options are '+\
                  u'provided below, but you may remove or alter them, or add new ones.'

    fields = {}
    add_schema = IFormField
    update_schema = IOrderedFormField
    addform_factory = FieldAddForm
    editform_factory = FieldEditForm

    # XXX display the field type

    def _get_fields(self):
        return self.getContent().setdefault('fields', {
            'body': {
                'field_type': 'text',
                'title': u'Letter Body',
                'description': u'',
                'required': True,
                'order': 0,
                },
            'first': {
                'title': u'First Name',
                'description': u'',
                'required': True,
                'order': 1,
                },
            'last': {
                'title': u'Last Name',
                'description': u'',
                'required': True,
                'order': 2,
                },
            'email': {
                'title': u'E-mail Address',
                'description': u'',
                'required': True,
                'validator': 'isEmail',
                'order': 3,
                },
            'street': {
                'title': u'Street Address',
                'description': u'',
                'required': False,
                'order': 4,
                },
            'city': {
                'title': u'City',
                'description': u'',
                'required': False,
                'order': 5,
                },
            'state': {
                'title': u'State',
                'description': u'',
                'required': False,
                'order': 6,
                },
            'zip': {
                'title': u'Postal Code',
                'description': u'',
                'required': False,
                'validator': 'isZipCode',
                'order': 7,
                },
            })

    def get_items(self):
        return sorted(self._get_fields().items(), key=lambda x: x[1]['order'])

    def add(self, data):
        data['order'] = len(self._get_fields())
        id = getUtility(IIDNormalizer).normalize(data['title'])

        if id in self._get_fields().keys() or id in self.context.objectIds():
            raise schema.ValidationError, u'You selected a field name that is already in use. Please use a different name.'

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

        existing_fields = [f.getId() for f in pfg.objectValues() if IPloneFormGenField.providedBy(f)]
        fields = data['fields']
        for field_id, field_attrs in sorted(fields.items(), key=lambda x: x[1]['order']):
            field_type_to_portal_type_map = {
                'string': 'FormStringField',
                'text': 'FormTextField',
                'boolean': 'FormBooleanField',
            }
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
                fieldinfo = {
                    'field_type': None,
                    'title': f.Title(),
                    'description': f.Description(),
                    'required': f.getRequired(),
                    'order': i,
                }
                if hasattr(f, 'getFgDefault'):
                    fieldinfo['default'] = f.getFgDefault()
                if f.portal_type == 'FormStringField':
                    fieldinfo['field_type'] = 'string'
                    fieldinfo['validator'] = f.getFgStringValidator()
                    if not fieldinfo['validator']:
                        fieldinfo['validator'] = 'vocabulary_none_text'
                if f.portal_type == 'FormBooleanField':
                    fieldinfo['field_type'] = 'boolean'
                    # make sure we match one of the vocab terms
                    if fieldinfo['default'] is not True:
                        fieldinfo['default'] = False
                fields[f.getId()] = fieldinfo
                i += 1
