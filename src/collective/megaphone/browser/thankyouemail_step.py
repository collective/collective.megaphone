from collective.megaphone.config import THANK_YOU_EMAIL_ID, ANNOTATION_KEY, \
    THANKYOU_MAILTEMPLATE_BODY, DEFAULT_THANKYOU_TEMPLATE
from collective.megaphone.browser.recipients_step import REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from plone.app.controlpanel.mail import IMailSchema
from z3c.form import field
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.interfaces import ISiteRoot
from Products.PloneFormGen.config import DEFAULT_MAILTEMPLATE_BODY


class IThankYouEmailStep(Interface):
    subject = schema.TextLine(
        title = u'E-mail subject',
        description = u'Enter the template for the e-mail subject. You may use the above variables.',
        default = u'Thanks for your letter, ${sender_first}'
        )

    from_addr = schema.TextLine(
        title = u'"From" E-mail Address',
        description = u'From whom should your thank you email appear to be?',
        # XXX use site from address as default
        )
    
    template = schema.Text(
        title = u'Thank you message',
        description = u'Enter the text of the thank you message. You may use the above variables.',
        default = DEFAULT_THANKYOU_TEMPLATE
        )


class ThankYouEmailStep(wizard.Step):
    """Step for optionally creating and configuring a thank you email to letter-writer"""
    
    template = ViewPageTemplateFile("thankyouemail_step.pt")
    
    prefix = 'thanksemail'
    label  = "Thank You to Activist"
    description = u"It's a good idea to send a thank you email to someone who has taken " +\
                  u"action on your behalf. This step allows you to configure that e-mail."

    fields = field.Fields(IThankYouEmailStep)

    def update(self):
        wizard.Step.update(self)
        self.widgets['template'].rows = 10
        self.widgets['subject'].size = 50
        
        if not self.widgets['from_addr'].value:
            portal = getUtility(ISiteRoot)
            from_addr = IMailSchema(portal).email_from_address
            self.widgets['from_addr'].value = IMailSchema(portal).email_from_address

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = (REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID)
        vars = [('sender_%s' % f_id, "Sender's %s" % f['title'])
            for f_id, f in fields.items()
            if f_id not in ignored_fields]
        return [dict(title=title, id=id) for id, title in sorted(vars, key=lambda x: x[1])]
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        if THANK_YOU_EMAIL_ID not in pfg.objectIds():
            pfg.invokeFactory(id=THANK_YOU_EMAIL_ID, type_name="FormMailerAdapter")
            mailer = getattr(pfg, THANK_YOU_EMAIL_ID)
            mailer.setTitle("Thank you email to letter writer")
        else:
            mailer = getattr(pfg, THANK_YOU_EMAIL_ID)
        if data.get("from_addr", None):
            mailer.setSenderOverride('string:' + data['from_addr'])
        if mailer.getTo_field() == '#NONE#':
            mailer.setTo_field('email')
        mailer.setMsg_subject(data['subject'])
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['thankyou_template'] = data['template']
        # replace default mail template body with our own version, unless its been customized
        if mailer.getRawBody_pt() == DEFAULT_MAILTEMPLATE_BODY:
            mailer.setBody_pt(THANKYOU_MAILTEMPLATE_BODY)
        if not mailer.getRawSubjectOverride():
            mailer.setSubjectOverride('here/@@letter-mailer-renderer/render_subject')
    
    def load(self, pfg):
        data = self.getContent()
        mailer = getattr(pfg, THANK_YOU_EMAIL_ID, None)
        if mailer is not None:
            data['subject'] = mailer.getMsg_subject()
            from_addr = mailer.getRawSenderOverride()
            if from_addr.startswith('string:'):
                data['from_addr'] = from_addr[7:]
        data['template'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('thankyou_template', '')
