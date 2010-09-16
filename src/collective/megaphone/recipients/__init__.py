from collective.megaphone.config import ANNOTATION_KEY
from zope.annotation.interfaces import IAnnotations

def get_recipient_settings(megaphone, recipient_type):
    data = IAnnotations(megaphone).get(ANNOTATION_KEY, {}).get('recipients', {})
    return [(id, settings) for (id, settings) in data.items()
                           if settings.get('recipient_type', 'standard') == recipient_type]
