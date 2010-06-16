import cgi
from zope.annotation.interfaces import IAnnotations
from Products.Five import BrowserView
from Products.CMFPlone.PloneBatch import Batch
from Products.Archetypes.interfaces.field import IField
from Products.PloneFormGen import dollarReplace
from collective.megaphone.config import ANNOTATION_KEY, SAVEDATA_ID
from collective.megaphone import implementedOrProvidedBy
from plone.memoize import instance

class SignersView(BrowserView):
    
    def __init__(self, *args):
        super(SignersView, self).__init__(*args)
        self.settings = IAnnotations(self.context).get(ANNOTATION_KEY, {}).get('signers', {})
        self.sda = getattr(self.context, SAVEDATA_ID, None)
    
    @property
    def count(self):
        if self.sda is not None:
            return self.sda.itemsSaved()
        return 0
    
    @property
    def enabled(self):
        if not self.count:
            return False
        
        return self.settings.get('show_signers', False)

    @property
    def as_table(self):
        return '|' in self.settings.get('template', u'')

    @property
    def rendered_signers(self):
        column_names = self.column_names
        column_count = len(column_names)
        template = self.settings.get('template', u'')
        if self.as_table:
            cells = ['<td>%s</td>' % cgi.escape(c.strip()) for c in template.split('|')]
            template = ''.join(cells)
        for row in self.signers:
            if len(row) != column_count:
                continue
            vars = dict([('sender_%s' % k,v) for k,v in zip(column_names, row)])
            yield dollarReplace.DollarVarReplacer(vars).sub(template)
    
    @instance.memoize
    def batch(self):
        b_size = self.settings.get('batch_size', 30)
        b_start = self.request.get('b_start', 0)
        storage = self.storage
        keys = storage and storage.keys() or []
        return Batch(keys, b_size, b_start, orphan=1)
    
    @property
    def signers(self):
        # We batch using the keys in forward order for efficiency,
        # but want to actually display the most recent items first.
        # (cf. Matt. 20:16)
        batch = self.batch()
        first = batch.sequence_length - batch.end
        last = batch.sequence_length - batch.start
        
        storage = self.storage
        if storage is not None:
            for row in reversed(self.storage.values()[first:last+1]):
                yield row
    
    @property
    def storage(self):
        if self.sda is not None:
            return self.sda._inputStorage

    @property
    def column_names(self):
        return [fo.__name__ for fo in self.context._getFieldObjects()
                if not implementedOrProvidedBy(IField, fo) and not fo.isLabel()]
