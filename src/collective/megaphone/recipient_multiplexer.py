from zope.component import getMultiAdapter, getAdapters
from zope.interface import Interface
from Products.CMFPlone.utils import safe_hasattr
from Products.CMFCore.Expression import getExprContext
from Products.Archetypes.interfaces.field import IField
from Products.PloneFormGen.interfaces import IPloneFormGenActionAdapter
from collective.megaphone import implementedOrProvidedBy
from collective.megaphone.interfaces import IRecipientSource


class IMultiplexedActionAdapter(Interface):
    """
    Marker interface for form action adapters that will be called multiple
    times.
    """

def request_variable_multiplexer(request, datasets):
    """
    Generator that swaps out a set of request variables.
    """
    orig_form = request.form.copy()
    for data in datasets:
        request.form = orig_form.copy()
        request.form.update(data)
        yield request
    request.form = orig_form

def lookup_recipients(pfg, request):
    # call the lookup method for each type
    for _, source in getAdapters((pfg, request), IRecipientSource):
        for recipient in source.lookup():
            yield recipient

def recipient_multiplexer(pfg, request):
    """
    Returns a generator that swaps out request variables for each recipient.
    """
    recipient_vars = []
    for r in lookup_recipients(pfg, request):
        recipient_vars.append({
            'recip_honorific': r['honorific'],
            'recip_email': r['email'],
            'recip_first': r['first'],
            'recip_last': r['last'],
            })
    if not recipient_vars:
        recipient_vars = [{
            'recip_honorific': '',
            'recip_email': '',
            'recip_first': '',
            'recip_last': '',
            }]
    
    renderer = getMultiAdapter((pfg, request), name=u'letter-renderer')
    
    orig_form = request.form.copy()
    for data in recipient_vars:
        request.form = orig_form.copy()
        request.form.update(data)
        request.form['rendered-letter'] = renderer.render_plaintext_letter()
        yield request
    request.form = orig_form

class ActionAdapterMultiplexer(object):
    """
    Abstract class for a PloneFormGen action adapter multiplexer that can be
    called from the form's after-validation override.
    
    Override the 'generator' method with something returning an instance of
    request_variable_multiplexer that swaps out the request variables as needed.
    """
    
    def generator(self):
        raise NotImplemented
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.fields = [fo for fo in context._getFieldObjects() if not implementedOrProvidedBy(IField, fo)]
        
        self.action_adapters = [a for a in self.context.contentValues()
            if IPloneFormGenActionAdapter.providedBy(a)
            and IMultiplexedActionAdapter.providedBy(a)
            ]
    
    def __call__(self):
        orig_form = self.request.form.copy()
        for request in self.generator(self.context, self.request):
            
            # execute action adapters
            try:
                for actionAdapter in self.action_adapters:
                    # Now, see if we should execute it.
                    # Check to see if execCondition exists and has contents
                    if safe_hasattr(actionAdapter, 'execCondition') and \
                      len(actionAdapter.getRawExecCondition()):
                        # evaluate the execCondition.
                        # create a context for expression evaluation
                        context = getExprContext(self, actionAdapter)
                        doit = actionAdapter.getExecCondition(expression_context=context)
                    else:
                        # no reason not to go ahead
                        doit = True
                
                    if doit:
                        result = actionAdapter.onSuccess(self.fields, REQUEST=request)
                        if type(result) is type({}) and len(result):
                            # return the dict, which hopefully uses
                            # field ids or FORM_ERROR_MARKER for keys
                            return result
            finally:
                self.request.form = orig_form

class FormRecipientMultiplexer(ActionAdapterMultiplexer):
    """
    This class adapts a PloneFormGen form.  When called, it will, for each
    recipient found in an annotation on the form:
        * Set variables for the recipient in the request form.
        * Call any action adapters that are marked with IMultiplexed
    
    This class is meant to be used from the after-validation override of the
    PloneFormGen form being adapted.  You will want to add execution conditions
    to the action adapters being multiplexed so that they don't get run by
    the normal PFG action adapter execution, or else disable them.
    """
    
    def generator(self, *args):
        return recipient_multiplexer(*args)
