from collective.z3cform.wizard import wizard
from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.utils import get_megaphone_defaults
from collective.megaphone.browser.general_step import GeneralSettingsStep
from collective.megaphone.browser.fields_step import FormFieldsStep
from collective.megaphone.browser.recipients_step import RecipientsStep
from collective.megaphone.browser.template_step import TemplateStep
from collective.megaphone.browser.thankyou_step import ThankYouStep
from collective.megaphone.browser.salesforce_step import SalesforceStep, salesforce_is_configured
from collective.megaphone.browser.signers_step import SignersStep
from collective.megaphone.interfaces import IMegaphone
from collective.megaphone.recipient_multiplexer import IMultiplexedActionAdapter
from plone.z3cform.layout import FormWrapper
from plone.app.kss.plonekssview import PloneKSSView
from kss.core import kssaction
from Products.PloneFormGen.content.form import FormFolder
from z3c.form import field
from zope.app.container.interfaces import IAdding
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component.factory import Factory
from zope.event import notify
from zope.interface import alsoProvides, Interface
from zope import schema
from zope.annotation.interfaces import IAnnotations
from collective.megaphone.config import ANNOTATION_KEY, SAVEDATA_ID, RENDERED_LETTER_ID
from persistent.dict import PersistentDict
from Products.Archetypes.event import ObjectInitializedEvent, ObjectEditedEvent
from Products.CMFPlone.i18nl10n import utranslate


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
        # XXX this should probably get adapterized in some fashion

        steps = []
        if not IMegaphone.providedBy(self.context):
            # initial creation or editing site defaults; show intro
            steps = [IntroStep]
            megaphone_type = self.session.get('intro', {}).get('megaphone_type', 'letter')
        else:
            megaphone_type = IAnnotations(self.context).get(ANNOTATION_KEY, {}).get('megaphone_type', 'letter')
        if 'intro.widgets.megaphone_type' in self.request.form:
            megaphone_type = self.request.form['intro.widgets.megaphone_type'][0]
        if megaphone_type == 'letter':
            steps.extend([GeneralSettingsStep, FormFieldsStep, RecipientsStep, TemplateStep, ThankYouStep])
        else:
            steps.extend([GeneralSettingsStep, FormFieldsStep, ThankYouStep])
        if salesforce_is_configured():
            steps.append(SalesforceStep)
        if megaphone_type == 'petition':
            steps.append(SignersStep)
        
        return steps

    def initialize(self):
        if IMegaphone.providedBy(self.context):
            # in use with a pre-existing PFG
            self.loadSteps(self.context)
        else:
            # initialize with site defaults
            self.session.update(get_megaphone_defaults())

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
            
            self.request.response.redirect("%s/@@summary?new=1" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=True)

        else:
            # existing letter
            obj = self.context
            self.request.response.redirect("%s/@@summary" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=False)

        # make sure the saved data adapter is configured properly
        existing_ids = obj.objectIds()
        if SAVEDATA_ID not in existing_ids:
            obj.invokeFactory(id=SAVEDATA_ID, type_name="FormSaveDataAdapter")
            sda = getattr(obj, SAVEDATA_ID)
            alsoProvides(sda, IMultiplexedActionAdapter)
            sda.setTitle(utranslate(DOMAIN, _(u'Saved Signatures'), context=self.request))
        sda = getattr(obj, SAVEDATA_ID)
        adapters = list(obj.actionAdapter)
        if SAVEDATA_ID in adapters:
            adapters.remove(SAVEDATA_ID)
            obj.setActionAdapter(adapters)
        execCondition = sda.getRawExecCondition()
        if not execCondition or execCondition in ('python:True', 'python:False'):
            sda.setExecCondition('python:True')

        if RENDERED_LETTER_ID not in existing_ids:
            obj.invokeFactory(id=RENDERED_LETTER_ID, type_name='FormStringField')
            f = getattr(obj, RENDERED_LETTER_ID)
            f.setServerSide(True)
            f.setTitle(utranslate(DOMAIN, _(u'Rendered Letter'), context=self.request))
            f.setDescription(utranslate(DOMAIN, _(u'This hidden field is used to provide the rendered letter to the mailer and save data adapters.'), context=self.request))

        obj.reindexObject()
        
        if IAdding.providedBy(self.context):
            notify(ObjectInitializedEvent(obj))
        else:
            notify(ObjectEditedEvent(obj))


class MegaphoneActionWizardView(FormWrapper):
    
    form = MegaphoneActionWizard
    
    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        request.set('disable_border', 1)
    
    def absolute_url(self):
        return '%s/%s' % (self.context.absolute_url(), self.__name__)

class MegaphoneWizardNullFormValidation(PloneKSSView):
    """Disable inline validation for the Megaphone wizard.
    """
    @kssaction
    def validate_input(self, *args):
        return
