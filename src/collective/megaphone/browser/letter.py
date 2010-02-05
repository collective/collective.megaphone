from collective.z3cform.wizard import wizard
from collective.megaphone import MegaphoneMessageFactory as _
from collective.megaphone.browser.general_step import GeneralSettingsStep
from collective.megaphone.browser.fields_step import FormFieldsStep
from collective.megaphone.browser.recipients_step import RecipientsStep
from collective.megaphone.browser.template_step import TemplateStep
from collective.megaphone.browser.thankyou_step import ThankYouStep
from collective.megaphone.browser.savedata_step import SaveDataStep
from collective.megaphone.interfaces import IActionLetter
from plone.z3cform.layout import FormWrapper
from Products.PloneFormGen.content.form import FormFolder
from z3c.form import field
from zope.app.container.interfaces import IAdding
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component.factory import Factory
from zope.interface import alsoProvides

ActionLetterFactory = Factory(
    FormFolder,
    title=_(u'Create a new action letter')
    )


class IntroStep(wizard.Step):
    index = ViewPageTemplateFile('intro.pt')
    prefix = 'intro'
    label = _(u'Intro')
    fields = field.Fields()


class ActionLetterWizard(wizard.Wizard):
    steps = IntroStep, GeneralSettingsStep, FormFieldsStep, RecipientsStep, \
        TemplateStep, ThankYouStep, SaveDataStep
    label = _(u'Action Letter Wizard')

    def initialize(self):
        if IActionLetter.providedBy(self.context):
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
            
            obj.portal_type = 'Action Letter'
            obj.setTitle(data['general']['title'])
            obj.setSubmitLabel('Preview')
            existing_ids = obj.objectIds()
            
            # delete the default form fields that come w/ PFG
            deleters = ("mailer", "replyto", "topic", "comments")
            deleters = [d for d in deleters if d in existing_ids]
            obj.manage_delObjects(deleters)
            obj.setActionAdapter(())
            if obj._at_rename_after_creation:
                obj._renameAfterCreation()
            alsoProvides(obj, IActionLetter)
            
            obj['thank-you'].setShowAll(0)
            
            self.request.response.redirect("%s/@@letter-summary?new=1" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=True)

        else:
            # existing letter
            obj = self.context
            self.request.response.redirect("%s/@@letter-summary" % (obj.absolute_url()))
            self.applySteps(obj, initial_finish=False)

        obj.reindexObject()

class ActionLetterWizardView(FormWrapper):
    
    form = ActionLetterWizard
    
    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        request.set('disable_border', 1)
