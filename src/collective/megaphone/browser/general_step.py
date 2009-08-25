from collective.megaphone import MegaphoneMessageFactory as _
from collective.z3cform.wizard import wizard
from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from z3c.form import field
from z3c.form.interfaces import INPUT_MODE
from zope import schema
from zope.interface import Interface
from Acquisition import ImplicitAcquisitionWrapper
from Products.CMFPlone.utils import safe_unicode
from UserDict import UserDict

class IGeneralSettings(Interface):
    title = schema.TextLine(
        title = _(u'Title of Letter'),
        description = _(u'Your letter will show up with this title in listings in Plone.'),
        )
    
    intro = schema.Text(
        title = _(u'Intro Text'),
        description = _(u'This text will be shown above the form prompting activists to send a letter. ' +
                        u'Use this to convince them to take action, list talking points, etc.'),
        required = False,
        missing_value = '',
        )

class GeneralSettingsStep(wizard.Step):
    prefix = 'general'
    label = _(u'General Settings')

    fields = field.Fields(IGeneralSettings)
    fields['intro'].widgetFactory[INPUT_MODE] = WysiwygFieldWidget

    def update(self):
        wizard.Step.update(self)
        self.widgets['title'].size = 30
        self.widgets['intro'].rows = 10
        
        # this is pretty stupid, but the wysiwyg widget needs to be able to acquire
        # things from the widget context, which is a dict in this wizard scenario,
        # and TALES traversal short-circuits to item lookup for normal dicts
        self.widgets['intro'].context = ImplicitAcquisitionWrapper(UserDict(self.widgets['intro'].context), self.context)

    def apply(self, pfg, initial_finish=True):
        """
        Apply changes to the underlying PloneFormGen form based on the submitted values.
        """
        data = self.getContent()
        pfg.setTitle(data['title'])
        pfg.setFormPrologue(data['intro'], mimetype='text/html')

    def load(self, pfg):
        data = self.getContent()
        data['title'] = safe_unicode(pfg.Title())
        data['intro'] = safe_unicode(pfg.getRawFormPrologue())
