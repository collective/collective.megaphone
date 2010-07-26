from zope.interface import implements, Invalid
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope import schema
from zope.schema.interfaces import IText
from z3c.form import validator
from Products.PloneFormGen.dollarReplace import dollarRE
from collective.z3cform.wizard import wizard
from collective.megaphone import MegaphoneMessageFactory as _

class GroupWizardStep(wizard.GroupStep):
    template = ViewPageTemplateFile('group_wizard_step.pt')

class IMegaphoneFormTemplateField(IText):
    pass

class MegaphoneFormTemplateField(schema.Text):
    implements(IMegaphoneFormTemplateField)

class MegaphoneFormTemplateVariableValidator(validator.SimpleFieldValidator):

    def validate(self, value):
        super(MegaphoneFormTemplateVariableValidator, self).validate(value)

        valid_fields = set(['sender_%s' % f for f in 
            self.view.wizard.session.get('formfields', {}).get('fields', {}).keys()])
        valid_fields.add('sender_public_name')
        for match in dollarRE.findall(value):
            if match not in valid_fields:
                raise Invalid(_(u'You used an invalid variable substitution.'))

validator.WidgetValidatorDiscriminators(MegaphoneFormTemplateVariableValidator, field=IMegaphoneFormTemplateField)
