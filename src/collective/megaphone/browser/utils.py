from zope.interface import implements, Invalid
from zope import schema
from zope.schema.interfaces import IText
from z3c.form import form, validator
from plone.z3cform import z2
from Products.PloneFormGen.dollarReplace import dollarRE
from collective.z3cform.wizard import wizard
from collective.megaphone.compat import ViewPageTemplateFile
from collective.megaphone.utils import MegaphoneMessageFactory as _

class GroupWizardStep(wizard.GroupStep):
    template = ViewPageTemplateFile('group_wizard_step.pt')

class PopupForm(form.Form):
    template = ViewPageTemplateFile('popup_form.pt')

    _finished = False

    def update(self):
        # BBB for Zope 2.10
        z2.switch_on(self)
        super(PopupForm, self).update()

    def render(self):
        if self._finished:
            # close popup
            return _(u'Form submitted successfully.')
        return super(PopupForm, self).render()

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
