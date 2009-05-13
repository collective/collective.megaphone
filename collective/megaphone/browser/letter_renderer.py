from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.annotation import IAnnotations
from collective.megaphone.config import ANNOTATION_KEY
from persistent.dict import PersistentDict
from Products.PloneFormGen import dollarReplace

def _dreplace(t, request):
    vars = {}
    for k, v in request.form.items():
        if not k.startswith('recip_'):
            k = 'sender_%s' % k
        vars[k] = v
    return dollarReplace.DollarVarReplacer(vars).sub(t)

class LetterRenderer(BrowserView):
    """
    This is a view of an action letter which renders the letter based on the
    request form variables and the template stored in an annotation on the
    form folder.
    """
    
    def render_letter(self):
        annotation = IAnnotations(self.context).get(ANNOTATION_KEY, PersistentDict())
        transformer = getToolByName(self.context, 'portal_transforms')
        template = annotation.get('template', '')
        return transformer('web_intelligent_plain_text_to_html', _dreplace(template, self.request))

    def render_thankyou(self):
        annotation = IAnnotations(self.context).get(ANNOTATION_KEY, PersistentDict())
        transformer = getToolByName(self.context, 'portal_transforms')
        template = annotation.get('thankyou_template', '')
        return transformer('web_intelligent_plain_text_to_html', _dreplace(template, self.request))

class LetterMailerRenderer(BrowserView):
    """
    Helpers for use with a form mailer inside an action letter.
    """

    def render_subject(self):
        nosubject = '(no subject)'
        subject = getattr(self.context, 'msg_subject', nosubject)
        subjectField = self.request.form.get(self.context.subject_field, None)
        if subjectField is not None:
            subject = subjectField
        else:
            # we only do subject expansion if there's no field chosen
            subject = _dreplace(subject, self.request)
        return subject

    def sender_envelope(self):
        try:
            fullname = ' '.join([self.request.form['first-name'], self.request.form['last-name']])
        except KeyError:
            fullname = None
        
        if fullname is not None:
            # XXX I would use the form's replyto_field setting, but if that
            # is set then the PFG mailer will set the Reply-To header which
            # will take precedence over the From header controlled by this
            # override method
            sender = '%s <%s>' % (fullname, self.request.form['email'])
        else:
            sender = self.request.form['email']
        
        return sender
