from collective.megaphone.utils import MegaphoneMessageFactory as _
from collective.megaphone.config import ANNOTATION_KEY, DEFAULT_SIGNER_PORTLET_TEMPLATE, \
    DEFAULT_SIGNER_FULL_TEMPLATE
from collective.megaphone.browser.utils import GroupWizardStep, MegaphoneFormTemplateField
from persistent.dict import PersistentDict
from z3c.form import field, group
from zope import schema
from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from plone.app.portlets.utils import assignment_mapping_from_key

class ISignersStep(Interface):
    show_sig_portlet = schema.Bool(
        title = _(u'Display signatures'),
        description = _(u"If selected, signatures will be listed in a portlet in the right "
                        u"column, site-wide. (If you don't want it everywhere, you may instead "
                        u"manually add a Megaphone portlet to particular sections of the site."),
        default = True,
        )
    
    sig_portlet_title = schema.TextLine(
        title = _(u'Title of the portlet'),
        default = _(u'Sign our petition'),
        )
    
    sig_portlet_text = schema.Text(
        title = _(u'Portlet text'),
        description = _(u'A general description of the call to action. Keep it brief!'),
        default = _(u"Petition the bad guys to stop doing bad things!\n\nBy adding your name to our list, "
                    u"you'll be joining the growing chorus of good guys saying 'Enough's enough!'")
        )
    
    sig_portlet_link = schema.TextLine(
        title = _(u'Button text'),
        description = _(u'This will be displayed on the button that links to the Megaphone form.'),
        default = _(u'Let me sign!'),
        required = False,
        )
    
    sig_portlet_button = schema.TextLine(
        title = _(u'Button image'),
        description = _(u'Enter the URL of an image to be used for the button that links to the Megaphone form.'),
        required = False,
        )
    
    sig_portlet_min_count = schema.Int(
        title = _(u'Minimum number of signatures'),
        description = _(u'If fewer than this number of people have signed, no signatures or count will be shown. (Includes the goose factor.)'),
        default = 20,
        )
    
    goose_factor = schema.Int(
        title = _(u'Goose factor'),
        description = _(u'The signature count will be artificially boosted by this integer amount.'),
        required = True,
        default = 0,
        )
    
    sig_portlet_batch_size = schema.Choice(
        title = _(u'Number of signatures to display'),
        values = (1, 3, 5),
        default = 3,
        )
    
    sig_portlet_template = MegaphoneFormTemplateField(
        title = _(u'Template for Signatures in Portlet'),
        description = _(u'Enter the format for how you want signatures to appear when listed in '
                        u'the portlet.  You may use the variables shown at right.'),
        default = DEFAULT_SIGNER_PORTLET_TEMPLATE,
        )

class ISignersFullListing(Interface):
    
    show_full_listing = schema.Bool(
        title = _(u'Enable link to full listing of signatures'),
        default = True,
        )

    full_template = MegaphoneFormTemplateField(
        title = _(u'Template for Signatures in Full Listing'),
        description = _(u"Enter the format for how you want signatures to appear when listed in "
                        u"the full listing. You may use the variables shown at right. "
                        u"If you would like these rows in a table, you "
                        u"may separate cells with a pipe ('|')." ),
        default = DEFAULT_SIGNER_FULL_TEMPLATE,
        )

    batch_size = schema.Choice(
        title = _(u'Batch size'),
        description = _(u'Petition signers will be presented in batches. Choose the number '
                        u'per page you would like to see.'),
        values = (10, 20, 30, 50),
        default = 30
        )

class SignersFullListingGroup(group.Group):
    prefix = 'signers'
    label = _(u'Full signature listing')
    description = _(u'You may optionally create a link from the signatures portlet to a full listing '
                    u'of all signatures.')
    fields = field.Fields(ISignersFullListing)
    
    def getContent(self):
        return self.parentForm.getContent()
    
    def update(self):
        super(SignersFullListingGroup, self).update()
        self.widgets['full_template'].rows = 2
    
    @property
    def wizard(self):
        return self.parentForm.wizard

def assign_megaphone_portlet(megaphone, enabled=True):
    utool = getToolByName(megaphone, 'portal_url')
    site = utool.getPortalObject()
    mapping = assignment_mapping_from_key(site, 'plone.rightcolumn', 'context', '/', create=True)
    name = 'megaphone_%s' % megaphone.UID()
    assignment = mapping.get(name, None)
    if assignment is None and enabled:
        # assign portlet
        assignment = getUtility(IFactory, name=u'collective.megaphone.portlets.calltoaction')()
        assignment.megaphone_path = '/'.join(utool.getRelativeContentPath(megaphone))
        mapping[name] = assignment
    elif assignment and not enabled:
        # remove assignment
        del mapping[name]
    

class SignersStep(GroupWizardStep):
    template = ViewPageTemplateFile('template_step.pt')
    
    prefix = 'signers'
    label = _(u'List of Signatures')
    description = _(u"This step allows you to configure how to present a list of the people "
                    u"who have signed your petition, to demonstrate the power your petition "
                    u"is generating, and/or to encourage more people to join the cause.")
    fields = field.Fields(ISignersStep)
    groups = (SignersFullListingGroup,)

    def update(self):
        super(SignersStep, self).update()
        self.widgets['sig_portlet_text'].rows = 3
        self.widgets['sig_portlet_template'].rows = 2

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = ('sincerely', )
        vars = [('sender_%s' % f_id, _(u"Sender's $varname", mapping={'varname': f['title']}))
            for f_id, f in sorted(fields.items(), key=lambda x:x[1]['order'])
            if f_id not in ignored_fields]
        vars.append(('sender_public_name', _(u"Sender's first name and last initial")))
        return [dict(title=title, id=id) for id, title in vars]
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['signers'] = data
        
        assign_megaphone_portlet(pfg, data['show_sig_portlet'])

    def load(self, pfg):
        data = self.getContent()
        data.update(IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('signers', {}))
