from Products.CMFPlone.utils import safe_unicode
from Acquisition import aq_inner
from Products.Archetypes.interfaces.field import IField
from Products.Five import BrowserView
from Products.Five.browser import decode
from Products.CMFCore.utils import getToolByName
from zope.annotation import IAnnotations
from collective.megaphone.utils import implementedOrProvidedBy
from zope.component import getAdapters
from collective.megaphone.config import ANNOTATION_KEY
from collective.megaphone.interfaces import IRecipientSource, IVariableProvider
from collective.megaphone.recipient_multiplexer import recipient_multiplexer
from persistent.dict import PersistentDict
from Products.PloneFormGen import dollarReplace

def _dreplace(t, form, request):
    vars = {}
    fields = [fo for fo in form._getFieldObjects()
              if not implementedOrProvidedBy(IField, fo)]
    for field in fields:
        fname = 'sender_' + field.__name__
        value = field.htmlValue(request)
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        transformer = getToolByName(form, 'portal_transforms')
        value = transformer('html_to_web_intelligent_plain_text', value)
        vars[fname] = safe_unicode(value.strip())
    for k, v in request.form.items():
        if not k.startswith('recip_'):
            continue
        vars[k] = safe_unicode(v)
    for k, adapter in getAdapters((form, request), IVariableProvider):
        v = adapter()
        vars[k] = v
    return dollarReplace.DollarVarReplacer(vars).sub(t)

def decode_form_inputs(func):
    def decoded_request_func(self, *args, **kw):
        if 'request' in kw:
            request = kw['request']
        else:
            try:
                request = self.request
            except AttributeError:
                raise ValueError('Unable to find request.')
        
        orig_form = request.form.copy()
        decode.processInputs(request)
        res = func(self, *args, **kw)
        request.form = orig_form
        return res
    return decoded_request_func

class MegaphoneRenderer(BrowserView):
    """
    This is a view of a Megaphone action which renders the letter based on the
    request form variables and the template stored in an annotation on the
    form folder.
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.data = IAnnotations(context).get(ANNOTATION_KEY, PersistentDict())

    def render_letter(self, request=None):
        if request is None:
            request = self.request
        transformer = getToolByName(self.context, 'portal_transforms')
        template = self.data.get('template', '${sender_body}')
        return transformer(
            'web_intelligent_plain_text_to_html',
            _dreplace(template, self.context, request)
            )

    def render_plaintext_letter(self):
        template = self.data.get('template', '${sender_body}')
        return _dreplace(template, self.context, self.request).encode('utf8')

    def render_all_letters(self):
        letters = []
        for request in recipient_multiplexer(self.context, self.request):
            letters.append(self.render_letter(request=request))
        return letters

    def render_thankyou(self):
        transformer = getToolByName(self.context, 'portal_transforms')
        template = self.data.get('thankyou_template', '')
        return transformer(
            'web_intelligent_plain_text_to_html',
            _dreplace(template, self.context, self.request)
            )
    
    def render_recipient_source_snippets(self):
        out = []
        for _, source in getAdapters((self.context, self.request), IRecipientSource):
            out.append(source.render_form())
        return ''.join(out)


class LetterMailerRenderer(BrowserView):
    """
    Helpers for use with a form mailer inside a Megaphone action.
    """

    def render_subject(self):
        nosubject = '(no subject)'
        subject = getattr(self.context, 'msg_subject', nosubject)
        subjectField = self.request.form.get(self.context.subject_field, None)
        if subjectField is not None:
            subject = subjectField
        else:
            # we only do subject expansion if there's no field chosen
            form = aq_inner(self.context).aq_parent
            subject = _dreplace(subject, form, self.request)
        return subject

    @decode_form_inputs
    def sender_envelope(self):
        try:
            fullname = ' '.join([self.request.form['first'], self.request.form['last']])
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
