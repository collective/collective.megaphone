from collective.z3cform.wizard import wizard
from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.browser.general_step import GeneralSettingsStep
from collective.megaphone.browser.fields_step import FormFieldsStep
from collective.megaphone.browser.recipients_step import RecipientsStep
from collective.megaphone.browser.template_step import TemplateStep
from collective.megaphone.browser.thankyou_step import ThankYouStep
from collective.megaphone.browser.savedata_step import SaveDataStep
from collective.megaphone.browser.signers_step import SignersStep
from collective.megaphone.interfaces import IMegaphone
from plone.z3cform.layout import FormWrapper
from plone.app.kss.plonekssview import PloneKSSView
from kss.core import kssaction
from Products.PloneFormGen.content.form import FormFolder
from z3c.form import field
from zope.app.container.interfaces import IAdding
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component.factory import Factory
from zope.interface import alsoProvides, Interface
from zope import schema
from zope.annotation.interfaces import IAnnotations
from collective.megaphone.config import ANNOTATION_KEY
from persistent.dict import PersistentDict


MegaphoneActionFactory = Factory(
    FormFolder,
    title=_(u'Create a new Megaphone Action')
    )


class IMegaphoneType(Interface):
    
    megaphone_type = schema.Choice(
        title = _(u'Megaphone Action Type'),
        description = _(u'You may create a letter or a petition. The type of action you choose '
                        u'will determine what additional options are available.'),
        values = ('letter', 'petition'),
        default = 'letter',
        )

class IntroStep(wizard.Step):
    index = ViewPageTemplateFile('intro.pt')
    prefix = 'intro'
    label = _(u'Intro')
    fields = field.Fields(IMegaphoneType)
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['megaphone_type'] = data['megaphone_type']

    def load(self, pfg):
        data = self.getContent()
        data['megaphone_type'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('megaphone_type', 'letter')


class MegaphoneActionWizard(wizard.Wizard):
    label = _(u'Megaphone Action Wizard')
    
    @property
    def steps(self):
        if IAdding.providedBy(self.context):
            # initial creation; show intro
            steps = [IntroStep]
        else:
            # returning to edit; skip intro
            steps = []
        
        megaphone_type = self.session.get('intro', {}).get('megaphone_type', 'letter')
        if 'intro.widgets.megaphone_type' in self.request.form:
            megaphone_type = self.request.form['intro.widgets.megaphone_type'][0]
        if megaphone_type == 'letter':
            steps.extend([GeneralSettingsStep, FormFieldsStep, RecipientsStep, TemplateStep, ThankYouStep, SaveDataStep])
        else:
            steps.extend([GeneralSettingsStep, FormFieldsStep, ThankYouStep, SaveDataStep, SignersStep])
        
        return steps

    def initialize(self):
        if IMegaphone.providedBy(self.context):
            # in use with a pre-existing PFG
            self.loadSteps(self.context)

    def applySteps(self, pfg, initial_finish=True):
        """
        Run the apply method for each step in the wizard
        """
        for step in self.activeSteps:
            if hasattr(step, 'apply'):
                step.apply(pfg, initial_finish=initial_finish)

    def finish(self):
        data = self.session
        if IAdding.providedBy(self.context):
            # creating a new letter
            container = self.context.context
            id = container.generateUniqueId("form-folder")
            
            # this is based on the createObject.py script from plone_scripts
            container.invokeFactory(id=id, type_name='FormFolder')
            obj=getattr(container, id, None)
            
            obj.portal_type = 'Megaphone Action'
            obj.setTitle(data['general']['title'])

            # enable preview if there is a letter template configured
            if data.get('template', {}).get('template', ''):
                obj.setSubmitLabel('Preview')
            else:
                obj.setSubmitLabel('Send')
            
            # delete the default form fields that come w/ PFG
            existing_ids = obj.objectIds()
            deleters = ("mailer", "replyto", "topic", "comments")
            deleters = [d for d in deleters if d in existing_ids]
            obj.manage_delObjects(deleters)
            obj.setActionAdapter(())
            if obj._at_rename_after_creation:
                obj._renameAfterCreation()
            alsoProvides(obj, IMegaphone)
            
            if not obj.getRawAfterValidationOverride():
                obj.setAfterValidationOverride('here/@@recipient_multiplexer')
            
            obj['thank-you'].setShowAll(0)
            
            self.request.response.redirect("%s/@@letter-summary?new=1" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=True)

        else:
            # existing letter
            obj = self.context
            self.request.response.redirect("%s/@@letter-summary" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=False)

        obj.reindexObject()

class MegaphoneActionWizardView(FormWrapper):
    
    form = MegaphoneActionWizard
    
    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        request.set('disable_border', 1)

class MegaphoneWizardNullFormValidation(PloneKSSView):
    """Disable inline validation for the Megaphone wizard.
    """
    @kssaction
    def validate_input(self, *args):
        return
