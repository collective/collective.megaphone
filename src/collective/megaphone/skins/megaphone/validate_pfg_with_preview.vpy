## Controller Validator "validate_action_letter"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##
FORM_ERROR_MARKER = '_pfg_form_error'

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.utils import addStatusMessage

request = context.REQUEST
preview = ('form_send' not in request.form)

errors = state.getErrors()
errors = context.fgvalidate(REQUEST=request, errors=errors, data=1, metadata=0, skip_action_adapters=True)

if not preview and (not errors or (len(errors) == 1 and errors.keys()[0] == 'captcha')):
    # (don't require captcha after preview step)
    errors = context.fgProcessActionAdapters(errors=[], REQUEST=request)
    if not errors or (len(errors) == 1 and errors.keys()[0] == 'captcha'):
        nextAction = context.fgGetSuccessAction()
        state.setNextAction( nextAction )

        if nextAction.find('fg_result_view') > 0:
            return state.set(portal_status_message='Form validated.')

        return state
else:
    if errors:
        if FORM_ERROR_MARKER in errors:
            message = errors.pop(FORM_ERROR_MARKER)
        else:
            message = _(u'Please correct the indicated errors.')
        addStatusMessage(request, message, type='error')
    return state.set(status='failure', errors=errors)
