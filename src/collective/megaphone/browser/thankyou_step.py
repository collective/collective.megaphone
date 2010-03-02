from collective.megaphone import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import THANK_YOU_EMAIL_ID, ANNOTATION_KEY, \
    THANKYOU_MAILTEMPLATE_BODY, DEFAULT_THANKYOU_TEMPLATE
from collective.megaphone.browser.recipients_step import REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from plone.app.controlpanel.mail import IMailSchema
from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from z3c.form import field
from z3c.form.interfaces import INPUT_MODE
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Acquisition import ImplicitAcquisitionWrapper
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.i18nl10n import utranslate
from Products.CMFPlone.utils import safe_unicode
from UserDict import UserDict

class IThankYouEmailStep(Interface):
    
    email = schema.Bool(
        title = _(u'Send a thank you e-mail to the sender of the letter.'),
        default = True,
        )
    
    subject = schema.TextLine(
        title = _(u'E-mail subject'),
        description = _(u'Enter the template for the subject of the thank you e-mail. You may use the listed variables.'),
        default = _(u'Thanks for your letter, ${sender_first}'),
        )

    from_addr = schema.TextLine(
        title = _(u'"From" E-mail Address'),
        description = _(u'From whom should your thank you email appear to be?'),
        )
    
    template = schema.Text(
        title = _(u'Thank you e-mail body'),
        description = _(u'Enter the text of the thank you message. You may use the listed variables.'),
        default = DEFAULT_THANKYOU_TEMPLATE
        )
    
    thankyou_text = schema.Text(
        title = _(u'Thank you page text'),
        description = _(u'This text will be displayed in the browser after a letter is '
                        u'successfully sent.'),
        required = False,
        default = _(u'Your letter has been sent successfully.  Thank you.'),
        )
    
    thankyou_url = schema.TextLine(
        title = _(u'Alternative thank you page URL'),
        description = _(u'If you specify a URL here, the letter writer will be '
                        u'redirected to that URL after successfully sending a '
                        u'letter.  The thank you page text above will not be used.'),
        required = False,
        )

class ThankYouStep(wizard.Step):
    """Step for optionally creating and configuring a thank you email to letter-writer"""
    
    template = ViewPageTemplateFile("template_step.pt")
    
    prefix = 'thanks'
    label = _(u"Thank You to Activist")
    description = _(u"It's a good idea to send a thank you email to someone who has taken " +
                    u"action on your behalf. This step allows you to configure that e-mail.")

    fields = field.Fields(IThankYouEmailStep)
    fields['thankyou_text'].widgetFactory[INPUT_MODE] = WysiwygFieldWidget

    def update(self):
        wizard.Step.update(self)
        self.widgets['template'].rows = 10
        self.widgets['subject'].size = 50
        
        if not self.widgets['from_addr'].value:
            portal = getUtility(ISiteRoot)
            self.widgets['from_addr'].value = IMailSchema(portal).email_from_address
        
        self.widgets['thankyou_text'].rows = 10
        # this is pretty stupid, but the wysiwyg widget needs to be able to acquire
        # things from the widget context, which is a dict in this wizard scenario,
        # and TALES traversal short-circuits to item lookup for normal dicts
        self.widgets['thankyou_text'].context = ImplicitAcquisitionWrapper(UserDict(self.widgets['thankyou_text'].context), self.context)
        self.widgets['thankyou_url'].size = 50

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = (REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID, 'sincerely')
        vars = [('sender_%s' % f_id, _("Sender's $varname", mapping={'varname': f['title']}))
            for f_id, f in sorted(fields.items(), key=lambda x:x[1]['order'])
            if f_id not in ignored_fields]
        return [dict(title=title, id=id) for id, title in vars]
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        if THANK_YOU_EMAIL_ID not in pfg.objectIds():
            pfg.invokeFactory(id=THANK_YOU_EMAIL_ID, type_name="FormMailerAdapter")
            mailer = getattr(pfg, THANK_YOU_EMAIL_ID)
            mailer.setTitle(utranslate(DOMAIN, _(u"Thank you email to letter writer"), context=self.request))
        else:
            mailer = getattr(pfg, THANK_YOU_EMAIL_ID)

        action_adapters = list(pfg.getActionAdapter())
        if data['email'] and mailer.getId() not in action_adapters:
            action_adapters.append(mailer.getId())
        elif not data['email'] and mailer.getId() in action_adapters:
            action_adapters.remove(mailer.getId())
        pfg.setActionAdapter(action_adapters)

        if data.get("from_addr", None):
            mailer.setSenderOverride('string:' + data['from_addr'])
        if mailer.getTo_field() == '#NONE#':
            mailer.setTo_field('email')
        mailer.setMsg_subject(data['subject'])
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['thankyou_template'] = data['template']
        # replace default mail template body with our own version, unless its been customized
        formgen_tool = getToolByName(pfg, 'formgen_tool')
        if mailer.getRawBody_pt() == formgen_tool.getDefaultMailTemplateBody():
            mailer.setBody_pt(THANKYOU_MAILTEMPLATE_BODY)
        if not mailer.getRawSubjectOverride():
            mailer.setSubjectOverride('here/@@letter-mailer-renderer/render_subject')
        
        thankyou = getattr(pfg, 'thank-you', None)
        if thankyou is not None:
            thankyou.setThanksPrologue(data['thankyou_text'])
        if data['thankyou_url']:
            pfg.setThanksPageOverride('redirect_to:string:' + data['thankyou_url'])
    
    def load(self, pfg):
        data = self.getContent()
        data['email'] = False
        mailer = getattr(pfg, THANK_YOU_EMAIL_ID, None)
        if mailer is not None:
            data['email'] = (mailer.getId() in pfg.getActionAdapter())
            data['subject'] = safe_unicode(mailer.getMsg_subject())
            from_addr = safe_unicode(mailer.getRawSenderOverride())
            if from_addr.startswith(u'string:'):
                data['from_addr'] = from_addr[7:]
        data['template'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('thankyou_template', '')

        thankyou = getattr(pfg, 'thank-you', None)
        if thankyou is not None:
            data['thankyou_text'] = safe_unicode(thankyou.getRawThanksPrologue())
        else:
            data['thankyou_text'] = u''
        thanksOverride = pfg.getThanksPageOverride()
        if thanksOverride.startswith('redirect_to:string:'):
            data['thankyou_url'] = thanksOverride[19:]
        else:
            data['thankyou_url'] = ''
