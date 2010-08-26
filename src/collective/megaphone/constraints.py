import re
from zope import schema
from collective.megaphone import MegaphoneMessageFactory as _

class InvalidEmailAddress(schema.ValidationError):
    __doc__ = _(u"Invalid e-mail address")

check_email = re.compile(r"[a-zA-Z0-9._%-]+@([a-zA-Z0-9-]+\.)*[a-zA-Z]{2,4}").match
def is_email(value):
    if not check_email(value):
        raise InvalidEmailAddress(value)
    return True
