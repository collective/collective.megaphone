from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.config import ANNOTATION_KEY, DEFAULT_SIGNER_LISTING_TEMPLATE
from collective.megaphone.browser.recipients_step import REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from z3c.form import field, validator
from zope import schema
from zope.interface import Interface, Invalid
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Products.PloneFormGen.dollarReplace import dollarRE

class ISignersStep(Interface):
    show_signers = schema.Bool(
        title = _(u'Display signers'),
        default = False,
        )
    
    batch_size = schema.Choice(
        title = _(u'Batch size'),
        description = _(u'Petition signers will be presented in batches. Choose the number '
                        u'per page you would like to see.'),
        values = (10, 20, 30, 50),
        default = 30
        )
    
    template = schema.Text(
        title = _(u'Template'),
        description = _(u"Prefacing field names from your petition with dollar signs, "
                        u"format how you would like rows of signers' names to show up "
                        u"in the listing. If you would like these rows in a table, you "
                        u"may separate cells with a pipe ('|'). The available fields are "
                        u"listed below." ),
        default = DEFAULT_SIGNER_LISTING_TEMPLATE,
        )

class SignersStep(wizard.Step):
    template = ViewPageTemplateFile('template_step.pt')
    
    prefix = 'signers'
    label = _(u'List Signers')
    description = _(u"This step allows you to configure how to present a list of the people "
                    u"who have signed your petition, to demonstrate the power your petition "
                    u"is generating, and/or to encourage more people to join the cause.")
    fields = field.Fields(ISignersStep)

    def update(self):
        wizard.Step.update(self)
        self.widgets['template'].rows = 2

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = (REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID, 'sincerely')
        vars = [('sender_%s' % f_id, _(u"Sender's $varname", mapping={'varname': f['title']}))
            for f_id, f in sorted(fields.items(), key=lambda x:x[1]['order'])
            if f_id not in ignored_fields]
        return [dict(title=title, id=id) for id, title in vars]
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['signers'] = data
    
    def load(self, pfg):
        data = self.getContent()
        data.update(IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('signers', ''))

class TemplateVariableValidator(validator.SimpleFieldValidator):
    
    def validate(self, value):
        super(TemplateVariableValidator, self).validate(value)
        
        valid_fields = set(['sender_%s' % f for f in 
            self.view.wizard.session.get('formfields', {}).get('fields', {}).keys()])
        for match in dollarRE.findall(value):
            if match not in valid_fields:
                raise Invalid(_(u'You used an invalid variable substitution.'))

validator.WidgetValidatorDiscriminators(TemplateVariableValidator, field=ISignersStep['template'])
