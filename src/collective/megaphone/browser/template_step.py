from collective.megaphone.config import ANNOTATION_KEY, RECIPIENT_MAILER_ID, DEFAULT_LETTER_TEMPLATE
from collective.megaphone.browser.recipients_step import REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from z3c.form import field
from zope import schema
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

class ITemplateStep(Interface):
    subject = schema.TextLine(
        title = u'E-mail subject',
        description = u'Enter the template for the e-mail subject. You may use the listed variables.',
        default = u'Dear ${recip_honorific} ${recip_first} ${recip_last}'
        )
    
    template = schema.Text(
        title = u'Letter Text',
        description = u'Enter the text of the letter. You may use the listed variables.',
        default = DEFAULT_LETTER_TEMPLATE
        )

class TemplateStep(wizard.Step):
    template = ViewPageTemplateFile('template_step.pt')
    
    prefix = 'template'
    label = 'Letter to Decisionmaker(s)'
    description = u"This step allows you to configure the subject and text of the message " + \
                  u"which will be sent to each of the recipients."
    fields = field.Fields(ITemplateStep)

    def update(self):
        wizard.Step.update(self)
        helptext = '<em>foo</em>'
        self.widgets['subject'].size = 50
        self.widgets['template'].rows = 10

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = (REQUIRED_LABEL_ID, OPTIONAL_SELECTION_ID, 'sincerely')
        vars = [('sender_%s' % f_id, "Sender's %s" % f['title'])
            for f_id, f in sorted(fields.items(), key=lambda x:x[1]['order'])
            if f_id not in ignored_fields]
        vars += (
            ('recip_honorific', "Recipient's Honorific"),
            ('recip_first', "Recipient's First"),
            ('recip_last', "Recipient's Last"),
            )
        return [dict(title=title, id=id) for id, title in vars]
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['template'] = data['template']
        mailer = getattr(pfg, RECIPIENT_MAILER_ID)
        mailer.setMsg_subject(data['subject'])
        if not mailer.getRawSenderOverride():
            mailer.setSenderOverride('here/@@letter-mailer-renderer/sender_envelope')
        if not mailer.getRawSubjectOverride():
            mailer.setSubjectOverride('here/@@letter-mailer-renderer/render_subject')
    
    def load(self, pfg):
        data = self.getContent()
        data['template'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('template', '')
        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        if mailer is not None:
            data['subject'] = mailer.getMsg_subject()
